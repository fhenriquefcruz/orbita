"""ORBITA | Homologação Auth/RLS real com duas contas e sem copiar JWTs.

Executar somente num computador privado:
  python3 quality/run_auth_homologation.py

Usa login normal (POST Auth) para criar duas sessões temporárias e executa
verificações GET-only na API de dados. Não escreve registros, não salva
credenciais, não imprime tokens, e não muda as migrações nem o GitHub.
"""
from __future__ import annotations

import getpass
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPSHandler

from auth_http_rls_probe import (
    PROJECT_REF, PROJECT_URL, GateError, HttpReader, NoRedirects, evaluate_http
)

CONFIRM = "HOMOLOGAR"
MAX_AUTH_RESPONSE = 32768
CONFIG = Path(__file__).resolve().parents[1] / "docs" / "cloud-config.js"
KEY_PATTERN = re.compile(r"""publishableKey\s*:\s*['"](sb_publishable_[A-Za-z0-9_-]+)['"]""")
URL_PATTERN = re.compile(r"""url\s*:\s*['"]([^'"]+)['"]""")


def public_key_from_config(content: str) -> str:
    """Apenas o valor já publicável; nunca permite usar outra instância."""
    url = URL_PATTERN.search(content)
    key = KEY_PATTERN.search(content)
    if not url or url.group(1) != PROJECT_URL or not key:
        raise GateError("Configuração pública não corresponde ao projeto exclusivo ORBITA.")
    return key.group(1)


def sign_in(email: str, password: str, key: str, *, opener=None) -> str:
    """Pede uma sessão Auth legítima; não persiste o access/refresh token."""
    if not email or not password or not key.startswith("sb_publishable_"):
        raise GateError("Credenciais de autenticação não fornecidas.")
    if len(email) > 320 or len(password) > 1024:
        raise GateError("Credenciais fora do limite permitido.")
    body = json.dumps({"email": email, "password": password}).encode("utf-8")
    request = Request(
        PROJECT_URL + "/auth/v1/token?grant_type=password",
        data=body, method="POST",
        headers={
            "apikey": key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cache-Control": "no-store",
            "User-Agent": "orbita-homologacao-auth/1"
        },
    )
    client = opener or build_opener(HTTPSHandler(), NoRedirects())
    try:
        with client.open(request, timeout=12) as response:
            if response.status != 200:
                raise GateError("A autenticação não foi aprovada.")
            raw = response.read(MAX_AUTH_RESPONSE + 1)
    except HTTPError as err:
        # Não imprimir resposta HTTP, email ou tokens.
        raise GateError(
            "Login recusado por Auth; confira conta confirmada e senha."
            if err.code in (400, 401, 403, 422) else "Serviço Auth indisponível."
        ) from None
    except (URLError, TimeoutError, OSError):
        raise GateError("Sem conexão segura com Supabase Auth.") from None
    if len(raw) > MAX_AUTH_RESPONSE:
        raise GateError("Resposta Auth excedeu limite de segurança.")
    try:
        payload = json.loads(raw)
        access_token = payload["access_token"]
        if not isinstance(access_token, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", access_token
        ):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise GateError("O Supabase não retornou token de acesso válido.") from None
    return access_token


def run() -> int:
    print("ORBITA — homologação real de duas sessões Supabase (apenas leitura de dados)")
    print("Projeto exclusivo:", PROJECT_REF)
    print("Nenhum e-mail, senha ou token será exibido nem salvo pelo programa.")
    if input("Digite HOMOLOGAR para iniciar: ").strip() != CONFIRM:
        print("Não executado; nenhuma sessão aberta.")
        return 2
    try:
        key = public_key_from_config(CONFIG.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, GateError):
        print("BLOQUEADO — configuração pública ausente ou inválida.")
        return 2

    try:
        owner_email = input("E-mail da conta titular: ").strip()
        owner_password = getpass.getpass("Senha da conta titular (oculta): ")
        other_email = input("E-mail da conta de teste: ").strip()
        other_password = getpass.getpass("Senha da conta de teste (oculta): ")
        if not owner_email or not other_email or owner_email.casefold() == other_email.casefold():
            raise GateError("São necessárias duas contas de e-mails diferentes.")
        owner_jwt = sign_in(owner_email, owner_password, key)
        other_jwt = sign_in(other_email, other_password, key)
        report = evaluate_http(HttpReader(key), owner_jwt, other_jwt)
    except (GateError, OSError, ValueError, TypeError):
        print("BLOQUEADO — não foi possível concluir login e isolamento HTTP.")
        print("Confira se ambas as contas estão confirmadas e se a API REST está habilitada.")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelado. Nenhum dado de negócio alterado.")
        return 2
    finally:
        # Strings não podem ser apagadas com garantia da memória Python.
        # O processo termina imediatamente após imprimir o resultado.
        pass

    print("PASSOU — duas contas reais diferentes autenticadas pelo servidor.")
    print("PASSOU — registros do titular invisíveis à segunda conta.")
    print("PASSOU — API privada Telegram e visitante anônimo bloqueados.")
    print("PASSOU — token inválido rejeitado pela API Auth.")
    if not report["chat_fixture_exists"]:
        print("PENDENTE — não existe mensagem de chat para demonstrar isolamento real.")
        print("Não criar fixture sem backup e plano de limpeza previamente validados.")
        return 1
    print("PASSOU — mensagens de chat do titular isoladas.")
    print("GATE DE LEITURA CONCLUÍDO. Ainda faltam escrita, logout, recuperação e Safari.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
