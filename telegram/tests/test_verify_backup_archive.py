"""Local-only integrity verification and release gate for archived ORBITA dumps."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"quality"))
from private_database_backup import PROJECT, BackupError
from verify_backup_archive import verify

TOC="""\
1; 0 126 TABLE DATA auth users postgres
2; 0 127 TABLE DATA public orbita_records postgres
3; 0 128 TABLE DATA public orbita_chat_messages postgres
4; 0 129 TABLE DATA public orbita_telegram_updates postgres
"""


class BackupVerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        self.dump=self.dir/f"orbita_{PROJECT}_20261025T100000Z.dump"
        self.dump.write_bytes(b"X"*4096)
        os.chmod(self.dump,0o600)
        self.manifest=self.dir/"index.manifest.json"
        self.data={
            "project_ref":PROJECT,"archive_filename":self.dump.name,
            "archive_bytes":self.dump.stat().st_size,
            "sha256":hashlib.sha256(b"X"*4096).hexdigest(),
        }
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.data),encoding="utf-8")
        os.chmod(self.manifest,0o600)

    def verified(self, toc=TOC):
        with patch("verify_backup_archive.shutil.which",return_value="/bin/pg_restore"),\
             patch("verify_backup_archive.subprocess.run",
                   return_value=CompletedProcess([],0,toc,"")):
            return verify(self.manifest)

    def test_good_archive_still_does_not_claim_restored(self):
        status=self.verified()
        self.assertTrue(status["archive_integrity_verified"])
        self.assertTrue(status["expected_tables_present"])
        self.assertFalse(status["restoration_tested"])
        self.assertFalse(status["fully_recoverable_confirmed"])

    def test_checksum_tampering_is_rejected(self):
        self.dump.write_bytes(b"tampered")
        with self.assertRaises(BackupError):
            self.verified()

    def test_corrupted_checksum_is_rejected(self):
        self.data["sha256"]="a"*64
        self.save()
        with self.assertRaises(BackupError):
            self.verified()

    def test_different_project_is_rejected(self):
        self.data["project_ref"]="not-orbita"
        self.save()
        with self.assertRaises(BackupError):
            self.verified()

    def test_path_traversal_archive_filename_is_rejected(self):
        self.data["archive_filename"]="../secret"
        self.save()
        with self.assertRaises(BackupError):
            self.verified()

    def test_missing_auth_users_in_dump_blocks(self):
        with self.assertRaisesRegex(BackupError,"auth.users"):
            self.verified(toc=TOC.replace("TABLE DATA auth users","TABLE DATA auth other"))

    def test_manifest_cannot_be_public(self):
        os.chmod(self.manifest,0o644)
        with self.assertRaises(BackupError):
            self.verified()

    def test_dump_cannot_be_public(self):
        os.chmod(self.dump,0o644)
        with self.assertRaises(BackupError):
            self.verified()

    def test_missing_archive_fails_closed(self):
        self.dump.unlink()
        with self.assertRaises(BackupError):
            self.verified()

    def test_pg_restore_failure_blocks(self):
        with patch("verify_backup_archive.shutil.which",return_value="/bin/pg_restore"),\
             patch("verify_backup_archive.subprocess.run",
                   return_value=CompletedProcess([],1,"","private error")):
            with self.assertRaises(BackupError):
                verify(self.manifest)


if __name__=="__main__":
    unittest.main()
