"""ORBITA 3.25: create a private, verifiable PostgreSQL archive on YOUR computer.

This is a local operator tool. It never contacts OpenAI/ChatGPT or Supabase
Management API, and never touches the database except pg_dump reads.
A verified archive is not the same thing as a tested restore.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

PROJECT = "tbqfymedgdsdrgkqmuni"
REQUIRED_TOC = {
    ("TABLE DATA", "public", "orbita_records"),
    ("TABLE DATA", "public", "orbita_chat_messages"),
    ("TABLE DATA", "public", "orbita_telegram_updates"),
    ("TABLE DATA", "auth", "users"),
}
ACK = "I_UNDERSTAND_BACKUP_IS_PRIVATE"
MAX_RUN_SECONDS = 600


class BackupError(Exception):
    pass


def validate_environment(env: dict[str, str], root: Path, directory: Path) -> None:
    if env.get("ORBITA_BACKUP_ACK") != ACK:
        raise BackupError("Confirmação de backup privado ausente.")
    if env.get("ORBITA_BACKUP_PROJECT") != PROJECT:
        raise BackupError("Projeto Supabase não confirmado.")
    host = env.get("PGHOST", "")
    user = env.get("PGUSER", "")
    if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
        raise BackupError("PGHOST inválido ou indisponível.")
    valid_direct = host == f"db.{PROJECT}.supabase.co"
    valid_pooler = host.endswith(".pooler.supabase.com") and user == f"postgres.{PROJECT}"
    if not (valid_direct or valid_pooler):
        raise BackupError("PGHOST/PGUSER não identificam o projeto ORBITA.")
    if env.get("PGDATABASE") != "postgres":
        raise BackupError("Use PGDATABASE=postgres para o projeto ORBITA.")
    if env.get("PGSSLMODE") not in ("require", "verify-full"):
        raise BackupError("PGSSLMODE exige TLS (require ou verify-full).")
    if not env.get("PGPORT", "").isdigit():
        raise BackupError("PGPORT inválido.")
    if not (env.get("PGPASSFILE") or env.get("PGPASSWORD")):
        raise BackupError("Configure uma senha privada em PGPASSFILE ou PGPASSWORD.")
    if env.get("PGPASSFILE"):
        pw = Path(env["PGPASSFILE"]).expanduser()
        if not pw.is_file() or (pw.stat().st_mode & 0o077):
            raise BackupError("PGPASSFILE deve existir e ter permissão 0600.")
    root = root.resolve()
    directory = directory.expanduser().resolve()
    if directory == root or root in directory.parents:
        raise BackupError("Nunca salvar backup privado dentro do repositório Git.")
    if not directory.is_dir():
        raise BackupError("Pasta de destino não existe.")
    if directory.stat().st_mode & 0o077:
        raise BackupError("Pasta do backup deve ter permissões 0700.")
    if not shutil.which("pg_dump") or not shutil.which("pg_restore"):
        raise BackupError("pg_dump e pg_restore são necessários na máquina local.")


def has_expected_tables(toc: str) -> tuple[bool, list[str]]:
    found = set()
    for line in toc.splitlines():
        if not line or line.lstrip().startswith(";"):
            continue
        for kind, schema, name in REQUIRED_TOC:
            if re.search(
                r"^\s*\d+;\s+\d+\s+\d+\s+" +
                re.escape(kind) + r"\s+" + re.escape(schema) + r"\s+" +
                re.escape(name) + r"(?:\s|$)", line
            ):
                found.add((kind, schema, name))
    missing = sorted(".".join((schema, name)) for kind, schema, name in REQUIRED_TOC
                     if (kind, schema, name) not in found)
    return not missing, missing


def run(argv: list[str], env: dict[str, str], timeout: int = MAX_RUN_SECONDS):
    """Never propagate subprocess stderr/stdout (may contain connection data)."""
    try:
        return subprocess.run(
            argv, env=env, capture_output=True, text=True, timeout=timeout,
            check=False
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise BackupError("Ferramenta PostgreSQL indisponível ou expirou.") from None


def create_backup(env: dict[str, str], root: Path, directory: Path,
                  *, clock=None) -> Path:
    validate_environment(env, root, directory)
    now = clock or dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    prefix = "orbita_" + PROJECT + "_" + stamp
    archive = directory / (prefix + ".dump")
    partial = directory / (prefix + ".partial")
    manifest = directory / (prefix + ".manifest.json")
    if any(path.exists() for path in (archive, partial, manifest)):
        raise BackupError("Arquivo existente; escolha uma nova execução.")
    oldmask = os.umask(0o077)
    try:
        # O_EXCL protects from race/symlink overwrite. pg_dump writes the
        # already reserved file, but never changes the permanent archive.
        fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        pg_env = {
            **env, "PGCONNECT_TIMEOUT": "10", "PGAPPNAME": "orbita-private-backup-3.25"
        }
        result = run(["pg_dump", "--format=custom", "--no-password",
                      "--file", str(partial)], pg_env)
        if result.returncode != 0 or partial.stat().st_size < 1024:
            raise BackupError("Exportação de banco falhou ou gerou arquivo inválido.")
        result = run(["pg_restore", "--list", str(partial)], pg_env, timeout=90)
        if result.returncode != 0:
            raise BackupError("Arquivo não pôde ser lido por pg_restore.")
        found, missing = has_expected_tables(result.stdout)
        if not found:
            raise BackupError("Backup incompleto: ausentes as tabelas esperadas.")
        with partial.open("rb") as reader:
            digest = hashlib.file_digest(reader, "sha256").hexdigest()
        archive_size = partial.stat().st_size
        os.replace(partial, archive)
        report = {
            "project_ref": PROJECT,
            "created_utc": now.isoformat(),
            "archive_filename": archive.name,
            "archive_bytes": archive_size,
            "sha256": digest,
            "toc_inspected": True,
            "expected_tables_present": True,
            "restore_tested": False,
            "recoverable_confirmed": False,
            "warning": "A integridade estrutural do dump não comprova restauração."
        }
        fd = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        return manifest
    except Exception:
        # Never leave a partial archive that could be accidentally mistaken
        # for a working backup. A complete archive may remain if manifest
        # writing fails; operator must inspect it manually.
        partial.unlink(missing_ok=True)
        raise
    finally:
        os.umask(oldmask)


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python quality/private_database_backup.py /pasta/privada/0700")
        return 2
    try:
        manifest = create_backup(os.environ, Path(__file__).resolve().parents[1],
                                 Path(sys.argv[1]))
    except BackupError as exc:
        # Only authored, non-sensitive errors are displayed.
        print("BLOQUEADO: " + str(exc))
        return 1
    except Exception:
        print("BLOQUEADO: erro inesperado; nenhuma migração foi aplicada.")
        return 1
    print("BACKUP ARQUIVADO — leia o manifesto privado:", manifest.name)
    print("Arquivo verificável por pg_restore --list, mas restauração NÃO testada.")
    print("SQL 002/003 continuam bloqueados até teste real de restauração isolada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
