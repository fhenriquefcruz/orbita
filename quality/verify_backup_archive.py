"""Verify a private ORBITA PostgreSQL archive after copying to secure storage.

Read-only verification of local archive bytes and pg_restore table of contents.
NEVER certifies that a full restore succeeded in an isolated database.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from private_database_backup import PROJECT, has_expected_tables, BackupError


def verify(manifest_file: Path) -> dict[str, object]:
    path = manifest_file.expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_mode & 0o077:
        raise BackupError("Manifesto deve ser um arquivo privado 0600.")
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError):
        raise BackupError("Manifesto JSON inválido.") from None
    if not isinstance(metadata, dict) or metadata.get("project_ref") != PROJECT:
        raise BackupError("O manifesto não pertence ao Supabase ORBITA.")
    name = metadata.get("archive_filename")
    if (not isinstance(name, str) or
            not re.fullmatch(r"orbita_" + PROJECT + r"_\d{8}T\d{6}Z\.dump", name)):
        raise BackupError("Nome do arquivo de backup inesperado.")
    archive = path.parent / name
    if not archive.is_file() or archive.is_symlink() or archive.stat().st_mode & 0o077:
        raise BackupError("Arquivo de backup ausente ou não privado 0600.")
    if not isinstance(metadata.get("archive_bytes"), int) or (
        archive.stat().st_size != metadata["archive_bytes"]
    ):
        raise BackupError("Arquivo de backup com tamanho divergente.")
    with archive.open("rb") as reader:
        digest = hashlib.file_digest(reader, "sha256").hexdigest()
    if digest != metadata.get("sha256"):
        raise BackupError("Checksum SHA-256 divergente; possível corrupção.")
    if not shutil.which("pg_restore"):
        raise BackupError("pg_restore indisponível no computador.")
    try:
        proc = subprocess.run(["pg_restore","--list",str(archive)],
                              capture_output=True,text=True,timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        raise BackupError("Falha local na ferramenta pg_restore.") from None
    if proc.returncode != 0:
        raise BackupError("pg_restore não reconheceu o arquivo.")
    valid,missing = has_expected_tables(proc.stdout)
    if not valid:
        raise BackupError("Tabelas obrigatórias ausentes: "+", ".join(missing))
    return {
        "archive_integrity_verified": True,
        "expected_tables_present": True,
        "restoration_tested": False,
        "fully_recoverable_confirmed": False,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python quality/verify_backup_archive.py /pasta/privada/manifest.json")
        return 2
    try:
        result = verify(Path(sys.argv[1]))
    except (OSError, BackupError, ValueError):
        print("BLOQUEADO — integridade do backup não confirmada.")
        return 1
    print("APROVADO — checksum, tamanho e catálogo PostgreSQL conferidos.")
    print("PENDENTE — restaurar uma cópia em ambiente isolado antes de")
    print("declarar o backup recuperável e aplicar SQL 002/003.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
