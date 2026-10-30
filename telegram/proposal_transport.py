"""Telegram InlineKeyboard de confirmação para propostas ORBITA.

Callback data são apenas referências de propostas, não autorização independente.
O backend ainda verifica identidade, validade e consome a proposta no banco.
"""
from __future__ import annotations

import re

_PREVIEW = re.compile(
    r"^📝 Preparei uma proposta de (?:tarefa|ideia), mas ainda NÃO registrei nada\.",
    re.MULTILINE
)
_CONFIRM_LINE = re.compile(
    r"^Para salvar, responda: confirmar ([0-9A-F]{12})$",
    re.MULTILINE
)
_CALLBACK = re.compile(r"^orbita:(confirm|cancel):([0-9A-F]{12})$")


def inline_keyboard(answer: str) -> dict | None:
    if not isinstance(answer, str) or not _PREVIEW.search(answer):
        return None
    match = _CONFIRM_LINE.search(answer)
    if not match:
        return None
    code = match.group(1)
    return {"inline_keyboard": [[
        {"text": "✅ Confirmar", "callback_data": "orbita:confirm:" + code},
        {"text": "✕ Cancelar", "callback_data": "orbita:cancel:" + code}
    ]]}


def callback_as_confirmation(data: str | None) -> str | None:
    if not isinstance(data, str) or len(data) > 64:
        return None
    match = _CALLBACK.fullmatch(data)
    if not match:
        return None
    action, code = match.groups()
    return ("confirmar " if action == "confirm" else "cancelar ") + code
