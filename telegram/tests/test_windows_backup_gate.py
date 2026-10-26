"""Aurora 3.28 | Offline static gates for the private Windows backup workflow.

Linux CI does not call Windows tools, does not connect to the database, and
never handles credentials. This catches accidental removal of safety gates.
"""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    ROOT / "quality" / "private_database_backup_windows.ps1",
    ROOT / "quality" / "verify_database_backup_windows.ps1",
]


class WindowsBackupStaticGates(unittest.TestCase):
    def script(self, i: int):
        return SCRIPTS[i].read_text(encoding="utf-8")

    def test_files_are_present_and_nonempty(self):
        for path in SCRIPTS:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 1500)

    def test_main_requires_windows_and_operator_project_confirmation(self):
        s = self.script(0)
        self.assertIn("Win32NT", s)
        self.assertIn("$ConfirmProject -ne $ref", s)
        self.assertIn("[switch]$CheckPrerequisites", s)
        self.assertIn("if ($CheckPrerequisites)", s)

    def test_preflight_no_database_credentials(self):
        s = self.script(0)
        preflight = s[:s.index('if ($CheckPrerequisites)')]
        self.assertNotIn("Read-Host", preflight)
        self.assertNotIn("pg_dump --format", preflight)

    def test_hostname_scoped_to_project(self):
        s = self.script(0)
        self.assertIn("db.", s)
        self.assertIn(r"pooler\\.supabase\\.com", s)
        self.assertIn("postgres.", s)
        self.assertIn('"5432"', s)
        self.assertIn('"require"', s)

    def test_ntfs_acl_restricted_with_no_broad_principals(self):
        s = self.script(0)
        for text in ("icacls.exe", "/inheritance:r", "Assert-Private",
                     "AreAccessRulesProtected", "S-1-5-18", "S-1-5-32-544"):
            self.assertIn(text, s)
        for forbidden in ("Everyone:(F)", "Authenticated Users:(F)", 
                          "/inheritance:e"):
            self.assertNotIn(forbidden, s)

    def test_secret_entered_hidden_and_cleared(self):
        s = self.script(0)
        self.assertIn("Read-Host", s)
        self.assertIn("-AsSecureString", s)
        self.assertIn("ZeroFreeBSTR", s)
        self.assertIn("$env:PGPASSWORD = $null", s)
        self.assertIn("finally {", s)
        self.assertNotIn("Write-Output $env:PGPASSWORD", s)

    def test_backup_is_custom_archive_and_checks_toc(self):
        s = self.script(0)
        for p in ("--format=custom", "--no-password", "--list",
                  "Get-FileHash", "-Algorithm SHA256", "TABLE DATA",
                  "orbita_records", "orbita_chat_messages",
                  "orbita_telegram_updates", '"auth","users"'):
            self.assertIn(p, s)

    def test_restore_is_never_claimed_complete(self):
        for s in map(lambda i: self.script(i), range(2)):
            self.assertIn("RESTAURACAO", s)
        self.assertIn("restore_tested = $false", self.script(0))
        self.assertIn("recoverable_confirmed = $false", self.script(0))

    def test_no_automatic_database_mutation_or_production_release(self):
        for s in map(lambda i: self.script(i), range(2)):
            self.assertNotIn("apply_migration", s)
            self.assertNotIn("supabase db push", s)
            self.assertNotIn("vercel --prod", s)
            self.assertNotIn("git push", s)
            self.assertNotIn("--clean", s)

    def test_verifier_requires_hash_toc_private_acl_and_project(self):
        s = self.script(1)
        for p in ("Get-FileHash", "SHA256", "Assert-Private", 
                  "AreAccessRulesProtected", "pg_restore", "--list",
                  "TABLE DATA", "project_ref", "archive_filename",
                  "archive_bytes"):
            self.assertIn(p, s)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell not installed on Linux runner")
    def test_powershell_source_parses_without_running_any_commands(self):
        for path in SCRIPTS:
            with self.subTest(script=path.name):
                expr = (
                    "$tokens=$null;$errors=$null;"
                    "[System.Management.Automation.Language.Parser]::ParseFile("
                    "[Console]::ReadLine(),[ref]$tokens,[ref]$errors)|Out-Null;"
                    "if($errors.Count){exit 1}else{exit 0}"
                )
                result = subprocess.run(
                    ["pwsh", "-NoProfile", "-NonInteractive", "-Command", expr],
                    input=str(path) + "\n", capture_output=True, text=True,
                    timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr[:150])


if __name__ == "__main__":
    unittest.main()
