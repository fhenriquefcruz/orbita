"""ORBITA Aurora 3.21: interpreta relatório SQL SEM conectar ao banco.

Execute preflight_readonly.sql no projeto dedicado e salve SOMENTE o objeto
JSON 'report' emitido na consulta. Nunca cole tokens ou strings de conexão.
Este programa avalia estrutura/permissões; não libera implantação por si só.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = ("base_tables_exist", "base_tables_rls")
ACTIONS = (
    "proposal_table_exists", "proposal_rls",
    "proposal_client_access_blocked", "proposal_service_access",
    "confirm_rpc_exists", "confirm_rpc_client_access_blocked",
    "confirm_rpc_service_access", "confirm_rpc_security_invoker",
)
DELIVERY = ("delivery_states_ready",)
REQUIRED = BASE + ACTIONS + DELIVERY


def evaluate(report: object) -> dict[str, bool]:
    """Validação fechada: todos os campos existem e são booleanos verdadeiros."""
    if not isinstance(report, dict):
        raise ValueError("Relatório deve ser um objeto JSON.")
    missing = [name for name in REQUIRED if not isinstance(report.get(name), bool)]
    if missing:
        raise ValueError("Campos booleanos ausentes/inválidos: " + ", ".join(missing))
    return {
        "base": all(report[name] is True for name in BASE),
        "natural_actions": all(report[name] is True for name in ACTIONS),
        "webhook_delivery": all(report[name] is True for name in DELIVERY),
    }


def parse_json(content: str) -> dict:
    data = json.loads(content)
    if isinstance(data, dict) and "report" in data:
        data = data["report"]
    if not isinstance(data, dict):
        raise ValueError("Formato inválido: use o objeto JSON da coluna report.")
    return data


def cli(path: str) -> int:
    try:
        raw = Path(path).read_text(encoding="utf-8")
        status = evaluate(parse_json(raw))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("Relatório inválido ou indisponível: " + type(error).__name__)
        return 2

    messages = (
        ("base", "Memória e RLS base"),
        ("natural_actions", "Propostas e RPC protegida (SQL 002)"),
        ("webhook_delivery", "Status de entrega Telegram (SQL 003)"),
    )
    for field, label in messages:
        print(("OK" if status[field] else "PENDENTE") + " — " + label)
    print("Validação de estrutura somente. Testes com contas reais, webhook, "
          "recuperação, Safari e permissões HTTP continuam obrigatórios.")
    return 0 if all(status.values()) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python quality/verify_release_report.py resultado.json")
        sys.exit(2)
    sys.exit(cli(sys.argv[1]))
