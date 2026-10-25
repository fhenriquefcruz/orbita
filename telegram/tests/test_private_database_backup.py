"""Aurora 3.25: no database is contacted or secrets read during CI tests."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"quality"))
from private_database_backup import (
  ACK, PROJECT, BackupError, create_backup, has_expected_tables, validate_environment
)

TOC = """\
; PGDMP - archive list
1; 0 126 TABLE DATA auth users postgres
2; 0 127 TABLE DATA public orbita_records postgres
3; 0 128 TABLE DATA public orbita_chat_messages postgres
4; 0 129 TABLE DATA public orbita_telegram_updates postgres
"""


class PrivateBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        folder=Path(self.tmp.name)
        self.root=folder/"repo"
        self.root.mkdir(mode=0o700)
        self.dest=folder/"private"
        self.dest.mkdir(mode=0o700)
        self.env={
            "ORBITA_BACKUP_ACK": ACK,
            "ORBITA_BACKUP_PROJECT": PROJECT,
            "PGHOST":f"db.{PROJECT}.supabase.co",
            "PGUSER":"postgres",
            "PGDATABASE":"postgres",
            "PGSSLMODE":"require",
            "PGPORT":"5432",
            "PGPASSWORD":"mock_local_only",
        }

    def validate(self, env=None, directory=None):
        with patch("private_database_backup.shutil.which",return_value="/usr/bin/pg_dump"):
            validate_environment(env or self.env,self.root,directory or self.dest)

    def test_matching_project_is_accepted(self):
        self.validate()

    def test_missing_ack_blocks_work(self):
        env={**self.env}
        del env["ORBITA_BACKUP_ACK"]
        with self.assertRaises(BackupError):
            self.validate(env)

    def test_wrong_project_never_targets_other_database(self):
        env={**self.env,"ORBITA_BACKUP_PROJECT":"a-different-project"}
        with self.assertRaises(BackupError):
            self.validate(env)

    def test_wrong_hostname_rejected(self):
        for host in ("example.com", "db.other.supabase.co",
                     f"db.{PROJECT}.supabase.co.attacker.invalid",""):
            with self.subTest(host=host):
                with self.assertRaises(BackupError):
                    self.validate({**self.env,"PGHOST":host})

    def test_pooler_requires_project_scoped_pguser(self):
        env={**self.env,
             "PGHOST":"aws-0-sa-east-1.pooler.supabase.com",
             "PGUSER":"postgres." + PROJECT}
        self.validate(env)
        env["PGUSER"]="postgres.someoneelse"
        with self.assertRaises(BackupError):
            self.validate(env)

    def test_tls_is_mandatory(self):
        for mode in ("disable","prefer","allow",""):
            with self.subTest(mode=mode):
                with self.assertRaises(BackupError):
                    self.validate({**self.env,"PGSSLMODE":mode})

    def test_no_secrets_in_configuration_fails(self):
        env={**self.env}
        del env["PGPASSWORD"]
        with self.assertRaises(BackupError):
            self.validate(env)

    def test_private_backup_cannot_live_inside_repo(self):
        inside=self.root/"backup"
        inside.mkdir(mode=0o700)
        with self.assertRaises(BackupError):
            self.validate(directory=inside)

    def test_world_readable_directory_is_rejected(self):
        os.chmod(self.dest,0o755)
        with self.assertRaises(BackupError):
            self.validate()

    def test_password_file_requires_private_permissions(self):
        password_file=Path(self.tmp.name)/"pgpass"
        password_file.write_text("fake:5432:*:postgres:mock",encoding="utf-8")
        os.chmod(password_file,0o644)
        env={**self.env,"PGPASSFILE":str(password_file)}
        with self.assertRaises(BackupError):
            self.validate(env)
        os.chmod(password_file,0o600)
        self.validate(env)

    def test_detect_archive_missing_managed_auth_user_table(self):
        ok,missing=has_expected_tables(TOC)
        self.assertTrue(ok)
        self.assertEqual(missing,[])
        ok,missing=has_expected_tables(TOC.replace("TABLE DATA auth users","TABLE DATA auth sessions"))
        self.assertFalse(ok)
        self.assertIn("auth.users",missing)

    def test_local_mock_backup_writes_only_private_archive_and_manifest(self):
        def fake_run(argv,env,timeout=600):
            if argv[0]=="pg_dump":
                Path(argv[argv.index("--file")+1]).write_bytes(b"P"*4096)
                return CompletedProcess(argv,0,"","")
            return CompletedProcess(argv,0,TOC,"")
        now=dt.datetime(2026,10,25,10,0,tzinfo=dt.timezone.utc)
        with patch("private_database_backup.shutil.which",return_value="/usr/bin/pg_dump"):
            with patch("private_database_backup.run",side_effect=fake_run) as runner:
                manifest=create_backup(self.env,self.root,self.dest,clock=now)
        report=json.loads(manifest.read_text(encoding="utf-8"))
        archive=self.dest/report["archive_filename"]
        self.assertTrue(archive.is_file())
        self.assertEqual(report["sha256"],hashlib.sha256(b"P"*4096).hexdigest())
        self.assertFalse(report["restore_tested"])
        self.assertFalse(report["recoverable_confirmed"])
        self.assertTrue(report["expected_tables_present"])
        self.assertEqual(archive.stat().st_mode & 0o777,0o600)
        self.assertEqual(manifest.stat().st_mode & 0o777,0o600)
        self.assertEqual(runner.call_count,2)
        self.assertNotIn("mock_local_only",str(runner.call_args_list[0].args[0]))

    def test_pg_dump_failure_deletes_partial_archive(self):
        def fake_run(argv,env,timeout=600):
            Path(argv[argv.index("--file")+1]).write_bytes(b"failed")
            return CompletedProcess(argv,1,"","sensitive private error")
        with patch("private_database_backup.shutil.which",return_value="/usr/bin/pg_dump"):
            with patch("private_database_backup.run",side_effect=fake_run):
                with self.assertRaises(BackupError):
                    create_backup(self.env,self.root,self.dest)
        self.assertEqual(list(self.dest.glob("*")),[])

    def test_bad_toc_never_marks_backup_verified(self):
        def fake_run(argv,env,timeout=600):
            if argv[0]=="pg_dump":
                Path(argv[argv.index("--file")+1]).write_bytes(b"x"*2048)
                return CompletedProcess(argv,0,"","")
            return CompletedProcess(argv,0,TOC.replace("orbita_records","wrong_table"),"")
        with patch("private_database_backup.shutil.which",return_value="/usr/bin/pg_dump"):
            with patch("private_database_backup.run",side_effect=fake_run):
                with self.assertRaises(BackupError):
                    create_backup(self.env,self.root,self.dest)
        self.assertEqual(list(self.dest.glob("*")),[])

    def test_existing_backup_not_overwritten(self):
        now=dt.datetime(2026,10,25,10,0,tzinfo=dt.timezone.utc)
        path=self.dest/f"orbita_{PROJECT}_20261025T100000Z.dump"
        path.write_text("preserve me",encoding="utf-8")
        with patch("private_database_backup.shutil.which",return_value="/usr/bin/pg_dump"):
            with self.assertRaises(BackupError):
                create_backup(self.env,self.root,self.dest,clock=now)
        self.assertEqual(path.read_text(encoding="utf-8"),"preserve me")


if __name__=="__main__":
    unittest.main()
