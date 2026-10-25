"""Offline validator for the ORBITA read-only, rollback-only RLS rehearsal.

The SQL uses SET LOCAL ROLE and a synthetic subject in PostgreSQL. This checks
RLS policy behavior but is NOT a substitute for two real Supabase Auth/JWT HTTP
sessions. No tokens, database access, or mutations are performed by this tool.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FIELDS = (
    "owner_has_visible_record",
    "nonowner_isolated",
    "telegram_private",
    "anon_restricted",
    "nonowner_chat_isolated",
    "owner_chat_count_nonnegative",
)


def evaluate(value: object) -> bool:
    if not isinstance(value, dict):
        raise ValueError("O relatório RLS deve ser um objeto JSON.")
    missing = [field for field in FIELDS if not isinstance(value.get(field), bool)]
    if missing:
        raise ValueError("Campos booleanos ausentes ou incorretos: " + ", ".join(missing))
    return all(value[field] is True for field in FIELDS)


def cli(path: str) -> int:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict) and "rls_access_evidence" in data:
            data = data["rls_access_evidence"]
        valid = evaluate(data)
    except (ValueError, OSError, TypeError) as exc:
        print("Relatório RLS inválido: " + type(exc).__name__)
        return 2
    print("OK — RLS simulado passou" if valid else "BLOQUEADO — RLS simulado falhou")
    print("Verificação transacional de papéis; exige sessões HTTP com JWTs reais.")
    return 0 if valid else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python quality/verify_rls_role_report.py resultado.json")
        sys.exit(2)
    sys.exit(cli(sys.argv[1]))
