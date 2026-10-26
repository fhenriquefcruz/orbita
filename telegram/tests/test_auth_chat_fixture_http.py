"""Aurora 3.27: synthetic dual-user HTTP fixture; NO actual HTTP or DB in CI."""
import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"quality"))

from auth_http_rls_probe import GateError, Response, PROJECT_REF
from auth_chat_fixture_http import ACK, FIXTURE_PREFIX, evaluate_fixture, cleanup, main, mutate

OWNER="11111111-1111-4111-8111-111111111111"
OTHER="22222222-2222-4222-8222-222222222222"
A="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJvd25lciJ9.sig"
B="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJvdGhlciJ9.sig"
MARK=FIXTURE_PREFIX + "a"*32


class FakeReader:
    def __init__(self,leak=False,deny_delete=False,cleanup_fails=False):
        self.marker=MARK
        self.row=None
        self.leak=leak
        self.deny_delete=deny_delete
        self.cleanup_fails=cleanup_fails
        self.actions=[]

    def get(self,path,jwt=None):
        if "orbita_chat_messages" not in path:
            raise AssertionError("Only fixture scoped GET supported")
        if jwt==B and not self.leak:
            return Response(200,[])
        return Response(200,[self.row] if self.row is not None else [])

    def mutation(self,reader,method,token,*,owner_id,marker):
        self.actions.append((method,token))
        if method=="POST":
            self.row={"id":414,"user_id":owner_id,"content":marker}
            return Response(201,[self.row])
        if method=="DELETE":
            if token==B:
                if self.deny_delete:
                    self.row=None
                    return Response(200,[{"id":414}])
                return Response(200,[])
            if self.cleanup_fails:
                return Response(500,None)
            result=[self.row] if self.row is not None else []
            self.row=None
            return Response(200,result)
        raise AssertionError("unexpected mutation")


