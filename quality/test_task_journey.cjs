/* Jornada isolada: Auth e Data API simuladas, sem acesso ao Supabase real. */
const assert = require('node:assert/strict');
const {existsSync} = require('node:fs');
const fs = require('node:fs/promises');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require('playwright');

const docs = path.resolve(__dirname, '../docs');
const owner = '11111111-1111-4111-8111-111111111111';
const cloud = 'https://orbita-tests.supabase.co';
const mime = {'.html':'text/html', '.js':'application/javascript', '.css':'text/css',
  '.svg':'image/svg+xml', '.webmanifest':'application/manifest+json'};

async function main() {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      const file = path.resolve(docs, '.' + (pathname === '/' ? '/index.html' : pathname));
      if (!file.startsWith(docs + path.sep)) throw Error('invalid path');
      const body = await fs.readFile(file);
      res.writeHead(200, {'Content-Type': mime[path.extname(file)] || 'application/octet-stream'});
      res.end(body);
    } catch (_) { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    const bundledChrome = chromium.executablePath();
    const chromePath = process.env.ORBITA_TEST_CHROME || (existsSync(bundledChrome)
      ? bundledChrome : 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe');
    browser = await chromium.launch({headless:true,executablePath:chromePath});
    const context = await browser.newContext({viewport:{width:390,height:844}});
    const page = await context.newPage();
    const errors = [], remoteMethods = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.route('**/cloud-config.js', route => route.fulfill({status:200,
      contentType:'application/javascript', body:`window.ORBITA_CLOUD_PUBLIC={url:'${cloud}',publishableKey:'sb_publishable_public_test'};`}));
    await page.route(cloud + '/**', async route => {
      const req = route.request(), url = new URL(req.url());
      const headers = {'access-control-allow-origin':'*',
        'access-control-allow-methods':'GET,POST,OPTIONS',
        'access-control-allow-headers':'authorization,apikey,prefer,content-type',
        'access-control-expose-headers':'content-range',
        'content-type':'application/json'};
      if (req.method() === 'OPTIONS') return route.fulfill({status:204,headers});
      if (url.pathname === '/auth/v1/token') return route.fulfill({status:200,headers,
        body:JSON.stringify({access_token:'test_access_token_owner',refresh_token:'test_refresh_token',
          expires_in:3600,user:{id:owner,email:'owner@example.test'}})});
      if (url.pathname === '/auth/v1/user') return route.fulfill({status:200,headers,
        body:JSON.stringify({id:owner,email:'owner@example.test'})});
      if (url.pathname.startsWith('/rest/v1/')) {
        remoteMethods.push(req.method());
        assert.equal(req.method(), 'GET', 'Consulta e simulação devem ser somente leitura');
        assert.equal(req.headers().authorization, 'Bearer test_access_token_owner');
        if (url.searchParams.get('select') === 'id,payload,updated_at')
          return route.fulfill({status:200,headers,body:JSON.stringify([{
            id:'cloud-1',updated_at:'2026-10-24T20:11:00Z',payload:{
              id:'cloud-1',title:'Registro remoto',type:'tarefa',status:'a_fazer',
              priority:'P2',source:'Telegram ORBITA',updated_at:'2026-10-24T20:11:00Z'}}])});
        if (url.searchParams.has('payload->>source'))
          return route.fulfill({status:200,headers,body:'[]'});
        return route.fulfill({status:206,headers:{...headers,'content-range':'0-0/1'},body:'[{"id":"cloud-1"}]'});
      }
      return route.fulfill({status:404,headers,body:'{}'});
    });

    const url = `http://127.0.0.1:${server.address().port}/`;
    await page.goto(url + '#/records', {waitUntil:'networkidle'});
    assert.equal(await page.locator('.layout').isVisible(), false);
    await page.locator('#orbitaAuthEmail').fill('owner@example.test');
    await page.locator('#orbitaAuthPassword').fill('test-password-123');
    await page.locator('#orbitaAuthLogin button[type=submit]').click();
    await page.locator('#orbitaAuthRoot').waitFor({state:'hidden'});
    assert.equal(await page.locator('#statOpen').innerText(), '0');
    assert.equal(await page.getByRole('searchbox', {name:'Pesquisar registros'}).count(), 1);

    await page.locator('#view-records [data-add]').click();
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'fTitle');
    await page.locator('#recordForm button[type=submit]').focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'closeModal');
    await page.keyboard.press('Shift+Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.textContent.trim()), 'Salvar registro');
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#modal').isVisible(), false);
    assert.equal(await page.evaluate(() => document.activeElement?.hasAttribute('data-add')), true);

    await page.locator('#view-records [data-add]').click();
    await page.locator('#fTitle').fill('Revisar documentação');
    await page.locator('#fNotes').fill('Conferir proposta');
    await page.locator('#recordForm button[type=submit]').click();
    assert.equal(await page.locator('#statOpen').innerText(), '1');
    await page.locator('#recordsList [data-edit]').click();
    await page.locator('#fTitle').fill('Revisar documentação ORBITA');
    await page.locator('#fPriority').selectOption('P0');
    await page.locator('#recordForm button[type=submit]').click();
    assert.equal(await page.locator('#statPriority').innerText(), '1');

    await page.locator('#view-records [data-add]').click();
    await page.locator('#fTitle').fill('Pagar conta');
    await page.locator('#recordForm button[type=submit]').click();
    assert.equal(await page.locator('#statOpen').innerText(), '2');
    await page.locator('#search').fill('documentacao');
    await page.locator('#filterType').selectOption('tarefa');
    await page.locator('#filterPriority').selectOption('P0');
    await page.locator('#filterStatus').selectOption('a_fazer');
    assert.equal(await page.locator('#filteredCount').innerText(), '1 de 2 registro(s)');
    assert.equal(await page.locator('#recordsList .entry').count(), 1);
    await page.locator('#clearFilters').click();
    assert.equal(await page.locator('#recordsList .entry').count(), 2);
    assert.equal(await page.locator('#clearFilters').isVisible(), false);

    let releaseVerification, markVerifying;
    const verificationStarted = new Promise(resolve => { markVerifying = resolve; });
    const userCheck = url => url.href === cloud + '/auth/v1/user';
    await page.route(userCheck, async route => {
      await new Promise(resolve => { releaseVerification = resolve; markVerifying(); });
      await route.fallback();
    });
    await page.reload({waitUntil:'domcontentloaded'});
    await verificationStarted;
    assert.equal(await page.locator('#orbitaAuthRoot').isVisible(), true);
    assert.equal(await page.locator('#orbitaAuthLogin').isVisible(), false,
      'O formulário de login não deve aparecer durante a restauração da sessão');
    assert.match(await page.locator('#orbitaAuthTitle').innerText(), /Verificando sua sessão/);
    assert.equal(await page.locator('.layout').isVisible(), false);
    releaseVerification();
    await page.unroute(userCheck);
    await page.locator('#orbitaAuthRoot').waitFor({state:'hidden'});
    assert.equal(await page.locator('#statOpen').innerText(), '2');
    assert.equal(await page.locator('#statPriority').innerText(), '1');
    assert.equal(await page.locator('#recordsList .entry').count(), 2);
    await page.locator('.mobile-nav [data-view="home"]').click();
    page.once('dialog', dialog => dialog.dismiss());
    await page.locator('#homeList [data-complete]').first().click();
    assert.equal(await page.locator('#statOpen').innerText(), '2');
    await page.evaluate(() => {
      window.orbitaOriginalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = function(key, value) {
        if (key === 'orbita_v12_local') throw Error('armazenamento indisponível');
        return window.orbitaOriginalSetItem.call(this, key, value);
      };
    });
    page.once('dialog', dialog => dialog.accept());
    await page.locator('#homeList [data-complete]').first().click();
    assert.equal(await page.locator('#statOpen').innerText(), '2', 'Falha de gravação não pode concluir visualmente');
    assert.match(await page.locator('#toast').innerText(), /Não foi possível concluir/);
    await page.evaluate(() => { Storage.prototype.setItem = window.orbitaOriginalSetItem; });
    page.once('dialog', dialog => dialog.accept());
    await page.locator('#homeList [data-complete]').first().click();
    assert.equal(await page.locator('#statOpen').innerText(), '1');
    assert.equal(await page.locator('#statPriority').innerText(), '0');
    assert.match(await page.locator('#summaryEvening').innerText(), /Concluídos hoje: 1/);
    await page.locator('.mobile-nav [data-view="records"]').click();
    await page.locator('#filterStatus').selectOption('concluida');
    assert.equal(await page.locator('#recordsList .entry').count(), 1);
    assert.match(await page.locator('#recordsList').innerText(), /Revisar documentação ORBITA/);
    const beforeRead = await page.evaluate(() => localStorage.getItem('orbita_v12_local'));
    await page.locator('.mobile-nav [data-view="home"]').click();
    await page.locator('#orbitaCloudInspect').click();
    await page.waitForFunction(() => document.querySelector('#orbitaCloudChecked')?.textContent.startsWith('Conferido'));
    await page.locator('.mobile-nav [data-view="data"]').click();
    await page.locator('#orbitaCloudPreview').click();
    await page.waitForFunction(() => document.querySelector('#orbitaCloudPreviewStatus')?.textContent.includes('Ainda não foi gravado nada'));
    assert.equal(await page.evaluate(() => localStorage.getItem('orbita_v12_local')), beforeRead);
    assert(remoteMethods.length >= 2 && remoteMethods.every(method => method === 'GET'));

    await page.locator('.mobile-nav [data-view="records"]').click();
    await page.locator('#recordsList [data-edit]').click();
    await page.locator('#fNotes').fill('Revisão após a primeira simulação');
    await page.locator('#recordForm button[type=submit]').click();
    assert.match(await page.locator('#orbitaCloudPreviewStatus').innerText(), /mudou após a simulação/);

    let resumeRemote, markPaused;
    const remotePaused = new Promise(resolve => { markPaused = resolve; });
    const pauseQuery = url => url.href.startsWith(cloud + '/rest/v1/orbita_records?select=id,payload,updated_at');
    await page.route(pauseQuery, async route => {
      await new Promise(resolve => { resumeRemote = resolve; markPaused(); });
      await route.fallback();
    });
    await page.locator('.mobile-nav [data-view="data"]').click();
    await page.locator('#orbitaCloudPreview').click();
    await remotePaused;
    await page.locator('.mobile-nav [data-view="records"]').click();
    await page.locator('#recordsList [data-edit]').click();
    await page.locator('#fNotes').fill('Revisão durante a consulta');
    await page.locator('#recordForm button[type=submit]').click();
    resumeRemote();
    await page.waitForFunction(() => document.querySelector('#orbitaCloudPreviewStatus')?.textContent.includes('mudaram durante a simulação'));
    await page.unroute(pauseQuery);
    await page.locator('.mobile-nav [data-view="data"]').click();
    await page.locator('#orbitaCloudPreview').click();
    await page.waitForFunction(() => document.querySelector('#orbitaCloudPreviewStatus')?.textContent.includes('Ainda não foi gravado nada'));
    assert(remoteMethods.every(method => method === 'GET'));

    await page.reload({waitUntil:'networkidle'});
    await page.locator('#orbitaAuthRoot').waitFor({state:'hidden'});
    assert.equal(await page.locator('#statOpen').innerText(), '1');
    assert.equal(await page.locator('#statPriority').innerText(), '0');
    assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem('orbita_v12_local')).records
      .find(item => item.title === 'Revisar documentação ORBITA')?.status), 'concluida');
    await page.locator('.mobile-nav [data-view="records"]').click();
    await page.locator('#view-records [data-add]').click();
    await page.locator('#fTitle').fill('Plano de viagem');
    await page.locator('#fType').selectOption('ideia');
    await page.locator('#recordForm button[type=submit]').click();
    await page.locator('.mobile-nav [data-view="chat"]').click();
    await page.locator('#chatInput').fill('concluir Plano de viagem');
    await page.locator('#chatSend').click();
    await page.locator('#chatApprove').waitFor({state:'visible'});
    page.once('dialog', dialog => dialog.accept());
    await page.locator('#chatApprove').click();
    assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem('orbita_v12_local')).records
      .find(item => item.title === 'Plano de viagem')?.status), 'concluida');
    assert.equal(await page.locator('#statOpen').innerText(), '1');
    for (const width of [320,390,1280]) {
      await page.setViewportSize({width,height:844});
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false,
        `Overflow em ${width}px`);
    }
    let verificationCalls = 0;
    await page.route(userCheck, route => {
      if (route.request().method() !== 'GET') return route.fallback();
      verificationCalls++;
      if (verificationCalls === 1) return route.fulfill({status:503,
        headers:{'access-control-allow-origin':'*','content-type':'application/json'},body:'{}'});
      return route.fallback();
    });
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('#orbitaAuthRetry').waitFor({state:'visible'});
    assert.equal(await page.locator('#orbitaAuthLogin').isVisible(), false);
    assert.equal(await page.locator('.layout').isVisible(), false);
    assert.equal(await page.evaluate(() => !!sessionStorage.getItem('orbita_auth_session_v1')), true,
      'Falha temporária não deve apagar a sessão salva');
    await page.locator('#orbitaAuthRetry').click();
    await page.locator('#orbitaAuthRoot').waitFor({state:'hidden'});
    assert.equal(await page.locator('#statOpen').innerText(), '1');
    assert.equal(verificationCalls, 2);
    await page.unroute(userCheck);

    await page.locator('.side [data-view="home"]').click();
    await page.waitForFunction(() => document.querySelector('#orbitaCloudDashboardStatus')?.textContent.includes('Conectado ao Supabase'));
    await page.evaluate(() => {
      window.orbitaOriginalDateNow = Date.now;
      Date.now = () => window.orbitaOriginalDateNow() + 7200000;
    });
    let refreshCalls = 0;
    const refreshToken = url => url.href === cloud + '/auth/v1/token?grant_type=refresh_token';
    await page.route(refreshToken, route => {
      if (route.request().method() !== 'POST') return route.fallback();
      refreshCalls++;
      if (refreshCalls === 1) return route.fulfill({status:503,
        headers:{'access-control-allow-origin':'*','content-type':'application/json'},body:'{}'});
      return route.fallback();
    });
    await page.locator('#orbitaCloudInspect').click();
    await page.waitForFunction(() => document.querySelector('#orbitaCloudDashboardStatus')?.textContent.includes('Não foi possível consultar'));
    assert.equal(await page.locator('#orbitaAuthRoot').isVisible(), false);
    assert.equal(await page.evaluate(() => !!sessionStorage.getItem('orbita_auth_session_v1')), true);
    await page.locator('#orbitaCloudInspect').click();
    await page.waitForFunction(() => document.querySelector('#orbitaCloudDashboardStatus')?.textContent.includes('Conectado ao Supabase'));
    assert.equal(refreshCalls, 2);
    await page.unroute(refreshToken);
    await page.evaluate(() => { Date.now = window.orbitaOriginalDateNow; });

    await page.route(userCheck, route => route.request().method() === 'GET'
      ? route.fulfill({status:401,
        headers:{'access-control-allow-origin':'*','content-type':'application/json'},body:'{}'})
      : route.fallback());
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('#orbitaAuthLogin').waitFor({state:'visible'});
    assert.equal(await page.locator('#orbitaAuthRetry').isVisible(), false);
    assert.equal(await page.locator('.layout').isVisible(), false);
    assert.equal(await page.evaluate(() => sessionStorage.getItem('orbita_auth_session_v1')), null,
      'Sessão recusada pelo Auth deve ser descartada');
    await page.unroute(userCheck);
    assert.deepEqual(errors, []);
    console.log('Jornada de tarefas, memória somente leitura e recuperação Auth: OK');
    await context.close();
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
