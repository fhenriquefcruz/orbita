import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot import Memory, interpret_task, reply_text, render_records


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mem = Memory(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.mem.close()
        self.tmp.cleanup()

    def test_task_priority(self):
        self.assertEqual(interpret_task("P1 | Enviar documento"), ("Enviar documento", "P1"))
        self.assertEqual(interpret_task("Ler livro"), ("Ler livro", "P2"))

    def test_owner_isolation(self):
        self.mem.add(10, "tarefa", "Tarefa A")
        self.assertEqual(len(self.mem.list(10)), 1)
        self.assertEqual(len(self.mem.list(11)), 0)

    def test_complete_only_own_task(self):
        rid = self.mem.add(10, "tarefa", "Fazer algo")
        self.assertFalse(self.mem.complete(11, rid))
        self.assertTrue(self.mem.complete(10, rid))
        self.assertFalse(self.mem.complete(10, rid))

    def test_feito_only_reports_success_for_committed_change(self):
        rid = self.mem.add(10, "tarefa", "Validar status")
        self.assertIn("Tarefa concluída.", reply_text("/feito " + str(rid), 10, self.mem, "", ""))
        failure = reply_text("/feito " + str(rid), 10, self.mem, "", "")
        self.assertIn("Não foi possível concluir", failure)
        self.assertIn("/tarefas", failure)

    def test_commands_without_api(self):
        answer = reply_text("/tarefa P1 | Revisar orçamento", 10, self.mem, "", "")
        self.assertIn("P1", answer)
        self.assertIn("Revisar orçamento", reply_text("/tarefas", 10, self.mem, "", ""))
        self.assertIn("prévia", reply_text("/resumo", 10, self.mem, "", ""))

    def test_idea_and_history(self):
        reply_text("/ideia Criar uma biblioteca", 10, self.mem, "", "")
        self.assertIn("biblioteca", reply_text("/ideias", 10, self.mem, "", ""))
        self.mem.save_message(10, "user", "Olá")
        self.assertEqual(len(self.mem.history(10)), 1)
        self.mem.clear_history(10)
        self.assertEqual(len(self.mem.history(10)), 0)
        self.assertEqual(len(self.mem.list(10, "ideia")), 1)

    def test_finished_hidden(self):
        rid = self.mem.add(10, "tarefa", "Revisão")
        self.mem.complete(10, rid)
        self.assertIn("concluídas", render_records(self.mem.list(10, "tarefa"), "tarefa"))

    def test_unknown_command(self):
        self.assertIn("não reconhecido", reply_text("/desconhecido", 10, self.mem, "", ""))


if __name__ == "__main__":
    unittest.main()

class TestPrompts(unittest.TestCase):
    def test_prompt_builds_without_secrets(self):
        from bot import assistant_instructions
        with tempfile.TemporaryDirectory() as tmp:
            mem = Memory(Path(tmp) / "test.db")
            mem.add(10, 'tarefa', 'Acompanhar fornecedor')
            prompt = assistant_instructions(mem, 10)
            self.assertIn('Vânia', prompt)
            self.assertIn('Acompanhar fornecedor', prompt)
            self.assertIn('/tarefa', prompt)
            mem.close()