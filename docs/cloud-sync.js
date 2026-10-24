/* ORBITA 3.0 | Acesso autenticado e migração explícita para Supabase.
 * O painel local continua funcionando sem rede; login e sincronização exigem
 * projeto próprio, esquema RLS e conta Auth. Nenhum token é persistido.
 */
(() => {
  'use strict';
  const config = window.ORBITA_CLOUD_PUBLIC || {};
  const core = window.OrbitaCloudCore;
  const STORE = 'orbita_v12_local', TOMBSTONES = 'orbita_cloud_tombstones_v1';
  const BINDING = 'orbita_cloud_binding_v1';
  let accessToken = '', accountId = '', busy = false, dirty = false;
  const base = (config.url || '').replace(/\/$/, '');
  const allowed = /^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(base) &&
    /^(sb_publishable_[\w-]+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/.test(config.publishableKey || '');
  const el = id => document.getElementById(id);
  const setText = (id, text) => { const node = el(id); if (node) node.textContent = text; };
  const mode = text => { setText('orbitaCloudStatus', text); };

  function localData() {
    const parsed = JSON.parse(localStorage.getItem(STORE) || '{}');
    if (parsed.records !== undefined && !Array.isArray(parsed.records)) throw Error('Backup local inconsistente');
    return {schema_version: parsed.schema_version || 1,
      records: parsed.records || [], audit: Array.isArray(parsed.audit) ? parsed.audit : []};
  }
  function tombstones() {
    const parsed = JSON.parse(localStorage.getItem(TOMBSTONES) || '{}');
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw Error('Lista de exclusões inválida');
    return parsed;
  }
  async function request(path, method = 'GET', payload = undefined, opts = {}) {
    if (!allowed) throw Error('Integração não configurada');
    const headers = {'apikey': config.publishableKey, 'Content-Type': 'application/json'};
    if (accessToken) headers.Authorization = 'Bearer ' + accessToken;
    if (opts.prefer) headers.Prefer = opts.prefer;
    const result = await fetch(base + path, {method, headers,
      body: payload === undefined ? undefined : JSON.stringify(payload), cache: 'no-store'});
    if (!result.ok) throw Error('Servidor recusou operação (HTTP ' + result.status + ')');
    const text = await result.text();
    return text ? JSON.parse(text) : [];
  }
  async function loadCloud() {
    const rows = [];
    let offset = 0;
    do {
      const search = '?select=id,payload,updated_at&order=updated_at.desc&limit=500&offset=' + offset;
      const part = await request('/rest/v1/orbita_records' + search);
      rows.push(...part);
      if (part.length < 500) break;
      offset += part.length;
      if (offset >= 10000) throw Error('Limite de consulta atingido; sincronização interrompida');
    } while (true);
    return rows;
  }
  async function login(event) {
    event.preventDefault();
    if (!allowed) { mode('Configuração pública do Supabase ainda pendente.'); return; }
    const email = el('orbitaCloudEmail').value.trim();
    const password = el('orbitaCloudPassword').value;
    if (!email || !password) return;
    busy = true; renderButtons(); mode('Autenticando...');
    try {
      const session = await request('/auth/v1/token?grant_type=password', 'POST', {email, password});
      if (!session.access_token || !session.user?.id) throw Error('Sessão não recebida');
      const savedBinding = localStorage.getItem(BINDING);
      if (savedBinding && savedBinding !== session.user.id) throw Error(
        'Este navegador contém dados vinculados a outra conta. Exporte um backup e use um perfil de navegador separado.');
      accessToken = session.access_token;
      accountId = session.user.id;
      el('orbitaCloudPassword').value = '';
      mode('Conectado: memória central disponível. Sincronização somente mediante confirmação.');
      setText('modeSide','Memória local + nuvem sob demanda');
      el('orbitaCloudLogin').hidden = true;
      el('orbitaCloudActions').hidden = false;
    } catch (e) { accessToken = ''; accountId = ''; mode('Não foi possível entrar: ' + e.message); }
    finally { busy = false; renderButtons(); }
  }
  function saveBackup(snapshot) {
    const blob = new Blob([JSON.stringify({...snapshot, exported_at: new Date().toISOString()}, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'orbita-backup-antes-sincronizacao-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 15000);
  }
  function renderButtons() {
    if (el('orbitaCloudSync')) el('orbitaCloudSync').disabled = busy || !accessToken;
    if (el('orbitaCloudSubmit')) el('orbitaCloudSubmit').disabled = busy;
  }
  async function sync() {
    if (!accessToken || busy) return;
    busy = true; renderButtons(); mode('Comparando a memória local e a nuvem...');
    try {
      const snapshot = localData();
      const remote = await loadCloud();
      const deleted = tombstones();
      const plan = core.reconcile(snapshot.records, remote, deleted);
      const detail = `${snapshot.records.length} locais, ${remote.length} na nuvem, ` +
        `${plan.upserts.length} a enviar, ${plan.deletions.length} exclusões e ` +
        `${plan.records.length} após conciliação.`;
      if (!window.confirm('ORBITA — sincronização da memória\n\n' + detail +
        '\n\nSerá feito um backup antes de alterar os dados deste navegador. Continuar?')) {
        mode('Operação cancelada. Nenhum dado foi alterado.'); return;
      }
      saveBackup(snapshot);
      for (const item of plan.upserts) {
        await request('/rest/v1/orbita_records?on_conflict=id', 'POST', {
          id: item.id, user_id: accountId, payload: item,
          created_at: item.created_at || new Date().toISOString(),
          updated_at: item.updated_at || new Date().toISOString()
        }, {prefer: 'resolution=merge-duplicates,return=minimal'});
      }
      for (const id of plan.deletions) {
        await request('/rest/v1/orbita_records?id=eq.' + encodeURIComponent(id), 'DELETE',
          undefined, {prefer:'return=minimal'});
      }
      const clear = {...deleted};
      plan.clearTombstones.concat(plan.deletions).forEach(id => delete clear[id]);
      // Gravação conjunta recuperável: backup prévio criado acima.
      localStorage.setItem(STORE, JSON.stringify({...snapshot, records:plan.records}));
      localStorage.setItem(TOMBSTONES, JSON.stringify(clear));
      localStorage.setItem(BINDING, accountId);
      dirty = false;
      mode('Sincronização confirmada: ' + plan.records.length + ' registros conciliados. Atualizando a tela...');
      setTimeout(() => location.reload(), 500);
    } catch (e) { dirty = true; mode('Sincronização não concluída: ' + e.message + '. Seus dados locais foram preservados.'); }
    finally { busy = false; renderButtons(); }
  }
  function logout() {
    accessToken = ''; accountId = '';
    el('orbitaCloudLogin').hidden = false;
    el('orbitaCloudActions').hidden = true;
    mode('Desconectado. Os registros locais continuam disponíveis.');
    setText('modeSide','Modo HTML local • neste navegador');
    renderButtons();
  }
  function buildPanel() {
    const parent = document.getElementById('view-data');
    if (!parent) return;
    const card = document.createElement('section');
    card.className = 'card orbita-cloud-panel';
    card.innerHTML = `<div class="sectionhead"><h2>Memória central</h2><span class="chip">SUPABASE · RLS</span></div>
      <p class="small muted">A conexão é opcional. Dados deste navegador só serão enviados após login e confirmação. O Telegram usará a mesma base quando seu backend estiver configurado.</p>
      <p class="small" id="orbitaCloudStatus" role="status" aria-live="polite"></p>
      <form id="orbitaCloudLogin" class="orbita-cloud-login">
        <label class="field" for="orbitaCloudEmail">E-mail da conta ORBITA<input class="input" id="orbitaCloudEmail" type="email" autocomplete="username" required></label>
        <label class="field" for="orbitaCloudPassword">Senha<input class="input" id="orbitaCloudPassword" type="password" autocomplete="current-password" required></label>
        <button id="orbitaCloudSubmit" class="btn primary" type="submit">Conectar memória</button>
      </form>
      <div id="orbitaCloudActions" hidden class="actions orbita-cloud-actions">
        <button id="orbitaCloudSync" type="button" class="btn primary">Conciliar registros agora</button>
        <button id="orbitaCloudLogout" type="button" class="btn">Desconectar</button>
      </div>`;
    parent.append(card);
    el('orbitaCloudLogin').addEventListener('submit', login);
    el('orbitaCloudSync').addEventListener('click', sync);
    el('orbitaCloudLogout').addEventListener('click', logout);
    mode(allowed ? 'Pronta para autenticar. Os dados continuam somente neste navegador.' :
      'Memória central não configurada. O painel continua em modo local; veja a documentação de implantação.');
    if (!allowed) { el('orbitaCloudLogin').hidden = true; }
    window.addEventListener('orbita:local-change', () => {
      if (accessToken) { dirty = true; mode('Alterações locais pendentes. Clique em “Conciliar registros agora”.'); }
    });
  }
  buildPanel();
})();
