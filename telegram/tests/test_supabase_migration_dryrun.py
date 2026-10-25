"""Offline quality gates for rollback-only PostgreSQL migration rehearsal."""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "quality"))
from build_supabase_dryrun import build


class DryRunBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = build()

    def test_one_transaction_ends_in_rollback(self):
        executable = "\n".join(line.split("--", 1)[0] for line in self.sql.splitlines())
        self.assertEqual(len(re.findall(r"(?im)^\s*BEGIN\s*;", executable)), 1)
        self.assertEqual(len(re.findall(r"(?im)^\s*ROLLBACK\s*;", executable)), 1)
        self.assertFalse(re.search(r"(?im)^\s*COMMIT\s*;", executable))
        self.assertTrue(executable.rstrip().endswith("ROLLBACK;"))

    def test_migrations_are_applied_inside_single_dry_run(self):
        first = self.sql.index("create table if not exists public.orbita_action_proposals")
        second = self.sql.index("alter table public.orbita_telegram_updates")
        dryrun = self.sql.index("DO $orbita_homologation$")
        rollback = self.sql.rindex("ROLLBACK;")
        self.assertLess(first, second)
        self.assertLess(second, dryrun)
        self.assertLess(dryrun, rollback)

    def test_security_and_idempotency_are_exercised(self):
        for text in ("has_function_privilege('anon'",
                     "has_function_privilege('authenticated'",
                     "has_function_privilege('service_role'",
                     "'already'", "'missing'", "'cancelled'", "'expired'",
                     "ORBITA DRY-RUN TEMPORARY TASK", "first_sequence"):
            self.assertIn(text, self.sql)

    def test_schema_keeps_existing_telegram_replied_status(self):
        self.assertIn("'received', 'replied', 'processed', 'delivered'", self.sql)

    def test_query_bounded_by_lock_and_statement_timeouts(self):
        self.assertIn("SET LOCAL lock_timeout='2s';", self.sql)
        self.assertIn("SET LOCAL statement_timeout='12s';", self.sql)

    def test_no_environment_token_or_database_uri(self):
        for forbidden in ("SUPABASE_SECRET_KEY=", "TELEGRAM_BOT_TOKEN=",
                          "postgresql://", "sb_secret_", "OPENAI_API_KEY="):
            self.assertNotIn(forbidden, self.sql)

    def test_missing_migration_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(OSError):
                build(Path(temp))

    def test_unexpected_transaction_in_first_migration_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)/"infra"/"supabase"
            directory.mkdir(parents=True)
            (directory/"002_action_proposals.sql").write_text(
                "create table if not exists public.orbita_action_proposals (id int);\n"
                "create or replace function public.orbita_confirm_action_proposal() "
                "returns int language sql as $$ select 1 $$;\nCOMMIT;\n",
                encoding="utf-8")
            (directory/"003_telegram_delivery.sql").write_text(
                "alter table public.orbita_telegram_updates add column demo int;\n",
                encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "controle de transação"):
                build(Path(temp))

    def test_unrecognized_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)/"infra"/"supabase"
            directory.mkdir(parents=True)
            (directory/"002_action_proposals.sql").write_text(
                "SELECT 1;", encoding="utf-8")
            (directory/"003_telegram_delivery.sql").write_text(
                "SELECT 2;", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "não correspondem"):
                build(Path(temp))


if __name__ == "__main__":
    unittest.main()
