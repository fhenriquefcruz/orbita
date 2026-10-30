import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloud_memory import CloudMemory
from bot import reply_text

USER = "11111111-1111-4111-8111-111111111111"
CODE = "ABCDEF123456"


class CloudProposalTest(unittest.TestCase):
    def setUp(self):
        self.mem = CloudMemory("https://orbita-test.supabase.co",
                               "sb_secret_testing_only", USER)

    def test_proposal_insert_contains_owner_and_not_record_insert(self):
        with patch.object(self.mem, "_call", return_value=[{"code": CODE}]) as caller:
            self.mem.create_proposal(123, "tarefa", "Enviar documento", "P1", CODE)
        args = caller.call_args
        self.assertEqual(args.args[:2], ("orbita_action_proposals", "POST"))
        body = args.kwargs["value"]
        self.assertEqual(body["user_id"], USER)
        self.assertEqual(body["telegram_id"], 123)
        self.assertEqual(body["priority"], "P1")
        self.assertEqual(body["code"], CODE)
        self.assertNotIn("status", body)

    def test_confirmation_calls_atomic_rpc_once_and_checks_seq(self):
        with patch.object(self.mem, "_call", return_value=[
            {"outcome":"saved","record_number":42}]) as caller:
            self.assertEqual(self.mem.confirm_proposal(123,CODE),("saved",42))
        self.assertEqual(caller.call_count,1)
        self.assertEqual(caller.call_args.args[:2],
                         ("rpc/orbita_confirm_action_proposal","POST"))
        self.assertEqual(caller.call_args.kwargs["value"], {
            "p_code":CODE,"p_user_id":USER,"p_telegram_id":123})

    def test_repeat_is_not_a_new_insert(self):
        with patch.object(self.mem, "_call", return_value=[
            {"outcome":"already","record_number":42}]):
            self.assertEqual(self.mem.confirm_proposal(123,CODE),("already",42))

    def test_zero_or_malformed_result_never_claims_success(self):
        for response in ([], [{"outcome":"saved","record_number":None}],
                         [{"outcome":"saved","record_number":0}],
                         [{"outcome":"unknown","record_number":5}]):
            with self.subTest(response=response):
                with patch.object(self.mem, "_call", return_value=response):
                    with self.assertRaises(RuntimeError):
                        self.mem.confirm_proposal(123,CODE)

    def test_wrong_identity_filtered_at_cancel(self):
        with patch.object(self.mem, "_call", return_value=[]) as caller:
            self.assertFalse(self.mem.cancel_proposal(321,CODE))
        self.assertEqual(caller.call_args.kwargs["query"]["telegram_id"], "eq.321")
        self.assertEqual(caller.call_args.kwargs["query"]["user_id"], "eq."+USER)
        self.assertEqual(caller.call_args.kwargs["query"]["status"], "eq.pending")

    def test_missing_schema_flag_blocks_cloud_natural_proposals(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(self.mem, "_call") as caller:
                response = reply_text("Vânia, anote que preciso revisar documento",
                                      123,self.mem,"","")
        self.assertIn("ainda não está ativado",response)
        caller.assert_not_called()

    def test_enabled_flag_uses_cloud_proposal_only_no_tasks(self):
        with patch.dict("os.environ",{"ORBITA_NATURAL_ACTIONS_ENABLED":"1"}):
            with patch("bot.new_code", return_value=CODE), patch.object(
                    self.mem,"_call",return_value=[{"code":CODE}]) as caller:
                response = reply_text("Vânia, anote que preciso enviar material",
                                      123,self.mem,"","")
        self.assertIn("confirmar "+CODE,response)
        self.assertEqual(caller.call_count,1)
        self.assertEqual(caller.call_args.args[0],"orbita_action_proposals")


if __name__ == "__main__":
    unittest.main()
