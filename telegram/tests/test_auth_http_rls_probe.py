"""No real credentials or network. Covers Aurora 3.24's HTTP-RLS release gate."""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "quality"))
from auth_http_rls_probe import (
    GateError, HttpReader, NoRedirects, PROJECT_REF, PROJECT_URL,
    Response, RUN_CONFIRMATION, evaluate_http, main,
)

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
OWNER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJvd25lciJ9.owner_signature"
OTHER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJvdGhlciJ9.other_signature"
KEY = "sb_publishable_mock_public_only"


class MockTransport:
    def __init__(self, *, owner_rows=None, owner_chats=None):
        self.owner_rows = [{"id": "record-1", "user_id": OWNER}] if owner_rows is None else owner_rows
        self.owner_chats = [{"user_id": OWNER}] if owner_chats is None else owner_chats
        self.other_id = OTHER
        self.other_records = []
        self.other_chats = []
        self.anon_records_status = 401
        self.queue_status = 403
        self.invalid_status = 401
        self.calls = []

    def get(self, path, jwt=None):
        self.calls.append((path, jwt))
        if path == "/auth/v1/user":
            if jwt == OWNER_TOKEN:
                return Response(200, {"id": OWNER})
            if jwt == OTHER_TOKEN:
                return Response(200, {"id": self.other_id})
            return Response(self.invalid_status, None)
        if path.startswith("/rest/v1/orbita_records?"):
            if jwt is None:
                return Response(self.anon_records_status, None)
            return Response(200, self.owner_rows if jwt == OWNER_TOKEN else self.other_records)
        if path.startswith("/rest/v1/orbita_chat_messages?"):
            return Response(200, self.owner_chats if jwt == OWNER_TOKEN else self.other_chats)
        if path.startswith("/rest/v1/orbita_telegram_updates?"):
            return Response(self.queue_status, None)
        raise AssertionError("Unexpected request: " + path)


