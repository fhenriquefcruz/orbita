"""ORBITA Aurora 3.24 | Real HTTP/Auth/RLS verification, strictly read-only.

Run manually, outside CI, with two already-authorized Supabase Auth JWTs. No
emails, passwords, refresh tokens, privileged keys or personal data are stored.
This script never performs POST/PATCH/PUT/DELETE or creates Auth users.
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, OpenerDirector, Request, build_opener
)

PROJECT_REF = "tbqfymedgdsdrgkqmuni"
PROJECT_URL = "https://" + PROJECT_REF + ".supabase.co"
RUN_CONFIRMATION = "YES_I_AUTHORIZE_READ_ONLY"
MAX_BYTES = 131072
JWT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")


class GateError(RuntimeError):
    """Only authored, non-secret error messages are ever raised to the CLI."""


@dataclass(frozen=True)
class Response:
    status: int
    data: object


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not forward private Authorization headers to redirects.
        return None


class HttpReader:
    """Minimal fixed-origin GET-only client; does not follow redirects."""

    def __init__(self, key: str, opener: OpenerDirector | None = None):
        if not isinstance(key, str) or not key.startswith("sb_publishable_"):
            raise GateError("Use uma chave publicável do projeto, nunca service_role.")
        self.key = key
        self.opener = opener if opener is not None else build_opener(
            HTTPSHandler(), NoRedirects()
        )

    def get(self, path: str, jwt: str | None = None) -> Response:
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
            raise GateError("Caminho da API inválido.")
        if not (path.startswith("/auth/v1/user") or
                path.startswith("/rest/v1/orbita_records?") or
                path.startswith("/rest/v1/orbita_chat_messages?") or
                path.startswith("/rest/v1/orbita_telegram_updates?")):
            raise GateError("Rota fora da lista de leitura autorizada.")
        if jwt is not None and not JWT_PATTERN.fullmatch(jwt):
            raise GateError("JWT inválido para a verificação.")
        headers = {
            "apikey": self.key, "Accept": "application/json",
            "Cache-Control": "no-store", "User-Agent": "orbita-e2e-readonly/3.24"
        }
        if jwt is not None:
            headers["Authorization"] = "Bearer " + jwt
        url = PROJECT_URL + path
        if urlsplit(url).hostname != PROJECT_REF + ".supabase.co":
            raise GateError("Destino remoto não corresponde ao projeto ORBITA.")
        req = Request(url, headers=headers, method="GET")
        try:
            with self.opener.open(req, timeout=12) as conn:
                status = conn.status
                raw = conn.read(MAX_BYTES + 1)
        except HTTPError as err:
            # Do not render service-provided bodies, which may include data.
            return Response(int(err.code), None)
        except (URLError, TimeoutError, OSError):
            raise GateError("Servidor inacessível ou conexão expirou.") from None
        if len(raw) > MAX_BYTES:
            raise GateError("Resposta inesperadamente grande.")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError):
            raise GateError("Servidor respondeu fora do formato JSON esperado.") from None
        return Response(int(status), value)


def _user_id(transport: HttpReader, token: str) -> str:
    reply = transport.get("/auth/v1/user", token)
    if reply.status != 200 or not isinstance(reply.data, dict):
        raise GateError("Uma das sessões Auth não foi validada pelo servidor.")
    try:
        return str(uuid.UUID(reply.data["id"]))
    except (ValueError, KeyError, TypeError, AttributeError):
        raise GateError("Auth não retornou identidade verificável.") from None


def _rows(transport: HttpReader, route: str, token: str) -> list[dict]:
    reply = transport.get(route, token)
    if reply.status != 200 or not isinstance(reply.data, list):
        raise GateError("Leitura PostgREST não foi autorizada ou retornou erro.")
    if not all(isinstance(row, dict) for row in reply.data):
        raise GateError("Linhas PostgREST inválidas.")
    return reply.data


def _must_deny(transport: HttpReader, route: str, token: str | None) -> None:
    reply = transport.get(route, token)
    if reply.status not in (401, 403):
        raise GateError("Tabela privada aceitou acesso que deveria ser negado.")


def evaluate_http(transport: HttpReader, owner_jwt: str, other_jwt: str) -> dict[str, object]:
    """Only reads schema-backed endpoints; success requires real chat fixture."""
    if not JWT_PATTERN.fullmatch(owner_jwt or "") or not JWT_PATTERN.fullmatch(other_jwt or ""):
        raise GateError("São necessários dois JWTs de usuário válidos.")
    if owner_jwt == other_jwt:
        raise GateError("As sessões não podem usar o mesmo JWT.")

    owner_id = _user_id(transport, owner_jwt)
    other_id = _user_id(transport, other_jwt)
    if owner_id == other_id:
        raise GateError("Auth confirmou duas sessões da mesma conta.")

    params = urlencode({"select": "id,user_id", "user_id": "eq." + owner_id, "limit": "10"})
    owner_records = _rows(transport, "/rest/v1/orbita_records?" + params, owner_jwt)
    if not owner_records or any(row.get("user_id") != owner_id for row in owner_records):
        raise GateError("Conta titular não possui registro verificável no ambiente.")
    crossed_records = _rows(transport, "/rest/v1/orbita_records?" + params, other_jwt)
    if crossed_records:
        raise GateError("Isolamento RLS FALHOU: outra conta enxerga registro do titular.")

    chats = urlencode({"select": "user_id", "user_id": "eq." + owner_id, "limit": "10"})
    owner_chats = _rows(transport, "/rest/v1/orbita_chat_messages?" + chats, owner_jwt)
    if any(row.get("user_id") != owner_id for row in owner_chats):
        raise GateError("Resposta de chat contém dados de outro titular.")
    cross_chats = _rows(transport, "/rest/v1/orbita_chat_messages?" + chats, other_jwt)
    if cross_chats:
        raise GateError("Isolamento RLS FALHOU: outra conta enxerga chat do titular.")

    private = "/rest/v1/orbita_telegram_updates?" + urlencode({
        "select": "update_id", "limit": "1"
    })
    _must_deny(transport, private, owner_jwt)
    _must_deny(transport, private, other_jwt)
    _must_deny(transport, private, None)
    _must_deny(transport, "/rest/v1/orbita_records?select=id&limit=1", None)

    invalid = transport.get("/auth/v1/user", "eyJhbGciOiJub25lIn0.e30.signature_invalid")
    if invalid.status not in (401, 403):
        raise GateError("Endpoint Auth não rejeitou token deliberadamente inválido.")

    return {
        "different_auth_users": True,
        "owner_records_accessible": True,
        "cross_account_records_hidden": True,
        "cross_account_chat_hidden": True,
        "private_telegram_denied": True,
        "anonymous_records_denied": True,
        "invalid_jwt_denied": True,
        "chat_fixture_exists": bool(owner_chats),
        "ready_for_next_gate": bool(owner_chats),
    }


def main(environ: dict[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    if env.get("ORBITA_E2E_HTTP_RUN") != RUN_CONFIRMATION:
        print("NÃO EXECUTADO — verificação manual exige confirmação explícita.")
        return 2
    if env.get("ORBITA_E2E_EXPECT_PROJECT") != PROJECT_REF:
        print("NÃO EXECUTADO — confirme o projeto Supabase exclusivo ORBITA.")
        return 2
    tokens = (env.get("ORBITA_E2E_OWNER_JWT", ""),
              env.get("ORBITA_E2E_OTHER_JWT", ""))
    key = env.get("ORBITA_E2E_PUBLISHABLE_KEY", "")
    if not key.startswith("sb_publishable_") or any(not t for t in tokens):
        print("NÃO EXECUTADO — dois JWTs e chave publicável são necessários.")
        return 2
    try:
        report = evaluate_http(HttpReader(key), *tokens)
    except (GateError, ValueError, TypeError):
        # Deliberately never prints request path, response bodies, JWTs or key.
        print("BLOQUEADO — falha em identidade, permissão ou rede; sem alterações.")
        return 1
    print("PASSOU — duas identidades Auth verificadas e registros isolados por HTTP.")
    print("PASSOU — filas privadas e acesso anônimo bloqueados.")
    if report["chat_fixture_exists"]:
        print("PASSOU — chat do titular existente e isolado por HTTP.")
        print("AVISO — ainda faltam provas de escrita, recuperação e Safari real.")
        return 0
    print("PENDENTE — não há mensagem do titular para comprovar isolamento do chat.")
    print("Nenhum dado foi modificado. O teste completo não foi homologado.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
