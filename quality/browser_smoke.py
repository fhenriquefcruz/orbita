"""Smoke test local (não substitui Safari/iPhone físico)."""
import http.server
import socketserver
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/'docs'
class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args): pass

with socketserver.TCPServer(('127.0.0.1',0),Quiet) as server:
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    url=f'http://127.0.0.1:{server.server_address[1]}/'
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        for width in (320,360,390,428,768,1024,1440,1920):
            page=browser.new_page(viewport={'width':width,'height':844})
            errors=[]
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.goto(url,wait_until='networkidle')
            assert page.title().startswith('ORBITA')
            assert page.locator('#statOpen').inner_text()=='0'
            overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 1')
            assert not overflow,(width,'horizontal overflow',page.evaluate('document.documentElement.scrollWidth'))
            assert not errors,(width,errors)
            # Navegação para dados; mostrar explicitamente integração ainda não configurada.
            if width>=701: page.locator('button[data-view="data"]').first.click()
            else: page.locator('button[data-view="data"]').last.click()
            assert page.locator('#orbitaCloudStatus').inner_text().startswith('Memória central não configurada')
            assert page.locator('#orbitaCloudLogin').is_hidden()
            page.close()
        page=browser.new_page(viewport={'width':390,'height':844})
        page.goto(url,wait_until='networkidle')
        page.locator('[data-add]').first.click()
        page.locator('#fTitle').fill('Testar tarefa ORBITA')
        page.locator('#recordForm button[type="submit"]').click()
        assert page.locator('#statOpen').inner_text()=='1'
        page.reload(wait_until='networkidle')
        assert page.locator('#statOpen').inner_text()=='1'
        print('Browser smoke: 8 viewports sem overflow/JS errors; criação e persistência local OK')
        browser.close()
    server.shutdown()
