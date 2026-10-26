"""ORBITA Aurora 3.27 — optional HTTP-only RLS chat fixture, on the user's PC.

Deliberately not run in CI. With EXPLICIT opt-in, signs in both existing
users, inserts one synthetic chat row as the owner, checks that the second
user cannot read or delete it, and finally deletes that exact row as owner.
It does not change schema, real messages, users, or Telegram settings.

Because HTTP spans multiple transactions, process/network failure may leave
a temporary row behind. Cleanup is verified; do not claim a PASS otherwise.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import secrets
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from auth_dual_login_runner import password_login
from auth_http_rls_probe import (
    GateError, HttpReader, PROJECT_REF, PROJECT_URL, Response,
    _rows, _user_id, evaluate_http
)

ACK = "I_AUTHORIZE_ONE_TEMPORARY_CHAT_MESSAGE"
FIXTURE_PREFIX = "ORBITA_RLS_FIXTURE_"
REST = "/rest/v1/orbita_chat_messages"
MAX_BYTES = 131072


def mutate(reader: HttpReader, method: str, owner_jwt: str, *,
           owner_id: str, marker: str) -> Response:
    """A narrow write interface; never takes arbitrary tables or destinations."""
    if method not in ("POST", "DELETE"):
        raise GateError("Operação HTTP não autorizada.")
    if not re.fullmatch(r"ORBITA_RLS_FIXTURE_[0-9a-f]{32}", marker):
        raise GateError("Identificador de teste inválido.")
    # The owner id was previously obtained from /auth/v1/user.
    from uuid import UUID
    try:
        owner_id = str(UUID(owner_id))
    except (TypeError, ValueError, AttributeError):
        raise GateError("Titular inválido.") from None

    path = REST
    payload = None
    if method == "POST":
        payload = json.dumps({
            "user_id": owner_id, "role": "user", "content": marker
        }).encode("utf-8")
    else:
        path += "?" + urlencode({
            "user_id": "eq." + owner_id, "content": "eq." + marker
        })
    request = Request(
        PROJECT_URL + path,
        data=payload,
        method=method,
        headers={
            "apikey": reader.key,
            "Authorization": "Bearer " + owner_jwt,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation",
            "Cache-Control": "no-store",
            "User-Agent": "orbita-e2e-ephemeral-chat/3.27",
        },
    )
    try:
        with reader.opener.open(request, timeout=12) as response:
            status = int(response.status)
            body = response.read(MAX_BYTES + 1)
    except HTTPError as error:
        return Response(int(error.code), None)
    except (URLError, TimeoutError, OSError):
        raise GateError("Conexão indisponível durante o teste do chat.") from None
    if len(body) > MAX_BYTES:
        raise GateError("Resposta HTTP inesperadamente grande.") 
    try:
        data = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise GateError("Resposta HTTP não é um JSON válido.") from None
    return Response(status, data)


def fixture_path(owner_id: str, marker: str, fields="id,user_id") -> str:
    return REST + "?" + urlencode({
        "select": fields,
        "user_id": "eq." + owner_id,
        "content": "eq." + marker,
        "limit": "2",
    })


def cleanup(reader: HttpReader, owner_jwt: str, owner_id: str,
            marker: str) -> bool:
    """Fail closed: verify row absent after owner-scoped deletion attempt."""
    try:
        path = fixture_path(owner_id, marker)
        before = _rows(reader, path, owner_jwt)
        if len(before) > 1:
            return False
        if before:
            resp = mutate(reader, "DELETE", owner_jwt,
                          owner_id=owner_id, marker=marker)
            if resp.status not in (200, 204) or not isinstance(resp.data, list):
                return False
            if len(resp.data) != 1:
                return False
        return _rows(reader, path, owner_jwt) == []
    except (GateError, ValueError, TypeError):
        return False


def evaluate_fixture(reader: HttpReader, owner_token: str, other_token: str,
                     *, marker: str | None = None) -> dict[str, bool]:
    # Read-only checks first: fail before any write if identity or permissions
    # are not already correct. Existing owner chat means no fixture needed.
    base = evaluate_http(reader, owner_token, other_token)
    if base["ready_for_next_gate"]:
        return {"chat_isolated": True, "write_tested": False,
                "cleanup_verified": True, "fixture_created": False}
    owner_id = _user_id(reader, owner_token)
    other_id = _user_id(reader, other_token)
    if owner_id == other_id:
        raise GateError("Uma mesma identidade não prova isolamento.")

    marker = marker or FIXTURE_PREFIX + secrets.token_hex(16)
    posted = False
    passed = False
    clean = False
    try:
        posted = True  # even a lost response may have committed the POST
        created = mutate(reader, "POST", owner_token,
                         owner_id=owner_id, marker=marker)
        if created.status != 201 or not isinstance(created.data, list) or (
            len(created.data) != 1
        ):
            raise GateError("Não foi possível comprovar criação da linha temporária.")
        created_row = created.data[0]
        if not isinstance(created_row, dict) or (
            created_row.get("user_id") != owner_id or
            created_row.get("content") != marker or
            not isinstance(created_row.get("id"), int)
        ):
            raise GateError("Resposta de criação do teste não é verificável.")

        scope = fixture_path(owner_id, marker)
        own_rows = _rows(reader, scope, owner_token)
        if len(own_rows) != 1 or own_rows[0].get("id") != created_row["id"]:
            raise GateError("A conta principal não recuperou seu próprio chat de teste.")
        if _rows(reader, scope, other_token):
            raise GateError("VAZAMENTO: a segunda conta conseguiu ler o chat.")
        other_delete = mutate(reader, "DELETE", other_token,
                              owner_id=owner_id, marker=marker)
        if other_delete.status not in (200, 204) or other_delete.data != []:
            raise GateError("VAZAMENTO: a segunda conta conseguiu excluir o chat.")
        if len(_rows(reader, scope, owner_token)) != 1:
            raise GateError("O chat desapareceu após ação da segunda conta.")

        # All original Auth/RLS gates, now with a real committed chat row.
        verdict = evaluate_http(reader, owner_token, other_token)
        if not verdict["ready_for_next_gate"]:
            raise GateError("Leitura cruzada HTTP não passou com o chat temporário.")
        passed = True
    finally:
        if posted:
            clean = cleanup(reader, owner_token, owner_id, marker)
        # No print of passwords, tokens, user ids or private payload.
        if not clean:
            raise GateError("LIMPEZA NÃO CONFIRMADA: verifique fixture temporária no Supabase.")

    return {"chat_isolated": passed, "write_tested": True,
            "cleanup_verified": clean, "fixture_created": True}


def main(env=None) -> int:
    env = os.environ if env is None else env
    if (env.get("ORBITA_CHAT_FIXTURE_ACK") != ACK or
            env.get("ORBITA_E2E_EXPECT_PROJECT") != PROJECT_REF):
        print("NÃO EXECUTADO — requer autorização explícita de uma mensagem temporária.")
        return 2
    try:
        reader = HttpReader(env.get("ORBITA_E2E_PUBLISHABLE_KEY", ""))
        print("O teste pode criar UMA mensagem sintética e excluir após a prova.")
        print("Se a conexão falhar, poderá ser necessária limpeza manual.")
        main_email = input("E-mail principal: ").strip()
        main_password = getpass.getpass("Senha principal: ")
        main_token = password_login(reader, main_email, main_password)
        del main_password
        test_email = input("E-mail da segunda conta: ").strip()
        test_password = getpass.getpass("Senha da segunda conta: ")
        test_token = password_login(reader, test_email, test_password)
        del test_password
        report = evaluate_fixture(reader, main_token, test_token)
        del main_token, test_token
    except (GateError, ValueError, TypeError, EOFError, KeyboardInterrupt):
        print("BLOQUEADO — verificação/limpeza não concluída. Confira o banco.")
        return 1

    if not report["chat_isolated"] or not report["cleanup_verified"]:
        print("BLOQUEADO — chat/limpeza não comprovados.")
        return 1
    if report["fixture_created"]:
        print("PASSOU — chat HTTP isolado entre duas contas; fixture excluída.")
        print("PASSOU — tentativa de excluir o chat alheio negada pela RLS.")
    else:
        print("PASSOU — chat real já presente e isolado; nenhuma linha criada.")
    print("AVISO — backup restaurado e migrações 002/003 continuam pendentes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
