"""Sem internet e sem credenciais: valida o assistente de homologação real."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "quality"))
import run_auth_homologation as flow  # noqa: E402


class FakeOpener:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return json.dumps(self.data).encode("utf-8")[:size]


class HomologationCLI(unittest.TestCase):
    def test_public_key_only_from_exclusive_project(self):
        src = ("window.ORBITA_CLOUD_PUBLIC={"
               "url:'https://tbqfymedgdsdrgkqmuni.supabase.co',"
               "publishableKey:'sb_publishable_sample'};")
        self.assertEqual(flow.public_key_from_config(src), "sb_publishable_sample")

    def test_wrong_project_or_privileged_key_blocked(self):
        variants = [
            "url:'https://another.supabase.co', publishableKey:'sb_publishable_valid'",
            "url:'https://tbqfymedgdsdrgkqmuni.supabase.co', publishableKey:'sb_secret_invalid'",
            "url:'http://tbqfymedgdsdrgkqmuni.supabase.co', publishableKey:'sb_publishable_x'"
        ]
        for item in variants:
            with self.subTest(item=item), self.assertRaises(flow.GateError):
                flow.public_key_from_config(item)

    def test_sign_in_posts_only_to_fixed_auth_endpoint(self):
        token = "eyJhbGciOiJub25lIn0.e30.fake_signature"
        opener = FakeOpener({"access_token": token, "refresh_token": "do-not-log-me"})
        result = flow.sign_in("test@example.invalid", "dont-print-password",
                              "sb_publishable_sample", opener=opener)
        self.assertEqual(result, token)
        self.assertEqual(len(opener.requests), 1)
        request = opener.requests[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.full_url, flow.PROJECT_URL + "/auth/v1/token?grant_type=password")
        self.assertNotIn("dont-print-password", request.full_url)

    def test_rejects_non_jwt_or_oversized_response(self):
        with self.assertRaises(flow.GateError):
            flow.sign_in("test@example.invalid", "password", "sb_publishable_sample",
                         opener=FakeOpener({"access_token": "not-valid"}))

    def test_no_network_without_opt_in(self):
        with patch("builtins.input", return_value="NÃO"):
            self.assertEqual(flow.run(), 2)

    def test_no_login_without_second_identity(self):
        with patch("builtins.input", side_effect=["HOMOLOGAR", "same@example.invalid",
                                                   "same@example.invalid"]), \
             patch("getpass.getpass", return_value="secret"), \
             patch.object(flow.CONFIG, "read_text",
                          return_value="url:'https://tbqfymedgdsdrgkqmuni.supabase.co',"
                                       "publishableKey:'sb_publishable_test'"), \
             patch.object(flow, "sign_in") as login:
            self.assertEqual(flow.run(), 1)
            login.assert_not_called()


if __name__ == "__main__":
    unittest.main()