class ChatFixtureTests(unittest.TestCase):
    def mock_run(self,reader,preflight=None):
        if preflight is None:
            preflight=[{"ready_for_next_gate":False},
                       {"ready_for_next_gate":True}]
        with patch("auth_chat_fixture_http.evaluate_http",side_effect=preflight) as auth,\
             patch("auth_chat_fixture_http._user_id",side_effect=[OWNER,OTHER]),\
             patch("auth_chat_fixture_http.mutate",side_effect=reader.mutation):
            result=evaluate_fixture(reader,A,B,marker=MARK)
        return result,auth.call_count

    def test_one_fixture_then_crosscheck_then_owner_delete(self):
        reader=FakeReader()
        report,count=self.mock_run(reader)
        self.assertTrue(report["chat_isolated"])
        self.assertTrue(report["cleanup_verified"])
        self.assertTrue(report["fixture_created"])
        self.assertEqual(count,2)
        self.assertIsNone(reader.row)
        self.assertEqual(reader.actions,[("POST",A),("DELETE",B),("DELETE",A)])

    def test_existing_chat_never_performs_a_mutation(self):
        reader=FakeReader()
        with patch("auth_chat_fixture_http.evaluate_http",return_value={
                "ready_for_next_gate":True}),\
             patch("auth_chat_fixture_http.mutate") as change:
            result=evaluate_fixture(reader,A,B)
        self.assertFalse(result["fixture_created"])
        self.assertTrue(result["cleanup_verified"])
        change.assert_not_called()

    def test_cross_account_read_leak_blocks_and_cleans(self):
        reader=FakeReader(leak=True)
        with self.assertRaisesRegex(GateError,"VAZAMENTO"):
            self.mock_run(reader)
        self.assertIsNone(reader.row)
        self.assertEqual(reader.actions,[("POST",A),("DELETE",A)])

    def test_foreign_delete_leak_blocks_and_cleans(self):
        reader=FakeReader(deny_delete=True)
        with self.assertRaisesRegex(GateError,"VAZAMENTO"):
            self.mock_run(reader)
        self.assertIsNone(reader.row)

    def test_cleanup_failure_never_returns_success(self):
        reader=FakeReader(cleanup_fails=True)
        with self.assertRaisesRegex(GateError,"LIMPEZA NÃO CONFIRMADA"):
            self.mock_run(reader)
        self.assertIsNotNone(reader.row)

    def test_second_http_probe_false_blocks_and_still_cleans(self):
        reader=FakeReader()
        with self.assertRaisesRegex(GateError,"Leitura cruzada HTTP não passou"):
            self.mock_run(reader,[{"ready_for_next_gate":False},
                                  {"ready_for_next_gate":False}])
        self.assertIsNone(reader.row)

    def test_creation_error_still_probes_cleanup(self):
        reader=FakeReader()
        def bad_post(reader_arg,method,token,*,owner_id,marker):
            if method=="POST":
                reader.row={"id":414,"user_id":owner_id,"content":marker}
                return Response(500,None)
            return reader.mutation(reader_arg,method,token,owner_id=owner_id,marker=marker)
        with patch("auth_chat_fixture_http.evaluate_http",return_value={
                "ready_for_next_gate":False}),\
             patch("auth_chat_fixture_http._user_id",side_effect=[OWNER,OTHER]),\
             patch("auth_chat_fixture_http.mutate",side_effect=bad_post):
            with self.assertRaises(GateError):
                evaluate_fixture(reader,A,B,marker=MARK)
        self.assertIsNone(reader.row)

    def test_clean_no_row_needs_no_delete(self):
        reader=FakeReader()
        with patch("auth_chat_fixture_http.mutate") as change:
            self.assertTrue(cleanup(reader,A,OWNER,MARK))
        change.assert_not_called()

    def test_invalid_method_and_marker_never_connect(self):
        reader=FakeReader()
        for method,mark in (("PATCH",MARK),("POST","bad"),("DELETE","")):
            with self.subTest(method=method,mark=mark):
                with self.assertRaises(GateError):
                    mutate(reader,method,A,owner_id=OWNER,marker=mark)

    def test_invalid_identity_rejected_before_http(self):
        with self.assertRaises(GateError):
            mutate(FakeReader(),"POST",A,owner_id="not-uuid",marker=MARK)

    def test_missing_optin_does_not_prompt_or_call_api(self):
        with patch("builtins.input") as ask,\
             patch("auth_chat_fixture_http.password_login") as login,\
             patch("auth_chat_fixture_http.mutate") as write:
            out=io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main({}),2)
            ask.assert_not_called()
            login.assert_not_called()
            write.assert_not_called()

    def test_wrong_project_does_not_prompt(self):
        with patch("builtins.input") as ask:
            out=io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main({
                    "ORBITA_CHAT_FIXTURE_ACK":ACK,
                    "ORBITA_E2E_EXPECT_PROJECT":"different",
                }),2)
            ask.assert_not_called()

    def test_success_report_contains_no_secrets(self):
        env={
            "ORBITA_CHAT_FIXTURE_ACK":ACK,
            "ORBITA_E2E_EXPECT_PROJECT":PROJECT_REF,
            "ORBITA_E2E_PUBLISHABLE_KEY":"sb_publishable_fake",
        }
        out=io.StringIO()
        with patch("builtins.input",side_effect=["principal@example.com","other@example.com"]),\
             patch("getpass.getpass",side_effect=["password1","password2"]),\
             patch("auth_chat_fixture_http.password_login",side_effect=[A,B]),\
             patch("auth_chat_fixture_http.evaluate_fixture",return_value={
                "chat_isolated":True,"cleanup_verified":True,"fixture_created":True}),\
             contextlib.redirect_stdout(out):
            self.assertEqual(main(env),0)
        printed=out.getvalue()
        for secret in (A,B,"password1","password2",OWNER,OTHER,MARK):
            self.assertNotIn(secret,printed)
        self.assertIn("PASSOU",printed)

    def test_failure_report_redacts_tokens(self):
        env={
            "ORBITA_CHAT_FIXTURE_ACK":ACK,
            "ORBITA_E2E_EXPECT_PROJECT":PROJECT_REF,
            "ORBITA_E2E_PUBLISHABLE_KEY":"sb_publishable_fake",
        }
        out=io.StringIO()
        with patch("builtins.input",side_effect=["principal@example.com","other@example.com"]),\
             patch("getpass.getpass",side_effect=["secret1","secret2"]),\
             patch("auth_chat_fixture_http.password_login",side_effect=[A,B]),\
             patch("auth_chat_fixture_http.evaluate_fixture",side_effect=GateError(A)),\
             contextlib.redirect_stdout(out):
            self.assertEqual(main(env),1)
        self.assertNotIn(A,out.getvalue())
        self.assertNotIn(B,out.getvalue())
        self.assertNotIn("secret1",out.getvalue())
        self.assertIn("BLOQUEADO",out.getvalue())


if __name__=="__main__":
    unittest.main()
