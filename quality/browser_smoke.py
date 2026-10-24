"""Smoke E2E com provedor Auth simulado. Não substitui testes reais de RLS."""
import http.server
import json
import socketserver
import threading
from pathlib import Path
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
        body = {"access_token": "test_access_token",
                "refresh_token": "test_refresh_token", "expires_in": 3600,
                "user": {"id": owner_id, "email": email}}
    elif path == "/user":
        body = {"id": OWNER, "email": "owner@example.test"}
    elif path.startswith("/logout"):
        body = {}
    else:
        return route.fulfill(status=404, body="{}", headers=headers)
    return route.fulfill(status=200, body=json.dumps(body), headers=headers)


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
        assert not errors, errors
        context.close()
        print("Browser smoke: 8 viewports, auth gate, login, protected route, reload, logout: OK")
        browser.close()
    server.shutdown()
