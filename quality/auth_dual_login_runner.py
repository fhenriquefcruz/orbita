"""Interactive, local-only real Auth login + HTTP RLS check for ORBITA.

Passwords are typed through getpass, kept in process memory and sent ONLY to
the project's Supabase Auth HTTPS endpoint. Tokens and password are NEVER
printed, persisted, added to command line arguments, or given to ChatGPT.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request

from auth_http_rls_probe import (
    GateError, HttpReader, PROJECT_REF, PROJECT_URL, RUN_CONFIRMATION,
    NoRedirects, evaluate_http
)

LOGIN_ACK = "I_AUTHORIZE_TWO_LOCAL_AUTH_LOGINS"
MAX_AUTH_BYTES = 131072


def password_login(transport: HttpReader, email: str, password: str) -> str:
    if (not isinstance(email, str) or len(email) > 254 or
            not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)):
        raise GateError("Endereço de login inválido.")
    if not isinstance(password, str) or not password:
        raise GateError("Senha de login ausente.")
    url = PROJECT_URL + "/auth/v1/token?grant_type=password"
    body = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = Request(url, data=body, method="POST", headers={
        "apikey": transport.key, "Content-Type": "application/json",
        "Accept": "application/json", "Cache-Control": "no-store",
        "User-Agent": "orbita-auth-private-e2e/3.25",
    })
    try:
        with transport.opener.open(req, timeout=12) as response:
            if response.status != 200:
                raise GateError("Supabase Auth não autenticou uma das contas.")
            raw = response.read(MAX_AUTH_BYTES + 1)
    except HTTPError:
        raise GateError("Credenciais não autenticadas no Supabase Auth.") from None
    except (URLError, TimeoutError, OSError):
        raise GateError("Sem conexão segura com Supabase Auth.") from None
    if len(raw) > MAX_AUTH_BYTES:
        raise GateError("Resposta de Auth acima do limite esperado.")
    try:
        data = json.loads(raw.decode("utf-8"))
        token = data["access_token"]
        if not isinstance(token, str) or not token:
            raise ValueError()
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise GateError("Supabase Auth não retornou access_token válido.") from None
    # Refresh token is intentionally never returned or saved.
    return token


def main(env: dict[str, str] | None = None) -> int:
    env = os.environ if env is None else env
    if (env.get("ORBITA_E2E_LOGIN_ACK") != LOGIN_ACK or
            env.get("ORBITA_E2E_EXPECT_PROJECT") != PROJECT_REF):
        print("NÃO EXECUTADO — é necessário autorizar dois logins locais no projeto ORBITA.")
        return 2
    public_key = env.get("ORBITA_E2E_PUBLISHABLE_KEY", "")
    try:
        reader = HttpReader(public_key)
        print("ORBITA — duas contas de teste previamente autorizadas.")
        print("Nenhum token ou senha será impresso ou salvo.")
        owner_email = input("E-mail da conta proprietária: ").strip()
        owner_pass = getpass.getpass("Senha da conta proprietária: ")
        owner_token = password_login(reader, owner_email, owner_pass)
        del owner_pass
        test_email = input("E-mail da conta de teste: ").strip()
        test_pass = getpass.getpass("Senha da conta de teste: ")
        test_token = password_login(reader, test_email, test_pass)
        del test_pass
        report = evaluate_http(reader, owner_token, test_token)
        del owner_token, test_token
    except (GateError, ValueError, TypeError, EOFError, KeyboardInterrupt):
        print("BLOQUEADO — login ou isolamento não comprovado; nenhum registro foi alterado.")
        return 1
    if not report["ready_for_next_gate"]:
        print("PENDENTE — Auth e isolamento de registros passaram, mas faltam mensagens")
        print("reais da conta titular para provar o isolamento do chat.")
        return 1
    print("PASSOU — duas sessões Auth independentes e leituras RLS verificadas por HTTP.")
    print("ATENÇÃO — não prova escrita, restore de backup nem autorização para produção.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
