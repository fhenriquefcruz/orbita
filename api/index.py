"""Webhook HTTPS para execução sem processo de polling (Vercel/ASGI).

Nunca aceite atualizações sem o X-Telegram-Bot-Api-Secret-Token ou faça
alterações para IDs não autorizados. Sem variáveis privadas retorna 503.
"""
from __future__ import annotations

import hmac
import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "telegram"))
from bot import reply_text, telegram_call  # noqa: E402
from cloud_memory import CloudMemory  # noqa: E402

app = FastAPI(title="ORBITA API", docs_url=None, redoc_url=None, openapi_url=None)
LOGGER = logging.getLogger("orbita.webhook")


def config():
    keys = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET", "ORBITA_OWNER_ID",
            "SUPABASE_URL", "SUPABASE_SECRET_KEY", "ORBITA_USER_UUID")
    values = {key: os.environ.get(key, "").strip() for key in keys}
    if not all(values.values()) or not values["ORBITA_OWNER_ID"].isdecimal():
        raise HTTPException(503, "Integração ainda não configurada")
    return values


@app.get("/api/health")
def health():
    return {"service": "orbita", "status": "running", "webhook_configured": all(
        os.environ.get(k) for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET",
                                  "SUPABASE_URL", "SUPABASE_SECRET_KEY", "ORBITA_USER_UUID"))}


@app.post("/api/telegram")
async def telegram_webhook(request: Request,
                           x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    cfg = config()
    if not x_telegram_bot_api_secret_token or not hmac.compare_digest(
            x_telegram_bot_api_secret_token, cfg["TELEGRAM_WEBHOOK_SECRET"]):
        raise HTTPException(403, "Acesso não autorizado")
    try:
        update = await request.json()
        update_id = int(update["update_id"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(400, "Atualização inválida")
    message = update.get("message") or {}
    sender = message.get("from") or {}
    chat = message.get("chat") or {}
    owner_id = int(cfg["ORBITA_OWNER_ID"])
    if (chat.get("type") != "private" or sender.get("is_bot")
            or int(sender.get("id") or 0) != owner_id
            or int(chat.get("id") or 0) != owner_id):
        return {"ok": True, "ignored": True}
    memory = CloudMemory(cfg["SUPABASE_URL"], cfg["SUPABASE_SECRET_KEY"], cfg["ORBITA_USER_UUID"])
    try:
        if not memory.claim_update(update_id):
            state = memory.get_update(update_id)
            if state and state.get("status") == "processed":
                return {"ok": True, "duplicate": True}
            if state and state.get("status") == "replied" and state.get("response"):
                # Resposta ja preparada: NAO repetir /tarefa, /feito ou chamada a IA.
                # Telegram nao fornece chave de idempotencia para sendMessage:
                # a entrega pode ser repetida se o ACK do banco falhar apos o envio.
                telegram_call(cfg["TELEGRAM_BOT_TOKEN"], "sendMessage",
                              {"chat_id": owner_id, "text": state["response"][:3900]},
                              timeout=10)
                memory.finish_update(update_id)
                return {"ok": True, "resumed": True}
            # Claim "received" sem resposta exige investigacao: nao executar
            # novamente comandos que podem modificar a memoria sem deduplicacao.
            return {"ok": True, "pending": True}
        content = message.get("text") or ""
        answer = reply_text(content, owner_id, memory,
                            os.environ.get("OPENAI_API_KEY", "").strip(),
                            os.environ.get("OPENAI_MODEL", "gpt-5-mini"))
        memory.stage_reply(update_id, answer)
        telegram_call(cfg["TELEGRAM_BOT_TOKEN"], "sendMessage",
                      {"chat_id": owner_id, "text": answer[:3900]}, timeout=10)
        memory.finish_update(update_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        LOGGER.error("Falha no webhook (%s)", type(exc).__name__)
        raise HTTPException(503, "Webhook indisponível")
    finally:
        memory.close()
