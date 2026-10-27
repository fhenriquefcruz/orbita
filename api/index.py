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
from proposal_transport import inline_keyboard, callback_as_confirmation  # noqa: E402
from action_proposals import classify_action  # noqa: E402

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
    callback = update.get("callback_query") or {}
    message = (callback.get("message") if callback else update.get("message")) or {}
    sender = (callback.get("from") if callback else message.get("from")) or {}
    chat = message.get("chat") or {}
    owner_id = int(cfg["ORBITA_OWNER_ID"])
    if (chat.get("type") != "private" or sender.get("is_bot")
            or int(sender.get("id") or 0) != owner_id
            or int(chat.get("id") or 0) != owner_id):
        return {"ok": True, "ignored": True}
    # Callback metadata é input não confiável, nunca autorização independente.
    content = (callback_as_confirmation(callback.get("data")) if callback
               else (message.get("text") or ""))
    if callback and not content:
        return {"ok": True, "ignored": True}
    memory = CloudMemory(cfg["SUPABASE_URL"], cfg["SUPABASE_SECRET_KEY"], cfg["ORBITA_USER_UUID"])
    # Ativar SOMENTE após homologar infra/supabase/003_telegram_delivery.sql.
    # No modo legado, mantém-se o comportamento anterior sem usar 'delivered'.
    verified_delivery = os.environ.get("ORBITA_WEBHOOK_DELIVERY_V2_ENABLED") == "1"
    try:
        replay = False
        legacy_queued = False
        if not memory.claim_update(update_id):
            state = memory.get_update(update_id)
            if state and state.get("status") == "delivered":
                return {"ok": True, "duplicate": True}
            if state and state.get("status") == "processed":
                if not verified_delivery:
                    return {"ok": True, "duplicate": True}
                # V2 consegue reencaminhar resposta salva sem reexecutar a tarefa.
                answer = state.get("response")
                if not isinstance(answer, str) or not answer.strip():
                    return {"ok": True, "pending": True}
                replay = True
            elif state and state.get("status") == "replied":
                # Estado legado ja usado por main: nunca recriar a acao.
                # E necessario concluir o ACK replied->processed apos enviar.
                answer = state.get("response")
                if not isinstance(answer, str) or not answer.strip():
                    return {"ok": True, "pending": True}
                replay = True
                legacy_queued = True
            else:
                # received sem resposta pode representar execucao em andamento.
                # Reprocessar comandos aqui poderia criar tarefas duplicadas.
                return {"ok": True, "pending": True}
        else:
            answer = reply_text(content, owner_id, memory,
                                os.environ.get("OPENAI_API_KEY", "").strip(),
                                os.environ.get("OPENAI_MODEL", "gpt-5-mini"))
            if verified_delivery:
                # V2 armazena response em processed; delivered apos envio.
                memory.finish_update(update_id, answer)
            else:
                # Modo atual/legado: grava replied antes de qualquer envio.
                memory.stage_reply(update_id, answer)
                legacy_queued = True
        payload = {"chat_id": owner_id, "text": answer[:3900]}
        buttons = inline_keyboard(answer) if not callback and classify_action(content) else None
        if buttons:
            payload["reply_markup"] = buttons
        # Se sendMessage falhar, o Telegram repetirá o update. Com v2 ativo,
        # recuperamos a resposta salva sem recriar a tarefa.
        telegram_call(cfg["TELEGRAM_BOT_TOKEN"], "sendMessage", payload, timeout=10)
        # Se falhar, o update fica como replied (legado) ou processed (V2)
        # com response salva, permitindo retry sem repetir a acao original.
        if legacy_queued:
            memory.confirm_legacy_sent(update_id)
        if verified_delivery and not memory.mark_delivered(update_id):
            # Falha do ACK apos sendMessage pode duplicar resposta no retry.
            # Nunca prometer exactly-once, mas nao reexecutar a tarefa.
            raise RuntimeError("Falha ao confirmar estado de entrega do Telegram")
        if callback.get("id"):
            try:
                telegram_call(cfg["TELEGRAM_BOT_TOKEN"], "answerCallbackQuery",
                              {"callback_query_id": callback["id"]}, timeout=10)
            except Exception as exc:
                LOGGER.warning("Falha ao reconhecer botão Telegram (%s)", type(exc).__name__)
        return ({"ok": True, "resumed": True} if replay and legacy_queued and not verified_delivery
                else {"ok": True, "replayed": True} if replay else {"ok": True})
    except HTTPException:
        raise
    except Exception as exc:
        LOGGER.error("Falha no webhook (%s)", type(exc).__name__)
        raise HTTPException(503, "Webhook indisponível")
    finally:
        memory.close()
