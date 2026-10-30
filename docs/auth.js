/* ORBITA | Supabase Auth em página estática.
 * GitHub Pages hospeda a interface; RLS é a barreira real para dados no Supabase.
 * Sessão fica em sessionStorage (sobrevive a recargas, não ao encerramento da aba).
 */
(function () {
  'use strict';
  const config = window.ORBITA_CLOUD_PUBLIC || {};
  const base = String(config.url || '').replace(/\/$/, '');
  const key = String(config.publishableKey || '');
  const configured = /^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(base) &&
    /^(sb_publishable_[\w-]+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/.test(key);
  // Links de e-mail podem chegar com tokens no fragmento. Capturar em memória
  // e LIMPAR a URL imediatamente, antes de renderizar ou consultar a API.
  // Nunca usar fragmentos não reconhecidos como prova de autenticação.
  const callbackFragment = new URLSearchParams(location.hash.replace(/^#/, ''));
  const callbackQuery = new URLSearchParams(location.search);
  const tokenFragment = ['access_token', 'refresh_token', 'token_hash']
    .some(name => callbackFragment.has(name));
  const callbackError = ['error', 'error_code'].some(name => callbackFragment.has(name));
  const sensitiveQuery = ['access_token', 'refresh_token', 'token_hash', 'code',
    'error', 'error_code'].some(name => callbackQuery.has(name));
  if (tokenFragment || callbackError || sensitiveQuery) {
    history.replaceState(null, '', location.pathname +
      (sensitiveQuery ? '' : location.search));
  }

  const STORAGE = 'orbita_auth_session_v1';
  const BINDING = 'orbita_cloud_binding_v1';
  const LEGACY = ['orbita_v12_local', 'orbita_v13_chat', 'orbita_cloud_tombstones_v1'];
  const readyCallbacks = [];
  let session = null;
  let user = null;
  let unlocked = false;
  let refreshing = null;
  let busy = false;
  let mode = 'login';

  const $ = (id) => document.getElementById(id);
  document.documentElement.removeAttribute('data-orbita-auth');

  const style = document.createElement('style');
  style.textContent = [
    '.orbita-auth-root{position:fixed;inset:0;z-index:1000;display:grid;place-items:center;overflow:auto;padding:22px;background:radial-gradient(circle at 13% 15%,#25483e 0%,#0b1216 44%,#081014 100%);color:#edf5f3;font-family:Inter,system-ui,sans-serif}',
    '.orbita-auth-root[hidden]{display:none!important}.orbita-auth-card{width:min(420px,100%);padding:clamp(23px,5vw,37px);border:1px solid #344950;border-radius:22px;background:#152228;box-shadow:0 25px 90px #0008}',
    '.orbita-auth-mark{font-size:12px;font-weight:800;color:#69d3b1;letter-spacing:.2em}.orbita-auth-card h1{font-family:Georgia,serif;font-size:32px;line-height:1.2;font-weight:500;margin:15px 0 12px}',
    '.orbita-auth-description,.orbita-auth-caption{font-size:13px;line-height:1.6;color:#afc2c0}.orbita-auth-field{display:grid;gap:7px;margin:16px 0}',
    '.orbita-auth-field label{font-size:12px;color:#d5e5e0}.orbita-auth-field input{width:100%;padding:13px;border-radius:10px;color:#fff;background:#0c181c;border:1px solid #40565b;font:inherit;min-width:0}',
    '.orbita-auth-field input:focus-visible,.orbita-auth-root button:focus-visible{outline:2px solid #69d3b1;outline-offset:3px}.orbita-auth-root button{cursor:pointer;font:inherit;border-radius:10px;border:1px solid #40565b}',
    '.orbita-auth-submit{background:#69d3b1!important;color:#102a24!important;font-size:13px!important;font-weight:800!important;padding:13px 17px;width:100%;margin-top:8px;border:0!important}',
    '.orbita-auth-links{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:20px}.orbita-auth-link{color:#8ee0c5;background:transparent;border:0!important;padding:6px 0;font-size:12px!important}',
    '.orbita-auth-status{min-height:20px;font-size:12px;color:#f2c789;line-height:1.6;margin:12px 0 0}.orbita-auth-root button:disabled{opacity:.6;cursor:wait}',
    '.orbita-auth-card form[hidden]{display:none!important}.orbita-auth-root code{color:#d5e5e0;font-size:11px;overflow-wrap:anywhere}'
  ].join('');
  document.head.appendChild(style);

  const root = document.createElement('section');
  root.id = 'orbitaAuthRoot';
  root.className = 'orbita-auth-root';
  root.setAttribute('aria-label', 'Acesso ao ORBITA');
  root.innerHTML = [
    '<div class="orbita-auth-card">',
    '<div class="orbita-auth-mark">◉ ORBITA · ACESSO SEGURO</div>',
    '<h1 id="orbitaAuthTitle">Seu espaço pessoal.</h1>',
    '<p class="orbita-auth-description" id="orbitaAuthDescription">Entre para acessar a sua central e a memória protegida.</p>',
    '<form id="orbitaAuthLogin">',
    '<div class="orbita-auth-field"><label for="orbitaAuthEmail">E-mail</label><input id="orbitaAuthEmail" type="email" autocomplete="username" required></div>',
    '<div class="orbita-auth-field"><label for="orbitaAuthPassword">Senha</label><input id="orbitaAuthPassword" type="password" autocomplete="current-password" required></div>',
    '<button class="orbita-auth-submit" type="submit">Entrar no ORBITA</button>',
    '</form>',
    '<form id="orbitaAuthRecover" hidden>',
    '<div class="orbita-auth-field"><label for="orbitaRecoverEmail">E-mail cadastrado</label><input id="orbitaRecoverEmail" type="email" autocomplete="email" required></div>',
    '<button class="orbita-auth-submit" type="submit">Enviar recuperação</button>',
    '</form>',
    '<form id="orbitaAuthReset" hidden>',
    '<div class="orbita-auth-field"><label for="orbitaAuthNewPassword">Nova senha</label><input id="orbitaAuthNewPassword" type="password" autocomplete="new-password" minlength="12" required></div>',
    '<div class="orbita-auth-field"><label for="orbitaAuthConfirm">Repita a nova senha</label><input id="orbitaAuthConfirm" type="password" autocomplete="new-password" minlength="12" required></div>',
    '<button class="orbita-auth-submit" type="submit">Atualizar senha</button>',
    '</form>',
    '<p role="status" aria-live="polite" id="orbitaAuthStatus" class="orbita-auth-status"></p>',
    '<button id="orbitaAuthRetry" class="orbita-auth-submit" type="button" hidden>Tentar novamente</button>',
    '<div class="orbita-auth-links"><button id="orbitaForgot" class="orbita-auth-link" type="button">Esqueci minha senha</button><button id="orbitaBack" class="orbita-auth-link" type="button" hidden>Voltar ao login</button></div>',
    '<p class="orbita-auth-caption">Acesso restrito aos titulares de contas autorizadas. Seus registros não são públicos.</p>',
    '</div>'
  ].join('');
  document.body.appendChild(root);

  function status(message) { $('orbitaAuthStatus').textContent = message || ''; }
  function show(next, message = '') {
    mode = next;
    $('orbitaAuthLogin').hidden = next !== 'login';
    $('orbitaAuthRecover').hidden = next !== 'recover';
    $('orbitaAuthReset').hidden = next !== 'reset';
    $('orbitaAuthRetry').hidden = next !== 'retry';
    $('orbitaForgot').hidden = next !== 'login';
    $('orbitaBack').hidden = next === 'login' || next === 'checking';
    $('orbitaAuthTitle').textContent = next === 'checking' ? 'Verificando sua sessão.' :
      next === 'retry' ? 'Conexão indisponível.' :
      next === 'reset' ? 'Defina sua nova senha.' :
      next === 'recover' ? 'Recuperar acesso.' : 'Seu espaço pessoal.';
    $('orbitaAuthDescription').textContent = next === 'checking' ?
      'Aguarde enquanto confirmamos seu acesso ao ORBITA.' :
      next === 'retry' ? 'Sua sessão continua salva nesta aba. Tente verificar o acesso novamente.' :
      next === 'reset' ? 'Escolha uma senha com ao menos 12 caracteres.' :
      next === 'recover' ? 'Enviaremos um link para o e-mail cadastrado.' :
      'Entre para acessar a sua central e a memória protegida.';
    root.setAttribute('aria-busy', next === 'checking' ? 'true' : 'false');
    status(message);
    root.hidden = false;
    if (next === 'retry') $('orbitaAuthRetry').focus();
  }
  function setBusy(value) {
    busy = value;
    root.querySelectorAll('button').forEach(button => { button.disabled = value; });
  }
  function forget() {
    session = null;
    user = null;
    unlocked = false;
    sessionStorage.removeItem(STORAGE);
    document.documentElement.removeAttribute('data-orbita-auth');
  }
  function remember(data) {
    if (!data?.access_token || !data?.refresh_token) throw Error('Sessão inválida recebida do servidor.');
    session = {access_token:data.access_token,refresh_token:data.refresh_token,
      expires_at: Math.floor(Date.now() / 1000) + Number(data.expires_in || 3600)};
    sessionStorage.setItem(STORAGE, JSON.stringify(session));
  }
  async function request(path, options = {}, token = '') {
    if (!configured) throw Error('Projeto Supabase ainda não configurado.');
    const headers = {apikey:key, 'Content-Type':'application/json'};
    if (token) headers.Authorization = 'Bearer ' + token;
    const response = await fetch(base + '/auth/v1' + path, {
      method:options.method || 'GET',headers,cache:'no-store',
      body:options.body === undefined ? undefined : JSON.stringify(options.body)
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = result.msg || result.error_description || result.message || result.error ||
        ('Falha ao autenticar (HTTP ' + response.status + ').');
      const err = new Error(String(message));
      err.status = response.status;
      throw err;
    }
    return result;
  }
  async function refresh() {
    if (refreshing) return refreshing;
    refreshing = (async () => {
      if (!session?.refresh_token) throw Error('É necessário entrar novamente.');
      const next = await request('/token?grant_type=refresh_token', {
        method:'POST',body:{refresh_token:session.refresh_token}
      });
      remember(next);
      return session.access_token;
    })();
    try { return await refreshing; } finally { refreshing = null; }
  }
  async function token() {
    if (!session) throw Error('Acesso não autenticado.');
    if (session.expires_at <= Date.now() / 1000 + 60) await refresh();
    return session.access_token;
  }
  async function getVerifiedUser() {
    let access = await token();
    try { return await request('/user', {}, access); }
    catch (err) {
      if (err.status !== 401) throw err;
      access = await refresh();
      return request('/user', {}, access);
    }
  }
  function bindLocalAccount(id) {
    const binding = localStorage.getItem(BINDING);
    if (binding && binding !== id)
      throw Error('Este navegador já contém dados de outra conta ORBITA. Faça login pelo perfil correto.');
    if (!binding) {
      const hasLegacy = LEGACY.some(k => {
        try {
          const raw = localStorage.getItem(k);
          if (!raw) return false;
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) return parsed.length > 0;
          if (!parsed || typeof parsed !== 'object') return true;
          if (k === 'orbita_cloud_tombstones_v1') return Object.keys(parsed).length > 0;
          return (Array.isArray(parsed.records) && parsed.records.length > 0) ||
            (Array.isArray(parsed.audit) && parsed.audit.length > 0);
        } catch (_) { return true; }
      });
      if (hasLegacy && !window.confirm(
        'Este navegador possui dados locais ou exclusões anteriores à autenticação.\n\n' +
        'Eles serão vinculados permanentemente a esta conta ORBITA. Confirme somente se ela for sua.'
      )) throw Error('Vinculação dos registros locais não autorizada.');
      localStorage.setItem(BINDING, id);
    }
  }
  function unlock(verified) {
    if (!verified?.id) throw Error('Identidade não verificada.');
    window.OrbitaLocalIntegrity.assertReady();
    bindLocalAccount(verified.id);
    user = {id:verified.id,email:verified.email || ''};
    unlocked = true;
    document.documentElement.setAttribute('data-orbita-auth', 'ready');
    root.hidden = true;
    const label = $('orbitaAuthIdentity');
    if (label) label.textContent = user.email || 'Conta autenticada';
    for (const callback of readyCallbacks.splice(0)) callback();
    window.dispatchEvent(new CustomEvent('orbita:authenticated', {detail:{user:user}}));
  }
  async function signIn(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    status('Verificando suas credenciais...');
    try {
      const email = $('orbitaAuthEmail').value.trim();
      const password = $('orbitaAuthPassword').value;
      const data = await request('/token?grant_type=password', {method:'POST', body:{email,password}});
      remember(data);
      const verified = await getVerifiedUser();
      unlock(verified);
      $('orbitaAuthPassword').value = '';
    } catch (err) {
      forget();
      status(err.message || 'Não foi possível entrar.');
    } finally { setBusy(false); }
  }
  async function recover(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    try {
      const redirect = location.origin + location.pathname;
      await request('/recover?redirect_to=' + encodeURIComponent(redirect), {
        method:'POST',body:{email:$('orbitaRecoverEmail').value.trim()}
      });
      show('login','Caso o e-mail exista, você receberá instruções para redefinir a senha.');
    } catch (err) { status(err.message); }
    finally { setBusy(false); }
  }
  async function resetPassword(event) {
    event.preventDefault();
    if (busy) return;
    const password = $('orbitaAuthNewPassword').value;
    if (password !== $('orbitaAuthConfirm').value) { status('As senhas não coincidem.'); return; }
    setBusy(true);
    try {
      await request('/user', {method:'PUT',body:{password}}, await token());
      // Nunca conceder acesso ao painel apenas por abrir um link de recuperação.
      try { await request('/logout', {method:'POST'}, await token()); } catch (_) { /* encerramento local */ }
      forget();
      $('orbitaAuthNewPassword').value = '';
      $('orbitaAuthConfirm').value = '';
      show('login','Senha atualizada. Entre novamente com sua nova senha.');
    } catch (err) { status(err.message); }
    finally { setBusy(false); }
  }
  async function signOut() {
    try { if (session) await request('/logout',{method:'POST'}, await token()); }
    catch (_) { /* falhas externas não impedem o encerramento local */ }
    forget();
    location.replace(location.pathname);
  }
  async function restore() {
    if (!configured) {
      show('login', 'O projeto Supabase do ORBITA ainda não foi conectado. Acesso temporariamente indisponível.');
      $('orbitaAuthLogin').hidden = true;
      $('orbitaForgot').hidden = true;
      return;
    }
    if (sensitiveQuery) {
      // O painel implementa fluxo implícito. Não tratar code/PKCE como sessão.
      forget();
      show('login', 'Retorno de autenticação não reconhecido. Solicite outro link de acesso.');
      return;
    }
    if (callbackError) {
      forget();
      show('login', 'O link de autenticação não pôde ser validado. Solicite outro link.');
      return;
    }
    if (tokenFragment) {
      const kind = callbackFragment.get('type');
      const supported = ['recovery', 'invite', 'magiclink', 'signup', 'email_change'];
      const access = callbackFragment.get('access_token');
      const refreshToken = callbackFragment.get('refresh_token');
      if (!supported.includes(kind) || !access || !refreshToken) {
        forget();
        show('login', 'Link de acesso incompleto ou não reconhecido.');
        return;
      }
      try {
        remember({access_token:access, refresh_token:refreshToken,
          expires_in:Number(callbackFragment.get('expires_in') || 3600)});
        // A URL já foi limpa. Só uma verificação /auth/v1/user permite entrar.
        const verified = await getVerifiedUser();
        if (kind === 'recovery' || kind === 'invite') {
          show('reset');
        } else {
          unlock(verified);
        }
      } catch (_) {
        forget();
        show('login', 'Link inválido ou expirado. Solicite outro acesso.');
      }
      return;
    }
    try {
      const stored = sessionStorage.getItem(STORAGE);
      if (stored) session = JSON.parse(stored);
      if (!session) { show('login'); return; }
      const verified = await getVerifiedUser();
      unlock(verified);
    } catch (err) {
      // Apenas uma sessão inválida pede novo login; indisponibilidade mantém o token na aba.
      if ([400, 401, 403].includes(err.status) || !session?.refresh_token) {
        forget();
        show('login', 'Sua sessão não pôde ser validada. Entre novamente.');
      } else {
        show('retry', 'Não foi possível confirmar a sessão. Verifique a conexão e tente novamente.');
      }
    }
  }
  $('orbitaAuthLogin').addEventListener('submit', signIn);
  $('orbitaAuthRecover').addEventListener('submit', recover);
  $('orbitaAuthReset').addEventListener('submit', resetPassword);
  $('orbitaAuthRetry').addEventListener('click', () => { show('checking'); restore(); });
  $('orbitaForgot').addEventListener('click', () => { $('orbitaRecoverEmail').value = $('orbitaAuthEmail').value; show('recover'); });
  $('orbitaBack').addEventListener('click', () => {
    if (mode === 'reset' || mode === 'retry') forget();
    show('login');
  });
  const signOutButton = $('orbitaSignOut');
  if (signOutButton) signOutButton.addEventListener('click', signOut);

  window.OrbitaAuth = Object.freeze({
    isAuthenticated: () => unlocked,
    getUser: () => unlocked ? {...user} : null,
    getAccessToken: async () => {
      if (!unlocked) throw Error('Faça login para continuar.');
      try { return await token(); }
      catch (err) {
        if ([400, 401, 403].includes(err.status)) {
          forget(); location.replace(location.pathname); throw Error('Sua sessão expirou.');
        }
        throw Error('Não foi possível confirmar a conexão. Tente novamente.');
      }
    },
    onReady: (callback) => { if (unlocked) callback(); else readyCallbacks.push(callback); },
    signOut
  });
  show('checking');
  restore();
})();
