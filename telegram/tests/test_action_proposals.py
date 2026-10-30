import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from action_proposals import classify_action, parse_confirmation, preview, check_proposal
from bot import Memory, reply_text

CODE = "ABCDEF123456"


class NaturalActionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "memory.db"
        self.mem = Memory(self.path)

    def tearDown(self):
        self.mem.close()
        self.tmp.cleanup()

    def test_task_in_natural_language_returns_preview_only(self):
        with patch("bot.new_code", return_value=CODE):
            response = reply_text("Vânia, anote que preciso enviar o relatório amanhã",
                                  42, self.mem, "", "")
        self.assertIn("enviar o relatório amanhã", response)
        self.assertIn("confirmar " + CODE, response)
        self.assertIn("NÃO registrei nada", response)
        self.assertEqual(self.mem.list(42), [])

    def test_confirm_is_atomic_and_idempotent(self):
        with patch("bot.new_code", return_value=CODE):
            reply_text("Anote que preciso revisar o relatório", 42, self.mem, "", "")
        answer = reply_text("confirmar " + CODE, 42, self.mem, "", "")
        self.assertIn("salvo", answer)
        other = reply_text("CONFIRMAR " + CODE.lower(), 42, self.mem, "", "")
        self.assertIn("Não criei uma duplicata", other)
        self.assertEqual(len(self.mem.list(42)), 1)

    def test_cancelled_proposal_cannot_be_saved(self):
        with patch("bot.new_code", return_value=CODE):
            reply_text("Registre uma ideia: melhorar a busca do ORBITA", 42, self.mem, "", "")
        self.assertIn("cancelada", reply_text("cancelar " + CODE, 42, self.mem, "", ""))
        reply_text("confirmar " + CODE, 42, self.mem, "", "")
        self.assertEqual(self.mem.list(42), [])

    def test_expired_proposal_cannot_write(self):
        self.mem.create_proposal(42, "tarefa", "Revisar documento", "P2", CODE)
        self.mem.db.execute(
            "UPDATE action_proposals SET expires_at=? WHERE code=?",
            ((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),CODE))
        self.mem.db.commit()
        self.assertEqual(self.mem.confirm_proposal(42, CODE)[0], "expired")
        self.assertEqual(self.mem.list(42), [])

    def test_proposal_belongs_to_same_user(self):
        self.mem.create_proposal(42, "tarefa", "Apenas do titular", "P2", CODE)
        self.assertEqual(self.mem.confirm_proposal(13, CODE), ("missing", None))
        self.assertFalse(self.mem.cancel_proposal(13, CODE))
        self.assertEqual(len(self.mem.list(13)), 0)
        self.assertEqual(self.mem.confirm_proposal(42, CODE)[0], "saved")

    def test_proposals_survive_process_restart(self):
        self.mem.create_proposal(42, "ideia", "Nova interface", "P3", CODE)
        self.mem.close()
        self.mem = Memory(self.path)
        status, rid = self.mem.confirm_proposal(42, CODE)
        self.assertEqual(status, "saved")
        self.assertIsInstance(rid, int)
        self.assertEqual(self.mem.list(42)[0]["title"], "Nova interface")

    def test_multiple_proposals_need_the_specific_code(self):
        self.mem.create_proposal(42, "tarefa", "Primeira", "P2", CODE)
        self.mem.create_proposal(42, "tarefa", "Segunda", "P1", "ABCDEF123457")
        self.assertEqual(self.mem.confirm_proposal(42, "ABCDEF123457")[0], "saved")
        self.assertEqual([x["title"] for x in self.mem.list(42)], ["Segunda"])
        self.assertEqual(self.mem.confirm_proposal(42, CODE)[0], "saved")
        self.assertEqual(len(self.mem.list(42)), 2)

    def test_idea_priority_and_task_urgency(self):
        idea = classify_action("Vânia, registre uma ideia: acompanhar entregas")
        task = classify_action("Crie uma tarefa para enviar documento urgente")
        self.assertEqual((idea.kind, idea.priority), ("ideia", "P3"))
        self.assertEqual((task.kind, task.priority), ("tarefa", "P1"))

    def test_does_not_intercept_regular_conversation_or_command(self):
        for text in ("Vânia, como posso organizar minha semana?",
                     "Crie uma estratégia de comunicação",
                     "/tarefa Comprar café",
                     "Tenho uma ideia",
                     "Você pode me ajudar a decidir?",
                     "Continue o que estávamos discutindo"):
            with self.subTest(text=text):
                self.assertIsNone(classify_action(text))

    def test_confirmation_requires_full_exact_code(self):
        self.assertIsNone(parse_confirmation("sim"))
        self.assertIsNone(parse_confirmation("confirmar"))
        self.assertIsNone(parse_confirmation("confirmar ABCDE"))
        self.assertIsNone(parse_confirmation("confirmar " + CODE + " apagar tudo"))
        self.assertEqual(parse_confirmation("/confirmar " + CODE.lower()), ("confirm", CODE))
        self.assertEqual(parse_confirmation("cancelar " + CODE), ("cancel", CODE))

    def test_invalid_proposals_are_rejected(self):
        for title in ("", " "):
            with self.assertRaises(ValueError):
                check_proposal("tarefa", title, "P2", CODE)
        with self.assertRaises(ValueError):
            check_proposal("apagar", "alguma coisa", "P2", CODE)
        with self.assertRaises(ValueError):
            check_proposal("tarefa", "a" * 1001, "P2", CODE)
        with self.assertRaises(ValueError):
            check_proposal("tarefa", "texto", "P5", CODE)

    def test_no_false_success_on_database_insert_error(self):
        self.mem.create_proposal(42, "tarefa", "Documento", "P2", CODE)
        self.mem.db.execute("""CREATE TRIGGER reject_action_record BEFORE INSERT
            ON records BEGIN SELECT RAISE(FAIL,'simulated'); END;""")
        self.mem.db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.mem.confirm_proposal(42, CODE)
        self.assertEqual(self.mem.db.execute(
            "SELECT status FROM action_proposals WHERE code=?", (CODE,)).fetchone()[0], "pending")
        self.assertEqual(self.mem.list(42), [])

    def test_explicit_task_command_still_commits_without_proposal(self):
        result = reply_text("/tarefa P1 | Visitar fornecedor", 42, self.mem, "", "")
        self.assertIn("registrou", result)
        self.assertEqual(len(self.mem.list(42)), 1)
        self.assertEqual(self.mem.db.execute("SELECT COUNT(*) FROM action_proposals").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
