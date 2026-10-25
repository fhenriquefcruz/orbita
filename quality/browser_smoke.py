"""Smoke E2E com provedor Auth simulado. Não substitui testes reais de RLS."""
import http.server
import json
import socketserver
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1] / "docs"
ORIGIN = "https://orbita-tests.supabase.co"
OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True


def mock_api(route):
    req = route.request
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
        "Access-Control-Allow-Headers": "authorization, apikey, content-type",
        "Content-Type": "application/json",
    }
    if req.method == "OPTIONS":
        return route.fulfill(status=204, headers=headers)
    path = req.url.split("/auth/v1")[-1]
    if path.startswith("/token?grant_type=password"):
        email = json.loads(req.post_data or "{}").get("email", "")
        owner_id = OTHER if email.startswith("other") else OWNER
        access_token = "test_access_token_other" if owner_id == OTHER else "test_access_token_owner"
        body = {"access_token": access_token,
                "refresh_token": "test_refresh_token", "expires_in": 3600,
                "user": {"id": owner_id, "email": email}}
    elif path == "/user":
        token = req.headers.get("authorization", "")
        if token == "Bearer test_access_token_other":
            body = {"id": OTHER, "email": "other@example.test"}
        elif token == "Bearer test_access_token_owner":
            body = {"id": OWNER, "email": "owner@example.test"}
        else:
            return route.fulfill(status=401, body='{"error":"unauthorized"}', headers=headers)
    elif path.startswith("/logout"):
        body = {}
    else:
        return route.fulfill(status=404, body="{}", headers=headers)
    return route.fulfill(status=200, body=json.dumps(body), headers=headers)



def mock_rest(route):
    req = route.request
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "authorization, apikey, prefer, content-type",
        "Content-Type": "application/json",
        "Content-Range": "0-0/2",
        "Access-Control-Expose-Headers": "Content-Range",
    }
    if req.method == "OPTIONS":
        return route.fulfill(status=204, headers=headers)
    if req.method == "PATCH":
        # Concorrência simulada: servidor alterou a revisão após a leitura.
        query = parse_qs(urlsplit(req.url).query)
        assert query.get("id") == ["eq.tg-1"]
        assert query.get("updated_at") == ["eq.2026-10-24T20:11:00Z"]
        assert req.headers.get("prefer") == "return=representation"
        assert req.headers.get("authorization") == "Bearer test_access_token_owner"
        return route.fulfill(status=200, headers=headers, body="[]")
    assert req.method == "GET", "Consultas não podem gravar registros sem comando explícito"
    assert "/rest/v1/orbita_records?" in req.url
    authorization = req.headers.get("authorization")
    assert authorization in ("Bearer test_access_token_owner", "Bearer test_access_token_other")
    is_other = authorization == "Bearer test_access_token_other"
    query = parse_qs(urlsplit(req.url).query)
    if "payload->>source" in query:
        assert query["payload->>source"] == ["eq.Telegram ORBITA"]
        assert query["limit"] == ["100"]
        assert req.headers.get("prefer") != "count=exact"
        items = [
            {"id": "tg-1", "telegram_seq": 1, "updated_at": "2026-10-24T20:11:00Z",
             "payload": {"id": "tg-1", "source": "Telegram ORBITA",
                         "title": '<img src=x onerror=alert(1)>',
                         "type": "tarefa", "priority": "P1", "status": "a_fazer"}},
            {"id": "tg-2", "telegram_seq": 2, "updated_at": "2026-10-24T20:12:00Z",
             "payload": {"id": "tg-2", "source": "Telegram ORBITA",
                         "title": "Entregar documento", "type": "tarefa",
                         "priority": "P2", "status": "concluida"}},
            {"id": "tg-3", "telegram_seq": 3, "updated_at": "2026-10-24T20:13:00Z",
             "payload": {"id": "tg-3", "source": "Telegram ORBITA",
                         "title": "Ideia de design", "type": "ideia",
                         "priority": "P3", "status": "a_fazer"}},
            {"id": "tg-4", "telegram_seq": 4, "updated_at": "2026-10-24T20:14:00Z",
             "payload": {"id": "tg-4", "source": "Telegram ORBITA",
                         "title": "Reunião de integração", "type": "tarefa",
                         "priority": "P1", "status": "em_andamento"}}
        ]
        return route.fulfill(status=200, headers=headers, body=json.dumps([] if is_other else items))
    if query.get("select") == ["id,payload,updated_at"]:
        assert query["limit"] == ["500"]
        assert req.headers.get("prefer") != "count=exact"
        preview = [] if is_other else [
            {"id": "tg-1", "updated_at": "2026-10-24T20:11:00Z",
             "payload": {"id": "tg-1", "title": "Teste de conciliação",
                         "type": "tarefa", "status": "a_fazer",
                         "updated_at": "2026-10-24T20:11:00Z"}}
        ]
        return route.fulfill(status=200, headers=headers, body=json.dumps(preview))
    assert req.headers.get("prefer") == "count=exact"
    if is_other:
        headers["Content-Range"] = "*/0"
        return route.fulfill(status=200, headers=headers, body="[]")
    return route.fulfill(status=206, headers=headers, body='[{"id":"teste"}]')

