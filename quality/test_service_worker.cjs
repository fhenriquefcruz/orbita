'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../docs/sw.js'), 'utf8');
const scope = 'https://example.test/orbita/';

function harness(initialCache = {}) {
  const listeners = {};
  const entries = new Map(Object.entries(initialCache));
  const storage = new Map([['orbita-pages-v3.13.0-offline-scope.1', entries]]);
  const fetchCalls = [];
  let networkResponse = null;
  const cache = name => ({
    async addAll(urls) { for (const url of urls) entries.set(new URL(url, scope).href, new Response('precache:' + url)); },
    async match(key) { return storage.get(name)?.get(key) || undefined; },
    async put(key, response) { storage.get(name).set(key, response); }
  });
  const ctx = {
    URL, Set, Response,
    self: {
      registration: {scope},
      clients: {claim: async () => {}},
      skipWaiting: async () => {},
      addEventListener(type, handler) { listeners[type] = handler; }
    },
    caches: {
      async open(name) { if (!storage.has(name)) storage.set(name, new Map()); return cache(name); },
      async keys() { return [...storage.keys()]; },
      async delete(name) { return storage.delete(name); }
    },
    fetch: async request => {
      fetchCalls.push(request.url);
      if (networkResponse === null) throw Error('offline');
      return networkResponse;
    }
  };
  vm.runInNewContext(source, ctx, {filename:'docs/sw.js'});
  async function request(uri, {mode = 'same-origin', method = 'GET'} = {}) {
    const actions = [];
    let response;
    listeners.fetch({
      request:{url:new URL(uri,scope).href,mode,method},
      respondWith(promise) { response = promise; },
      waitUntil(promise) { actions.push(promise); }
    });
    const result = response ? await response : null;
    await Promise.all(actions);
    return result;
  }
  return {request, entries, storage, fetchCalls, listeners, setNetwork(value) { networkResponse = value; }};
}

test('offline: script em cache mantém tipo/conteúdo próprio, nunca recebe HTML', async () => {
  const sw = harness({
    [scope + 'index.html']: new Response('<html>ORBITA</html>', {headers:{'Content-Type':'text/html'}}),
    [scope + 'auth.js']: new Response('window.auth = true;', {headers:{'Content-Type':'application/javascript'}})
  });
  const response = await sw.request('./auth.js');
  assert.equal(response.status, 200);
  assert.match(await response.text(), /window\.auth/);
  assert.equal(response.headers.get('Content-Type'), 'application/javascript');
});

test('offline: script sem cache retorna 503 texto, não HTML da aplicação', async () => {
  const sw = harness({[scope + 'index.html']: new Response('<html>ORBITA</html>')});
  const response = await sw.request('./cloud-sync.js');
  assert.equal(response.status, 503);
  assert.match(response.headers.get('Content-Type'), /text\/plain/);
});

test('offline: navegação dentro do escopo utiliza index.html previamente instalado', async () => {
  const sw = harness({[scope + 'index.html']: new Response('<html>ORBITA</html>')});
  const response = await sw.request('./app', {mode:'navigate'});
  assert.equal(await response.text(), '<html>ORBITA</html>');
});

test('não intercepta API, domínios externos, caminhos fora do escopo ou arquivos desconhecidos', async () => {
  const sw = harness();
  assert.equal(await sw.request('./api/private'), null);
  assert.equal(await sw.request('https://elsewhere.test/orbita/index.html'), null);
  assert.equal(await sw.request('https://example.test/other/auth.js'), null);
  assert.equal(await sw.request('./secret.json'), null);
  assert.equal(await sw.request('./auth.js', {method:'POST'}), null);
  assert.equal(sw.fetchCalls.length, 0);
});

test('sucesso da rede: atualiza apenas recursos estáticos permitidos', async () => {
  const sw = harness();
  const served = new Response('/* v2 */', {headers:{'Content-Type':'application/javascript'}});
  Object.defineProperty(served, 'type', {value:'basic'}); // Resposta same-origin no navegador.
  sw.setNetwork(served);
  const response = await sw.request('./auth.js');
  assert.equal(await response.text(), '/* v2 */');
  assert.equal(await sw.entries.get(scope + 'auth.js').text(), '/* v2 */');
  assert.equal(sw.entries.has(scope + 'secret.json'), false);
});

test('ativação apaga apenas caches antigos do ORBITA', async () => {
  const sw = harness();
  sw.storage.set('orbita-pages-3.12', new Map());
  sw.storage.set('other-project-cache', new Map());
  const pending = [];
  sw.listeners.activate({waitUntil(p) { pending.push(p); }});
  await Promise.all(pending);
  assert.equal(sw.storage.has('orbita-pages-3.12'), false);
  assert.equal(sw.storage.has('other-project-cache'), true);
  assert.equal(sw.storage.has('orbita-pages-v3.13.0-offline-scope.1'), true);
});