class HttpRLSProbeTests(unittest.TestCase):
    def test_full_two_jwt_readonly_probe_passes_with_chat_fixture(self):
        transport = MockTransport()
        summary = evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)
        self.assertTrue(summary["ready_for_next_gate"])
        self.assertTrue(summary["cross_account_records_hidden"])
        self.assertTrue(summary["cross_account_chat_hidden"])
        self.assertTrue(summary["private_telegram_denied"])
        self.assertTrue(summary["invalid_jwt_denied"])
        self.assertEqual(len(transport.calls), 11)
        self.assertTrue(all(path.startswith("/") for path, _ in transport.calls))

    def test_chat_without_fixture_is_pending_not_false_success(self):
        result = evaluate_http(MockTransport(owner_chats=[]), OWNER_TOKEN, OTHER_TOKEN)
        self.assertFalse(result["chat_fixture_exists"])
        self.assertFalse(result["ready_for_next_gate"])

    def test_same_jwt_fails_before_any_http(self):
        transport = MockTransport()
        with self.assertRaisesRegex(GateError, "mesmo JWT"):
            evaluate_http(transport, OWNER_TOKEN, OWNER_TOKEN)
        self.assertEqual(transport.calls, [])

    def test_two_valid_sessions_must_belong_to_different_accounts(self):
        transport = MockTransport()
        transport.other_id = OWNER
        with self.assertRaisesRegex(GateError, "mesma conta"):
            evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)

    def test_cross_account_record_leak_fails(self):
        transport = MockTransport()
        transport.other_records = [{"id": "record-1", "user_id": OWNER}]
        with self.assertRaisesRegex(GateError, "Isolamento RLS FALHOU"):
            evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)

    def test_cross_account_chat_leak_fails(self):
        transport = MockTransport()
        transport.other_chats = [{"user_id": OWNER}]
        with self.assertRaisesRegex(GateError, "chat do titular"):
            evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)

    def test_owner_chat_cannot_silently_include_foreign_account(self):
        transport = MockTransport(owner_chats=[{"user_id": OTHER}])
        with self.assertRaisesRegex(GateError, "outro titular"):
            evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)

    def test_owner_without_record_does_not_fake_proof(self):
        with self.assertRaisesRegex(GateError, "não possui registro"):
            evaluate_http(MockTransport(owner_rows=[]), OWNER_TOKEN, OTHER_TOKEN)

    def test_owner_cannot_read_other_owner_data(self):
        with self.assertRaisesRegex(GateError, "não possui registro"):
            evaluate_http(MockTransport(owner_rows=[{"id": "other-record", "user_id": OTHER}]),
                          OWNER_TOKEN, OTHER_TOKEN)

    def test_private_telegram_must_be_forbidden_for_users(self):
        transport = MockTransport()
        transport.queue_status = 200
        with self.assertRaisesRegex(GateError, "Tabela privada"):
            evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)

    def test_anon_must_be_forbidden_to_read_records(self):
        transport = MockTransport()
        transport.anon_records_status = 200
        with self.assertRaisesRegex(GateError, "Tabela privada"):
            evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)

    def test_invalid_jwt_must_be_rejected(self):
        transport = MockTransport()
        transport.invalid_status = 200
        with self.assertRaisesRegex(GateError, "Auth não rejeitou"):
            evaluate_http(transport, OWNER_TOKEN, OTHER_TOKEN)

    def test_http_error_does_not_expose_tokens_or_bodies(self):
        from urllib.error import HTTPError
        class Opener:
            def open(self, request, timeout):
                raise HTTPError(request.full_url, 403, OWNER_TOKEN + " sensitive", {}, None)
        reader = HttpReader(KEY, opener=Opener())
        self.assertEqual(reader.get("/auth/v1/user", OWNER_TOKEN), Response(403, None))

    def test_real_client_is_get_only_and_project_locked(self):
        class Endpoint:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, n): return json.dumps({"id": OWNER}).encode()
        class Opener:
            def __init__(self): self.requests = []
            def open(self, request, timeout):
                self.requests.append(request)
                return Endpoint()
        opener = Opener()
        reader = HttpReader(KEY, opener=opener)
        self.assertEqual(reader.get("/auth/v1/user", OWNER_TOKEN).status, 200)
        req = opener.requests[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(urlsplit(req.full_url).hostname, PROJECT_REF + ".supabase.co")
        self.assertEqual(req.headers["Authorization"], "Bearer " + OWNER_TOKEN)
        self.assertEqual(req.headers["Apikey"], KEY)
        for forbidden in ("//example.com", "/rest/v1/other_table?select=id", "/delete",
                          "https://evil.example", "/rest/v1/orbita_records"):
            with self.subTest(route=forbidden):
                with self.assertRaises(GateError):
                    reader.get(forbidden, OWNER_TOKEN)

    def test_redirect_is_never_followed(self):
        redirects = NoRedirects()
        self.assertIsNone(redirects.redirect_request(
            None, None, 302, "moved", {}, "https://evil.example/steal"))

    def test_requires_publishable_key_not_privileged_secret(self):
        for key in ("", "sb_secret_not_allowed", "service_role"):
            with self.subTest(key=key):
                with self.assertRaises(GateError):
                    HttpReader(key)

    def test_manual_optin_and_project_guards_fail_closed(self):
        cases = (
            {},
            {"ORBITA_E2E_HTTP_RUN": RUN_CONFIRMATION},
            {"ORBITA_E2E_HTTP_RUN": RUN_CONFIRMATION,
             "ORBITA_E2E_EXPECT_PROJECT": "someone_else"},
            {"ORBITA_E2E_HTTP_RUN": RUN_CONFIRMATION,
             "ORBITA_E2E_EXPECT_PROJECT": PROJECT_REF},
        )
        for env in cases:
            with self.subTest(env=env):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = main(env)
                self.assertEqual(code, 2)
                self.assertIn("NÃO EXECUTADO", out.getvalue())

    def test_cli_failure_never_prints_response_details_or_credentials(self):
        env = {
            "ORBITA_E2E_HTTP_RUN": RUN_CONFIRMATION,
            "ORBITA_E2E_EXPECT_PROJECT": PROJECT_REF,
            "ORBITA_E2E_OWNER_JWT": OWNER_TOKEN,
            "ORBITA_E2E_OTHER_JWT": OTHER_TOKEN,
            "ORBITA_E2E_PUBLISHABLE_KEY": KEY,
        }
        output = io.StringIO()
        with patch("auth_http_rls_probe.evaluate_http", side_effect=GateError(OWNER_TOKEN)):
            with contextlib.redirect_stdout(output):
                result = main(env)
        self.assertEqual(result, 1)
        self.assertNotIn(OWNER_TOKEN, output.getvalue())
        self.assertNotIn(KEY, output.getvalue())
        self.assertIn("BLOQUEADO", output.getvalue())

    def test_cli_with_empty_chat_fixture_remains_blocked(self):
        env = {
            "ORBITA_E2E_HTTP_RUN": RUN_CONFIRMATION,
            "ORBITA_E2E_EXPECT_PROJECT": PROJECT_REF,
            "ORBITA_E2E_OWNER_JWT": OWNER_TOKEN,
            "ORBITA_E2E_OTHER_JWT": OTHER_TOKEN,
            "ORBITA_E2E_PUBLISHABLE_KEY": KEY,
        }
        output = io.StringIO()
        with patch("auth_http_rls_probe.HttpReader", return_value=MockTransport(owner_chats=[])):
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(env), 1)
        self.assertIn("PENDENTE", output.getvalue())


if __name__ == "__main__":
    unittest.main()
