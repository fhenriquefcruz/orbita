"""Memória Telegram que usa a mesma fonte de verdade do painel: Supabase PostgREST.

Chaves `sb_secret_...` são exclusivas do servidor. A classe exige um UUID
explícito do usuário dono; o bot verifica separadamente o Telegram ID.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from action_proposals import check_proposal, CODE_RE

TZ = ZoneInfo("America/Campo_Grande")
ALLOWED_KINDS = {"tarefa": "tarefa", "ideia": "ideia"}


class CloudMemory:
    def __init__(self, url: str, secret: str, user_id: str):
        if not re.fullmatch(r"https://[A-Za-z0-9-]+\.supabase\.co/?", url):
            raise ValueError("SUPABASE_URL deve ser HTTPS e apontar para o projeto Supabase")
        if not secret or secret.startswith("COLE_"):
            raise ValueError("SUPABASE_SECRET_KEY indisponível")
        self.user_id = str(uuid.UUID(user_id))
        self.url = url.rstrip("/")
        self.secret = secret

    def _call(self, table: str, method="GET", query=None, value=None, prefer="return=representation"):
        if table not in ("orbita_records", "orbita_chat_messages", "orbita_telegram_updates",
                         "orbita_action_proposals", "rpc/orbita_confirm_action_proposal"):
            raise ValueError("tabela não permitida")
        suffix = "?" + urlencode(query, doseq=True, safe=".,():*") if query else ""
        data = None if value is None else json.dumps(value, ensure_ascii=False).encode("utf-8")
        headers = {
            "apikey": self.secret,  # sb_secret_ não é JWT e não deve ir em Authorization
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": prefer,
            "User-Agent": "orbita-server/3.0",
        }
        req = Request(self.url + "/rest/v1/" + table + suffix, data=data, headers=headers, method=method)
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else []

    def add(self, owner_id: int, kind: str, title: str, priority="P2") -> int:
        if kind not in ALLOWED_KINDS or priority not in {"P0", "P1", "P2", "P3"}:
            raise ValueError("tipo ou prioridade inválidos")
        title = title.strip()[:1000]
        if not title:
            raise ValueError("título vazio")
        now = datetime.now(TZ).isoformat(timespec="seconds")
        payload = {
            "id": "tg-" + uuid.uuid4().hex, "type": kind, "title": title,
            "context": "criatividade" if kind == "ideia" else "pessoal",
            "priority": priority, "status": "a_fazer", "source": "Telegram ORBITA",
            "certainty": "confirmado", "sensitivity": "pessoal", "notify_mode": "summary",
            "owner": "Gusttavo Lima" if kind == "ideia" else "Zezé",
            "created_at": now, "updated_at": now,
        }
        row = self._call("orbita_records", "POST", value={
            "id": payload["id"], "user_id": self.user_id, "payload": payload,
            "created_at": now, "updated_at": now,
        })
        return int(row[0]["telegram_seq"])

    def create_proposal(self, owner_id: int, kind: str, title: str,
                        priority: str, code: str) -> None:
        check_proposal(kind, title, priority, code)
        response = self._call("orbita_action_proposals", "POST", value={
            "code": code, "user_id": self.user_id, "telegram_id": int(owner_id),
            "kind": kind, "title": title, "priority": priority
        }, prefer="return=representation")
        if not isinstance(response, list) or len(response) != 1 or response[0].get("code") != code:
            raise RuntimeError("Não foi possível guardar a proposta para confirmação")

    def confirm_proposal(self, owner_id: int, code: str) -> tuple[str, int | None]:
        if not CODE_RE.fullmatch(code or ""):
            return "missing", None
        response = self._call("rpc/orbita_confirm_action_proposal", "POST", value={
            "p_code": code, "p_user_id": self.user_id,
            "p_telegram_id": int(owner_id)
        }, prefer="return=representation")
        if not isinstance(response, list) or len(response) != 1:
            raise RuntimeError("Confirmação remota sem resultado verificável")
        result = response[0]
        status = result.get("outcome")
        if status not in {"missing", "already", "saved", "cancelled", "expired"}:
            raise RuntimeError("Resultado de confirmação remoto desconhecido")
        number = result.get("record_number")
        if status in {"saved", "already"} and (not isinstance(number, int) or number < 1):
            raise RuntimeError("Resultado remoto sem identificador válido")
        return status, number if status in {"saved", "already"} else None

    def cancel_proposal(self, owner_id: int, code: str) -> bool:
        if not CODE_RE.fullmatch(code or ""):
            return False
        result = self._call("orbita_action_proposals", "PATCH", query={
            "code": "eq." + code, "user_id": "eq." + self.user_id,
            "telegram_id": "eq." + str(int(owner_id)), "status": "eq.pending"
        }, value={"status": "cancelled"}, prefer="return=representation")
        return (isinstance(result, list) and len(result) == 1
                and result[0].get("code") == code)

    def list(self, owner_id: int, kind=None, limit=30) -> list[dict]:
        result = self._call("orbita_records", query={
            "select": "telegram_seq,payload", "user_id": "eq." + self.user_id,
            "order": "updated_at.desc", "limit": str(min(max(limit, 1), 200)),
        })
        rows = []
        for entry in result:
            p = entry["payload"]
            if kind and p.get("type") != kind:
                continue
            rows.append({"id": entry["telegram_seq"], "kind": p.get("type"), "title": p.get("title", ""),
                         "priority": p.get("priority", "P2"), "status": p.get("status", "a_fazer"),
                         "created_at": p.get("created_at", "")})
        return sorted(rows, key=lambda r: (r["priority"], -int(r["id"])))[:limit]

    def complete(self, owner_id: int, record_id: int) -> bool:
        """Conclui uma tarefa apenas se a revisão remota continuar inalterada.

        Telegram e painel podem editar a mesma linha. Um PATCH condicional sobre
        updated_at impede confirmar uma gravação que afete zero registros.
        """
        rows = self._call("orbita_records", query={
            "select": "id,payload,updated_at", "user_id": "eq." + self.user_id,
            "telegram_seq": "eq." + str(int(record_id)), "limit": "1",
        })
        if len(rows) != 1 or not isinstance(rows[0], dict):
            return False
        item = rows[0]
        payload = item.get("payload")
        row_id = item.get("id")
        revision = item.get("updated_at")
        if not isinstance(payload, dict) or not isinstance(row_id, str) or not row_id:
            return False
        if payload.get("type") != "tarefa" or payload.get("status") in (
            "concluida", "cancelada", "arquivada"
        ):
            return False
        # Versão ausente/ilegível: não escrever sem a guarda de concorrência.
        if not isinstance(revision, str) or not revision:
            return False
        try:
            previous = datetime.fromisoformat(revision.replace("Z", "+00:00"))
        except ValueError:
            return False
        if previous.tzinfo is None or previous.utcoffset() is None:
            return False

        # Microssegundos evitam reutilizar a mesma revisão em ações rápidas.
        now = datetime.now(TZ)
        if now <= previous:
            now = (previous + timedelta(microseconds=1)).astimezone(TZ)
        timestamp = now.isoformat(timespec="microseconds")
        updated = {
            **payload,
            "status": "concluida",
            "updated_at": timestamp,
            "completed_at": timestamp,
        }
        changed = self._call("orbita_records", "PATCH", query={
            "id": "eq." + row_id,
            "user_id": "eq." + self.user_id,
            "updated_at": "eq." + revision,
        }, value={"payload": updated, "updated_at": timestamp},
            prefer="return=representation")
        # Se uma outra origem mudou a revisão, PostgREST responde [].
        # Não afirmar sucesso sem a linha efetivamente retornada.
        return (isinstance(changed, list) and len(changed) == 1
                and isinstance(changed[0], dict)
                and changed[0].get("id") == row_id)

    def save_message(self, owner_id: int, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("role inválido")
        self._call("orbita_chat_messages", "POST", value={
            "user_id": self.user_id, "role": role, "content": content[:6000],
        }, prefer="return=minimal")

    def history(self, owner_id: int, n=10) -> list[dict]:
        rows = self._call("orbita_chat_messages", query={
            "select": "role,content", "user_id": "eq." + self.user_id,
            "order": "id.desc", "limit": str(min(max(n, 1), 100)),
        })
        return list(reversed(rows))

    def clear_history(self, owner_id: int) -> None:
        self._call("orbita_chat_messages", "DELETE", query={
            "user_id": "eq." + self.user_id,
        }, prefer="return=minimal")


    def claim_update(self, update_id: int) -> bool:
        """Retorna True somente no primeiro processamento deste update do Telegram."""
        rows = self._call("orbita_telegram_updates", "POST",
            query={"on_conflict": "update_id"},
            value={"update_id": int(update_id), "user_id": self.user_id},
            prefer="resolution=ignore-duplicates,return=representation")
        return bool(rows)

    def finish_update(self, update_id: int, answer: str) -> None:
        """Guarda resposta antes de enviar. Falha fechada se não houver linha alterada."""
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Resposta vazia não pode ser marcada como processada")
        rows = self._call("orbita_telegram_updates", "PATCH", query={
            "update_id": "eq." + str(int(update_id)), "user_id": "eq." + self.user_id,
            "status": "eq.received",
        }, value={"status": "processed", "response": answer[:4000]},
            prefer="return=representation")
        if (not isinstance(rows, list) or len(rows) != 1 or
                rows[0].get("update_id") != int(update_id) or
                rows[0].get("status") != "processed"):
            raise RuntimeError("Resposta não foi persistida na fila Telegram")

    def mark_delivered(self, update_id: int) -> bool:
        """Marca entrega após sendMessage retornar sucesso (somente schema v3.20)."""
        rows = self._call("orbita_telegram_updates", "PATCH", query={
            "update_id": "eq." + str(int(update_id)), "user_id": "eq." + self.user_id,
            "status": "eq.processed",
        }, value={"status": "delivered"}, prefer="return=representation")
        return (isinstance(rows, list) and len(rows) == 1 and
                rows[0].get("update_id") == int(update_id) and
                rows[0].get("status") == "delivered")

    def get_update(self, update_id: int):
        rows = self._call("orbita_telegram_updates", query={
            "select": "status,response", "user_id": "eq." + self.user_id,
            "update_id": "eq." + str(int(update_id)), "limit": "1",
        })
        return rows[0] if rows else None

    def close(self):
        pass
