import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"quality"))
from verify_rls_role_report import FIELDS, evaluate, cli


class RLSRehearsalTests(unittest.TestCase):
    def ready(self):
        return {name:True for name in FIELDS}

    def test_clean_report_passes_but_requires_jwt_http(self):
        self.assertTrue(evaluate(self.ready()))

    def test_each_denial_and_owner_gate_blocks(self):
        for name in FIELDS:
            with self.subTest(field=name):
                report=self.ready()
                report[name]=False
                self.assertFalse(evaluate(report))

    def test_missing_field_fails_closed(self):
        for name in FIELDS:
            with self.subTest(field=name):
                report=self.ready()
                del report[name]
                with self.assertRaises(ValueError):
                    evaluate(report)

    def test_truthy_nonboolean_fails_closed(self):
        for bad in ("true",1,[],None):
            with self.subTest(value=bad):
                report=self.ready()
                report["nonowner_isolated"]=bad
                with self.assertRaises(ValueError):
                    evaluate(report)

    def test_list_or_string_report_rejected(self):
        for bad in ([], "pass", None, 1):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    evaluate(bad)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/"rls.json"
            file.write_text(json.dumps({"rls_access_evidence":self.ready()}),encoding="utf-8")
            self.assertEqual(cli(str(file)),0)
            bad=self.ready()
            bad["anon_restricted"]=False
            file.write_text(json.dumps(bad),encoding="utf-8")
            self.assertEqual(cli(str(file)),1)
            file.write_text("not valid json",encoding="utf-8")
            self.assertEqual(cli(str(file)),2)

    def test_sql_is_rollback_only(self):
        sql=(ROOT/"infra"/"supabase"/"rls_role_rehearsal.sql").read_text(encoding="utf-8")
        cleaned="\n".join(line.split("--",1)[0] for line in sql.splitlines())
        self.assertEqual(len(re.findall(r"(?im)^\s*BEGIN\s*;",cleaned)),1)
        self.assertEqual(len(re.findall(r"(?im)^\s*ROLLBACK\s*;",cleaned)),1)
        self.assertTrue(cleaned.rstrip().endswith("ROLLBACK;"))
        self.assertFalse(re.search(r"(?im)^\s*COMMIT\s*;",cleaned))

    def test_sql_has_no_data_mutation_and_two_roles(self):
        sql=(ROOT/"infra"/"supabase"/"rls_role_rehearsal.sql").read_text(encoding="utf-8")
        cleaned="\n".join(line.split("--",1)[0] for line in sql.splitlines()).upper()
        without_strings=re.sub(r"'(?:''|[^'])*'","''",cleaned)
        for keyword in ("UPDATE","INSERT","DELETE","DROP","ALTER","CREATE",
                        "TRUNCATE","GRANT","REVOKE"):
            with self.subTest(keyword=keyword):
                self.assertIsNone(re.search(r"\b"+keyword+r"\b",without_strings))
        self.assertIn("SET LOCAL ROLE AUTHENTICATED;",cleaned)
        self.assertIn("SET LOCAL ROLE ANON;",cleaned)
        self.assertIn("RESET ROLE;",cleaned)

    def test_sql_never_discloses_identity(self):
        sql=(ROOT/"infra"/"supabase"/"rls_role_rehearsal.sql").read_text(encoding="utf-8")
        self.assertIn("AS rls_access_evidence",sql)
        self.assertNotIn("supabase_secret_key",sql.lower())
        self.assertNotIn("telegram_bot_token",sql.lower())
        self.assertNotIn("RETURNING user_id",sql)
        self.assertNotIn("SELECT * FROM public.orbita_records",sql)


if __name__=="__main__":
    unittest.main()
