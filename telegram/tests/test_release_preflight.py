"""Regressão do gate Supabase sem acessar serviços reais nem segredos."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "quality"))
from verify_release_report import BASE, ACTIONS, DELIVERY, REQUIRED, cli, evaluate, parse_json


class ReleasePreflightTests(unittest.TestCase):
    def ready(self):
        return {name: True for name in REQUIRED}

    def test_full_report_marks_schema_ready_for_e2e_only(self):
        status = evaluate(self.ready())
        self.assertEqual(status, {
            "base": True, "natural_actions": True, "webhook_delivery": True
        })

    def test_real_orbita_schema_snapshot_blocks_activation(self):
        report = self.ready()
        report.update({
            "proposal_table_exists": False,
            "proposal_rls": False,
            "proposal_service_access": False,
            "confirm_rpc_exists": False,
            "confirm_rpc_service_access": False,
            "confirm_rpc_security_invoker": False,
            "delivery_states_ready": False,
        })
        self.assertEqual(evaluate(report), {
            "base": True, "natural_actions": False, "webhook_delivery": False
        })

    def test_absent_boolean_field_fails_closed(self):
        for name in REQUIRED:
            with self.subTest(field=name):
                report = self.ready()
                del report[name]
                with self.assertRaises(ValueError):
                    evaluate(report)

    def test_non_boolean_true_does_not_pass(self):
        for bad in ("true", 1, {}, None, []):
            with self.subTest(value=bad):
                report = self.ready()
                report["proposal_rls"] = bad
                with self.assertRaises(ValueError):
                    evaluate(report)

    def test_one_insecure_grant_blocks_proposals(self):
        for name in ACTIONS:
            with self.subTest(name=name):
                report = self.ready()
                report[name] = False
                self.assertFalse(evaluate(report)["natural_actions"])

    def test_legacy_status_constraint_blocks_delivery_only(self):
        report = self.ready()
        report["delivery_states_ready"] = False
        status = evaluate(report)
        self.assertTrue(status["base"])
        self.assertTrue(status["natural_actions"])
        self.assertFalse(status["webhook_delivery"])

    def test_missing_base_rls_blocks_baseline(self):
        report = self.ready()
        report["base_tables_rls"] = False
        self.assertFalse(evaluate(report)["base"])

    def test_report_wrapped_or_direct_is_readable(self):
        report = self.ready()
        self.assertEqual(parse_json(json.dumps(report)), report)
        self.assertEqual(parse_json(json.dumps({"report": report})), report)

    def test_invalid_top_level_json_is_rejected(self):
        for entry in ("[]", "null", '"yes"'):
            with self.subTest(entry=entry):
                with self.assertRaises(ValueError):
                    parse_json(entry)

    def test_cli_returns_success_only_when_all_schema_checks_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "report.json"
            file.write_text(json.dumps(self.ready()), encoding="utf-8")
            self.assertEqual(cli(str(file)), 0)
            report = self.ready()
            report["delivery_states_ready"] = False
            file.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(cli(str(file)), 1)
            file.write_text("not JSON", encoding="utf-8")
            self.assertEqual(cli(str(file)), 2)

    def test_query_never_includes_mutating_statements(self):
        sql = (ROOT / "infra" / "supabase" / "preflight_readonly.sql"
               ).read_text(encoding="utf-8")
        # Checa somente linhas executáveis, ignorando comentários SQL.
        executable = "\n".join(
            line.split("--", 1)[0] for line in sql.splitlines()
        ).upper()
        import re
        for word in ("INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "CREATE",
                     "TRUNCATE", "CALL", "DO", "GRANT", "REVOKE"):
            with self.subTest(statement=word):
                self.assertIsNone(re.search(r"\b" + word + r"\b", executable))
        self.assertIn("SELECT JSONB_BUILD_OBJECT(", executable)


if __name__ == "__main__":
    unittest.main()