with ReusableServer(("127.0.0.1", 0), Quiet) as server:
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width in (320, 360, 390, 428, 768, 1024, 1440, 1920):
            context = browser.new_context(viewport={"width": width, "height": 844})
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(url, wait_until="networkidle")
            assert page.title().startswith("ORBITA")
            assert page.locator("#orbitaAuthRoot").is_visible()
            assert page.locator(".layout").is_hidden()
            # A organização pode estar configurada ou não. O gate de login deve proteger a tela em ambos os casos.
            assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"), width
            assert not errors, (width, errors)
            context.close()

        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.route("**/cloud-config.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript",
            body="window.ORBITA_CLOUD_PUBLIC={url:'" + ORIGIN +
                 "',publishableKey:'sb_publishable_public_test'};"))
        page.route(ORIGIN + "/**", mock_api)
        page.route(ORIGIN + "/rest/v1/**", mock_rest)
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(url + "#/records", wait_until="networkidle")
        assert page.locator(".layout").is_hidden(), "Protected route loaded without auth"
        page.locator("#orbitaAuthEmail").fill("owner@example.test")
        page.locator("#orbitaAuthPassword").fill("strong-password-example")
        page.locator("#orbitaAuthLogin button[type=submit]").click()
        page.locator("#orbitaAuthRoot").wait_for(state="hidden")
        assert page.locator("#view-records").is_visible()
        assert page.locator("#statOpen").inner_text() == "0"
        # Consulta autenticada é de leitura: exibe somente a contagem da nuvem.
        page.wait_for_function(
            "document.querySelector('#orbitaCloudDashboardStatus')?.textContent.includes('2 registro(s) na nuvem')"
        )
        assert page.locator("#orbitaCloudBridge").count() == 1
        # A faixa é exibida na visão geral, não na rota /records.
        page.locator('.mobile-nav button[data-view="home"]').click()
        assert page.locator("#orbitaCloudBridge").is_visible()
        page.locator("#orbitaCloudInspect").click()
        page.wait_for_function(
            "document.querySelector('#orbitaCloudChecked')?.textContent.startsWith('Conferido')"
        )
        page.locator('.mobile-nav button[data-view="data"]').click()
        page.wait_for_function(
            "document.querySelector('#orbitaTelegramStatus')?.textContent.includes('Exibindo 4 de 4')"
        )
        assert page.locator("#orbitaTelegramList li").count() == 4
        assert page.locator("#orbitaTelegramList img").count() == 0, "Título remoto deve ser texto seguro"
        assert page.locator("#orbitaTelegramOpen").inner_text() == "2"
        assert page.locator("#orbitaTelegramDone").inner_text() == "1"
        assert page.locator("#orbitaTelegramIdeas").inner_text() == "1"
        page.locator("#orbitaTelegramFilter").select_option("done")
        assert page.locator("#orbitaTelegramList li").count() == 1
        assert "Entregar documento" in page.locator("#orbitaTelegramList").inner_text()
        page.locator("#orbitaTelegramFilter").select_option("ideas")
        assert page.locator("#orbitaTelegramList li").count() == 1
        assert "Ideia de design" in page.locator("#orbitaTelegramList").inner_text()
        page.locator("#orbitaTelegramFilter").select_option("open")
        assert page.locator("#orbitaTelegramList li").count() == 2
        page.locator("#orbitaTelegramFilter").select_option("all")
        page.locator("#orbitaTelegramSearch").fill("reuniao")
        assert page.locator("#orbitaTelegramList li").count() == 1, "Busca deve ignorar acentos"
        assert "Reunião de integração" in page.locator("#orbitaTelegramList").inner_text()
        page.locator("#orbitaTelegramSearch").fill("inexistente")
        assert "Nenhum item corresponde aos filtros" in page.locator("#orbitaTelegramList").inner_text()
        page.locator("#orbitaTelegramSearch").fill("")
        assert page.locator("#orbitaTelegramList li").count() == 4
        assert page.evaluate(
            "(JSON.parse(localStorage.getItem('orbita_v12_local') || '{}').records || []).length"
        ) == 0, "Consulta não pode importar registros localmente"
        page.locator("#orbitaTelegramRefresh").click()
        page.wait_for_function(
            "document.querySelector('#orbitaTelegramRefresh')?.disabled === false"
        )
        assert page.locator("#orbitaTelegramList li").count() == 4
        page.locator("#orbitaCloudPreview").click()
        page.wait_for_function(
            "document.querySelector('#orbitaCloudPreviewStatus')?.textContent.includes('1 a receber')"
        )
        assert "Ainda não foi gravado nada" in page.locator("#orbitaCloudPreviewStatus").inner_text()
        assert page.evaluate(
            "(JSON.parse(localStorage.getItem('orbita_v12_local') || '{}').records || []).length"
        ) == 0, "Prévia de conciliação não pode salvar dados locais"
        page.locator('.mobile-nav button[data-view="records"]').click()
        assert page.locator("#view-records").is_visible()
        # Validação de scroll horizontal também depois da autenticação.
        for responsive_width in (320,360,390,428,768,1024,1440,1920):
            page.set_viewport_size({"width":responsive_width,"height":844})
            assert not page.evaluate(
                "document.documentElement.scrollWidth > window.innerWidth + 1"
            ), f"Overflow na central autenticada: {responsive_width}"
        page.set_viewport_size({"width":390,"height":844})
        # Alternância visual: tema noturno e persistência local.
        toggle = page.locator("#orbitaThemeToggle")
        assert toggle.count() == 1
        assert page.evaluate("document.documentElement.dataset.orbitaTheme") == "light"
        toggle.click()
        assert page.evaluate("document.documentElement.dataset.orbitaTheme") == "night"
        assert toggle.get_attribute("aria-pressed") == "true"

        page.locator("#view-records [data-add]").click()
        page.locator("#fTitle").fill("Testar tarefa ORBITA")
        page.locator('#recordForm button[type="submit"]').click()
        assert page.locator("#statOpen").inner_text() == "1"
        page.reload(wait_until="networkidle")
        assert page.evaluate("document.documentElement.dataset.orbitaTheme") == "night", "Tema não foi restaurado"
        page.locator("#orbitaAuthRoot").wait_for(state="hidden")
        assert page.locator("#statOpen").inner_text() == "1"
        assert page.locator("#view-records").is_visible(), "Deep link not restored"

        page.locator("#orbitaSignOut").click()
        page.locator("#orbitaAuthRoot").wait_for(state="visible")
        assert page.locator(".layout").is_hidden(), "Protected shell exposed on logout"

        # Mesmo navegador: o vínculo local impede trocar o titular de registros.
        page.locator("#orbitaAuthEmail").fill("other@example.test")
        page.locator("#orbitaAuthPassword").fill("strong-password-example")
        page.locator("#orbitaAuthLogin button[type=submit]").click()
        page.wait_for_function(
            "document.querySelector('#orbitaAuthStatus')?.textContent.includes('outra conta ORBITA')"
        )
        assert page.locator(".layout").is_hidden()
        assert not errors, errors
        context.close()

        # Outra sessão independente: Auth /user precisa devolver a identidade própria.
        # Mock API simula que registros do proprietário NÃO existem nesta conta.
        isolated = browser.new_context(viewport={"width": 390, "height": 844})
        other_page = isolated.new_page()
        other_errors = []
        other_page.on("pageerror", lambda err: other_errors.append(str(err)))
        other_page.route("**/cloud-config.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript",
            body="window.ORBITA_CLOUD_PUBLIC={url:'" + ORIGIN +
                 "',publishableKey:'sb_publishable_public_test'};"))
        other_page.route(ORIGIN + "/**", mock_api)
        other_page.route(ORIGIN + "/rest/v1/**", mock_rest)
        other_page.goto(url + "#/data", wait_until="networkidle")
        other_page.locator("#orbitaAuthEmail").fill("other@example.test")
        other_page.locator("#orbitaAuthPassword").fill("strong-password-example")
        other_page.locator("#orbitaAuthLogin button[type=submit]").click()
        other_page.locator("#orbitaAuthRoot").wait_for(state="hidden")
        assert "other@example.test" in other_page.locator("#orbitaCloudAccount").inner_text()
        other_page.wait_for_function(
            "document.querySelector('#orbitaCloudDashboardStatus')?.textContent.includes('0 registro(s) na nuvem')"
        )
        other_page.wait_for_function(
            "document.querySelector('#orbitaTelegramStatus')?.textContent.includes('Exibindo 0 de 0')"
        )
        assert "Nenhum registro do Telegram nesta conta" in other_page.locator("#orbitaTelegramList").inner_text()
        assert other_page.locator("#orbitaTelegramList .orbita-telegram-empty").count() == 1
        other_page.locator("#orbitaCloudPreview").click()
        other_page.wait_for_function(
            "document.querySelector('#orbitaCloudPreviewStatus')?.textContent.includes('0 a receber')"
        )
        assert other_page.evaluate(
            "(JSON.parse(localStorage.getItem('orbita_v12_local') || '{}').records || []).length"
        ) == 0
        assert not other_errors, other_errors
        isolated.close()

        # Um PATCH concorrente que afeta zero registros deve interromper a conciliação.
        conflict = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        conflict_page = conflict.new_page()
        conflict_errors = []
        conflict_page.on("pageerror", lambda err: conflict_errors.append(str(err)))
        conflict_page.route("**/cloud-config.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript",
            body="window.ORBITA_CLOUD_PUBLIC={url:'" + ORIGIN +
                 "',publishableKey:'sb_publishable_public_test'};"))
        conflict_page.route(ORIGIN + "/**", mock_api)
        conflict_page.route(ORIGIN + "/rest/v1/**", mock_rest)
        conflict_page.goto(url + "#/data", wait_until="networkidle")
        conflict_page.locator("#orbitaAuthEmail").fill("owner@example.test")
        conflict_page.locator("#orbitaAuthPassword").fill("strong-password-example")
        conflict_page.locator("#orbitaAuthLogin button[type=submit]").click()
        conflict_page.locator("#orbitaAuthRoot").wait_for(state="hidden")
        local_item = {"id": "tg-1", "title": "Local mais recente",
                      "type": "tarefa", "updated_at": "2026-10-24T20:12:00Z"}
        conflict_page.evaluate(
            "(item) => localStorage.setItem('orbita_v12_local', JSON.stringify("
            "{schema_version:1,records:[item],audit:[]}))", local_item)
        conflict_page.evaluate("window.confirm = () => true")
        conflict_page.locator("#orbitaCloudSync").click()
        conflict_page.wait_for_function(
            "document.querySelector('#orbitaCloudStatus')?.textContent.includes('Sincronização não concluída')"
        )
        assert "mudou na nuvem" in conflict_page.locator("#orbitaCloudStatus").inner_text()
        assert conflict_page.evaluate(
            "JSON.parse(localStorage.getItem('orbita_v12_local')).records[0].title"
        ) == "Local mais recente", "Falha remota não pode sobrescrever o backup local"
        assert not conflict_errors, conflict_errors
        conflict.close()

        # Importação somente para o navegador: backup confirmado e nenhuma escrita remota.
        pull = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        pull_page = pull.new_page()
        pull_errors = []
        remote_methods = []
        pull_page.on("pageerror", lambda err: pull_errors.append(str(err)))
        pull_page.on("request", lambda req: remote_methods.append(req.method)
                     if "/rest/v1/orbita_records" in req.url else None)
        pull_page.route("**/cloud-config.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript",
            body="window.ORBITA_CLOUD_PUBLIC={url:'" + ORIGIN +
                 "',publishableKey:'sb_publishable_public_test'};"))
        pull_page.route(ORIGIN + "/**", mock_api)
        pull_page.route(ORIGIN + "/rest/v1/**", mock_rest)
        pull_page.goto(url + "#/data", wait_until="networkidle")
        pull_page.locator("#orbitaAuthEmail").fill("owner@example.test")
        pull_page.locator("#orbitaAuthPassword").fill("strong-password-example")
        pull_page.locator("#orbitaAuthLogin button[type=submit]").click()
        pull_page.locator("#orbitaAuthRoot").wait_for(state="hidden")
        pull_page.evaluate("window.confirm = () => true")
        pull_page.locator("#orbitaCloudImport").click()
        pull_page.wait_for_function(
            "(JSON.parse(localStorage.getItem('orbita_v12_local') || '{}').records || []).length === 1"
        )
        assert pull_page.evaluate(
            "JSON.parse(localStorage.getItem('orbita_v12_local')).records[0].id"
        ) == "tg-1", "Importação deve trazer registro da nuvem"
        assert pull_page.evaluate(
            "Object.keys(JSON.parse(localStorage.getItem('orbita_cloud_tombstones_v1') || '{}')).length"
        ) == 0
        assert remote_methods and set(remote_methods) == {"GET"}, remote_methods
        assert not pull_errors, pull_errors
        pull.close()
        print("Browser smoke: Auth, isolamento, importação unidirecional e PATCH concorrente: OK")
        browser.close()
    server.shutdown()
