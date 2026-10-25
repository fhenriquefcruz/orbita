import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proposal_transport import inline_keyboard, callback_as_confirmation

CODE="ABCDEF123456"


class ProposalTransportTest(unittest.TestCase):
    def test_preview_produces_two_bounded_buttons(self):
        text=("📝 Preparei uma proposta de tarefa, mas ainda NÃO registrei nada.\n\n"
              "Título: Enviar documento\nPrioridade: P2\n"
              "Para salvar, responda: confirmar "+CODE+"\n"
              "Para descartar: cancelar "+CODE)
        keyboard=inline_keyboard(text)
        self.assertEqual(len(keyboard["inline_keyboard"][0]),2)
        confirm,cancel=keyboard["inline_keyboard"][0]
        self.assertEqual(confirm["callback_data"],"orbita:confirm:"+CODE)
        self.assertEqual(cancel["callback_data"],"orbita:cancel:"+CODE)
        self.assertLessEqual(len(confirm["callback_data"].encode()),64)

    def test_callback_only_understands_approved_payloads(self):
        self.assertEqual(callback_as_confirmation("orbita:confirm:"+CODE),"confirmar "+CODE)
        self.assertEqual(callback_as_confirmation("orbita:cancel:"+CODE),"cancelar "+CODE)
        for invalid in ("orbita:delete:"+CODE, "orbita:confirm:"+CODE+";drop",
                        "orbita:confirm:BAD","orbita:confirm:"+CODE.lower(),
                        "confirmar "+CODE, None, "x"*100):
            with self.subTest(invalid=invalid):
                self.assertIsNone(callback_as_confirmation(invalid))

    def test_free_dialogue_does_not_receive_buttons(self):
        self.assertIsNone(inline_keyboard("Posso ajudar a organizar suas tarefas."))
        self.assertIsNone(inline_keyboard("Para salvar, responda: confirmar "+CODE))
        self.assertIsNone(inline_keyboard("📝 Preparei uma proposta de tarefa, mas ainda NÃO registrei nada."))

    def test_no_unvalidated_code_leaks_into_markup(self):
        forged=("📝 Preparei uma proposta de tarefa, mas ainda NÃO registrei nada.\n"
                "Para salvar, responda: confirmar "+CODE+";injetado")
        self.assertIsNone(inline_keyboard(forged))


if __name__ == "__main__":
    unittest.main()
