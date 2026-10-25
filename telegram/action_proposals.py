"""Ações naturais supervisionadas do ORBITA.

O texto do usuário apenas monta uma proposta. Persistência de registros ocorre
EXCLUSIVAMENTE no método de confirmação idempotente do armazenamento.
"""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass

CODE_RE = re.compile(r"^[0-9A-F]{12}$")
PRIORITIES = {"P0", "P1", "P2", "P3"}
MAX_TITLE = 1000

@dataclass(frozen=True)
class ProposedAction:
    kind: str
    title: str
    priority: str

_PREFIX = r"(?:(?:v[âa]nia)\s*[,!:—-]?\s*)?(?:(?:por favor)\s*[,!:—-]?\s*)?"
_IDEA = re.compile(
    _PREFIX + r"(?:"
    r"(?:tive|tenho)\s+uma\s+ideia\s*(?:[:—-]\s*|de\s+)"
    r"|(?:anote|anota|registre|registra|guarde|guarda|salve|salva)"
    r"\s+(?:a\s+)?(?:seguinte\s+)?ideia\s*(?:[:—-]\s*|de\s+|que\s+)"
    r")(.+)$", re.IGNORECASE | re.DOTALL
)
_TASK = re.compile(
    _PREFIX + r"(?:"
    r"(?:anote|anota|registre|registra|guarde|guarda|salve|salva)\s+(?:que\s+)?"
    r"|(?:crie|cria|adicione|adiciona)\s+(?:uma\s+)?tarefa\s+(?:para\s+|de\s+|que\s+|:\s*)?"
    r"|(?:me\s+lembre|lembre-me|me\s+lembra)\s+de\s+"
    r")(.+)$", re.IGNORECASE | re.DOTALL
)
_TASK_INTRO = re.compile(
    r"^(?:(?:eu\s+)?(?:preciso\s+(?:de\s+)?|tenho\s+que\s+|devo\s+)|(?:uma\s+)?tarefa\s+(?:de\s+|para\s+))",
    re.IGNORECASE
)
_PRIORITY = re.compile(r"^(P[0-3])\s*[|:—-]\s*(.+)$", re.IGNORECASE | re.DOTALL)
_CONFIRM = re.compile(r"^/?(?:confirmar|confirme)\s+([0-9a-f]{12})\s*$", re.IGNORECASE)
_CANCEL = re.compile(r"^/?(?:cancelar|cancele)\s+([0-9a-f]{12})\s*$", re.IGNORECASE)


def parse_confirmation(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    for kind, pattern in (("confirm", _CONFIRM), ("cancel", _CANCEL)):
        matched = pattern.fullmatch(raw)
        if matched:
            return kind, matched.group(1).upper()
    return None


def classify_action(text: str) -> ProposedAction | None:
    """Somente pedidos explícitos, nunca uma discussão ou recomendação."""
    raw = (text or "").strip()
    if not raw or len(raw) > 1200 or raw.startswith("/"):
        return None
    kind = "ideia"
    match = _IDEA.fullmatch(raw)
    if not match:
        kind, match = "tarefa", _TASK.fullmatch(raw)
    if not match:
        return None

    title = " ".join(match.group(1).split())
    if kind == "tarefa":
        title = _TASK_INTRO.sub("", title).strip()
    title = title.strip(' \t\r\n:—-|')
    priority = "P3" if kind == "ideia" else "P2"
    if kind == "tarefa":
        priority_match = _PRIORITY.fullmatch(title)
        if priority_match:
            priority, title = priority_match.group(1).upper(), priority_match.group(2).strip()
        elif re.search(r"\b(?:urgente|urgência)\b", title, re.IGNORECASE):
            priority = "P1"
    if not title or len(title) > MAX_TITLE or title.lower() in {"isso", "algo", "uma coisa"}:
        return None
    return ProposedAction(kind, title, priority)


def new_code() -> str:
    return secrets.token_hex(6).upper()


def check_proposal(kind: str, title: str, priority: str, code: str) -> None:
    if kind not in {"tarefa", "ideia"} or priority not in PRIORITIES:
        raise ValueError("tipo ou prioridade inválidos")
    if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE:
        raise ValueError("título inválido")
    if not isinstance(code, str) or not CODE_RE.fullmatch(code):
        raise ValueError("código de confirmação inválido")


def preview(kind: str, title: str, priority: str, code: str) -> str:
    check_proposal(kind, title, priority, code)
    label = "tarefa" if kind == "tarefa" else "ideia"
    return (
        f"📝 Preparei uma proposta de {label}, mas ainda NÃO registrei nada.\n\n"
        f"Título: {title}\n"
        f"Prioridade: {priority}\n"
        "Prazo/alertas: não agendados automaticamente.\n\n"
        f"Para salvar, responda: confirmar {code}\n"
        f"Para descartar: cancelar {code}\n"
        "A proposta expira em 15 minutos."
    )
