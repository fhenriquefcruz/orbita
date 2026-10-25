"""Aurora 3.25 user-initiated HTTP Auth logins: no network in CI."""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"quality"))
from auth_dual_login_runner import (
    GateError, LOGIN_ACK, main, password_login
)
from auth_http_rls_probe import PROJECT_REF, HttpReader

KEY="sb_publishable_mock_only"
JWT="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.mock_signature"


class FakeResponse:
    status=200
    def __init__(self, obj=None): self.obj = obj or {"access_token":JWT}
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self, n):return json.dumps(self.obj).encode()


class FakeOpener:
    def __init__(self):self.requests=[]
    def open(self,req,timeout=12):
        self.requests.append(req)
        return FakeResponse()


class DualLoginTests(unittest.TestCase):
    def test_password_login_uses_only_project_auth_endpoint(self):
        opener=FakeOpener()
        token=password_login(HttpReader(KEY,opener), "test@example.com", "test-secret")
        self.assertEqual(token,JWT)
        self.assertEqual(len(opener.requests),1)
        req=opener.requests[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(req.full_url,
                         f"https://{PROJECT_REF}.supabase.co/auth/v1/token?grant_type=password")
        self.assertEqual(req.headers["Apikey"],KEY)
        self.assertEqual(json.loads(req.data),{
            "email":"test@example.com","password":"test-secret"
        })
        self.assertNotIn("test-secret",str(req.headers))

    def test_missing_password_never_calls_network(self):
        op=FakeOpener()
        with self.assertRaises(GateError):
            password_login(HttpReader(KEY,op),"test@example.com","")
        self.assertEqual(op.requests,[])

    def test_invalid_email_never_calls_network(self):
        op=FakeOpener()
        for email in ("","not-an-email","s p@example.com"):
            with self.subTest(email=email):
                with self.assertRaises(GateError):
                    password_login(HttpReader(KEY,op),email,"test")
        self.assertEqual(op.requests,[])

    def test_bad_server_response_fails_without_token_leak(self):
        class BrokenOpener:
            def open(self,req,timeout=12):
                return FakeResponse({"refresh_token":"private_not_a_jwt"})
        with self.assertRaises(GateError):
            password_login(HttpReader(KEY,BrokenOpener()),"test@example.com","secret")

    def test_auth_error_body_is_never_returned(self):
        from urllib.error import HTTPError
        class BrokenOpener:
            def open(self,req,timeout=12):
                raise HTTPError(req.full_url,400,"sensitive_server_secret",{},None)
        with self.assertRaisesRegex(GateError,"Credenciais não autenticadas"):
            password_login(HttpReader(KEY,BrokenOpener()),"test@example.com","secret")

    def test_without_optin_main_never_prompts(self):
        with patch("builtins.input") as ask,patch("getpass.getpass") as secret:
            self.assertEqual(main({}),2)
            ask.assert_not_called()
            secret.assert_not_called()

    def test_wrong_project_never_prompts(self):
        env={"ORBITA_E2E_LOGIN_ACK":LOGIN_ACK,
             "ORBITA_E2E_EXPECT_PROJECT":"other",
             "ORBITA_E2E_PUBLISHABLE_KEY":KEY}
        with patch("builtins.input") as ask:
            self.assertEqual(main(env),2)
            ask.assert_not_called()

    def test_two_accounts_verify_and_no_secrets_printed(self):
        env={"ORBITA_E2E_LOGIN_ACK":LOGIN_ACK,
             "ORBITA_E2E_EXPECT_PROJECT":PROJECT_REF,
             "ORBITA_E2E_PUBLISHABLE_KEY":KEY}
        output=io.StringIO()
        with patch("builtins.input",side_effect=["owner@example.com","second@example.com"]),\
             patch("getpass.getpass",side_effect=["private1","private2"]),\
             patch("auth_dual_login_runner.password_login",side_effect=["owner.jwt.signature","other.jwt.signature"]) as login,\
             patch("auth_dual_login_runner.evaluate_http",return_value={
                "ready_for_next_gate":True}),\
             contextlib.redirect_stdout(output):
            self.assertEqual(main(env),0)
        self.assertEqual(login.call_count,2)
        self.assertNotIn("private1",output.getvalue())
        self.assertNotIn("owner.jwt.signature",output.getvalue())
        self.assertIn("PASSOU",output.getvalue())

    def test_empty_chat_fixture_keeps_release_gate_blocked(self):
        env={"ORBITA_E2E_LOGIN_ACK":LOGIN_ACK,
             "ORBITA_E2E_EXPECT_PROJECT":PROJECT_REF,
             "ORBITA_E2E_PUBLISHABLE_KEY":KEY}
        with patch("builtins.input",side_effect=["owner@example.com","second@example.com"]),\
             patch("getpass.getpass",side_effect=["private1","private2"]),\
             patch("auth_dual_login_runner.password_login",side_effect=["owner.jwt.signature","other.jwt.signature"]),\
             patch("auth_dual_login_runner.evaluate_http",return_value={
                "ready_for_next_gate":False}):
            self.assertEqual(main(env),1)


if __name__=="__main__":
    unittest.main()
