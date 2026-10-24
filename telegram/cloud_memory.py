"""Memória Telegram que usa a mesma fonte de verdade do painel: Supabase PostgREST.

Chaves `sb_secret_...` são exclusivas do servidor. A classe exige um UUID
explícito do usuário dono; o bot verifica separadamente o Telegram ID.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

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
        if table not in ("orbita_records", "orbita_chat_messages", "orbita_telegram_updates"):
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
        rows = self._call("orbita_records", query={
            "select": "id,payload", "user_id": "eq." + self.user_id,
            "telegram_seq": "eq." + str(int(record_id)), "limit": "1",
        })
        if not rows:
            return False
        item = rows[0]
        p = item["payload"]
        if p.get("type") != "tarefa" or p.get("status") in ("concluida", "cancelada", "arquivada"):
            return False
        p["status"] = "concluida"
        p["updated_at"] = datetime.now(TZ).isoformat(timespec="seconds")
        p["completed_at"] = p["updated_at"]
        self._call("orbita_records", "PATCH", query={
            "id": "eq." + item["id"], "user_id": "eq." + self.user_id,
        }, value={"payload": p, "updated_at": p["updated_at"]}, prefer="return=minimal")
        return True

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
        self._call("orbita_telegram_updates", "PATCH", query={
            "update_id": "eq." + str(int(update_id)), "user_id": "eq." + self.user_id,
        }, value={"status": "processed", "response": answer[:4000]}, prefer="return=minimal")

    def get_update(self, update_id: int):
        rows = self._call("orbita_telegram_updates", query={
            "select": "status,response", "user_id": "eq." + self.user_id,
            "update_id": "eq." + str(int(update_id)), "limit": "1",
        })
        return rows[0] if rows else None

    def close(self):
        pass
