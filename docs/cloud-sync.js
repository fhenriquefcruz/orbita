/* ORBITA 3.1 | Conciliação manual vinculada à sessão autenticada do painel.
 * Nenhum login paralelo ou token privado: utiliza a identidade verificada em auth.js.
 */
(() => {
  'use strict';
  const config = window.ORBITA_CLOUD_PUBLIC || {};
  const auth = window.OrbitaAuth;
  const core = window.OrbitaCloudCore;
  const STORE = 'orbita_v12_local', TOMBSTONES = 'orbita_cloud_tombstones_v1';
  const BINDING = 'orbita_cloud_binding_v1';
  let accountId = '', busy = false, dirty = false, inspecting = false;
  let lastRemoteCount = null;
  const base = (config.url || '').replace(/\/$/, '');
  const allowed = /^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(base) &&
    /^(sb_publishable_[\w-]+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/.test(config.publishableKey || '');
  const el = id => document.getElementById(id);
  const setText = (id, text) => { const node = el(id); if (node) node.textContent = text; };
  const mode = text => { setText('orbitaCloudStatus', text); };
  // Never render a previous account's response or write a snapshot after a session switch.
  const sameAccount = id => auth.isAuthenticated() && auth.getUser()?.id === id;

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
    headers.Authorization = 'Bearer ' + await auth.getAccessToken();
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
      const search = '?select=id,payload,updated_at&order=updated_at.desc,id.asc&limit=500&offset=' + offset;
      const part = await request('/rest/v1/orbita_records' + search);
      rows.push(...part);
      if (part.length < 500) break;
      offset += part.length;
      if (offset >= 10000) throw Error('Limite de consulta atingido; sincronização interrompida');
    } while (true);
    return rows;
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
    if (el('orbitaCloudSync')) el('orbitaCloudSync').disabled = busy || !auth.isAuthenticated();
    if (el('orbitaCloudInspect')) el('orbitaCloudInspect').disabled = inspecting || busy || !auth.isAuthenticated();
  }
  function dashboardStatus(text) {
    setText('orbitaCloudDashboardStatus', text);
  }
  async function inspectRemote() {
    if (!auth.isAuthenticated() || inspecting || busy) return;
    const viewingAccount = auth.getUser().id;
    inspecting = true;
    renderButtons();
    dashboardStatus('Verificando conexão com a memória central...');
    try {
      if (!allowed) throw Error('Configuração da memória não disponível');
      const response = await fetch(base + '/rest/v1/orbita_records?select=id&limit=1', {
        method: 'GET',
        headers: {
          apikey: config.publishableKey,
          Authorization: 'Bearer ' + await auth.getAccessToken(),
          Prefer: 'count=exact',
          Accept: 'application/json'
        },
        cache: 'no-store'
      });
      if (!response.ok) throw Error('HTTP ' + response.status);
      if (!sameAccount(viewingAccount)) return;
      const range = response.headers.get('content-range') || '';
      const match = range.match(/\/(\d+)$/);
      lastRemoteCount = match ? Number(match[1]) : null;
      const localCount = localData().records.length;
      dashboardStatus('Conectado ao Supabase · ' +
        (lastRemoteCount === null ? 'total remoto indisponível' :
          lastRemoteCount + ' registro(s) na nuvem') +
        ' · ' + localCount + ' neste dispositivo' +
        (dirty ? ' · alterações locais pendentes' : ''));
      setText('orbitaCloudChecked', 'Conferido às ' +
        new Intl.DateTimeFormat('pt-BR', {hour: '2-digit', minute: '2-digit'}).format(new Date()));
    } catch (err) {
      if (!sameAccount(viewingAccount)) return;
      lastRemoteCount = null;
      dashboardStatus('Não foi possível consultar a memória central. Os dados locais não foram alterados.');
      setText('orbitaCloudChecked', '');
    } finally {
      inspecting = false;
      renderButtons();
    }
  }
  function buildBridge() {
    const home = el('view-home');
    if (!home || el('orbitaCloudBridge')) return;
    const bridge = document.createElement('section');
    bridge.id = 'orbitaCloudBridge';
    bridge.className = 'orbita-cloud-bridge';
    bridge.setAttribute('aria-label', 'Estado da memória central');
    bridge.innerHTML = '<div class="orbita-cloud-bridge-mark" aria-hidden="true">◎</div>' +
      '<div class="orbita-cloud-bridge-body">' +
      '<strong>Memória central</strong>' +
      '<span id="orbitaCloudDashboardStatus" role="status" aria-live="polite">Aguardando autenticação...</span>' +
      '<small id="orbitaCloudChecked"></small></div>' +
      '<div class="orbita-cloud-bridge-buttons">' +
      '<button class="btn sm" type="button" id="orbitaCloudInspect">Conferir</button>' +
      '<button class="btn sm primary" type="button" id="orbitaCloudOpen">Conciliar ↗</button>' +
      '</div>';
    const hero = home.querySelector('.hero');
    if (hero) hero.insertAdjacentElement('afterend', bridge);
    else home.prepend(bridge);
    el('orbitaCloudInspect').addEventListener('click', inspectRemote);
    el('orbitaCloudOpen').addEventListener('click', () => {
      const navigation = document.querySelector('[data-view="data"]');
      if (navigation) navigation.click();
    });
  }
  async function sync() {
    if (!auth.isAuthenticated() || busy) return;
    const operationAccount = auth.getUser().id;
    accountId = operationAccount;
    busy = true; renderButtons(); mode('Comparando a memória local e a nuvem...');
    try {
      // Captura versão exata: evita sobrescrever alterações feitas em outra aba durante a rede.
      const originalStore = localStorage.getItem(STORE);
      const originalTombstones = localStorage.getItem(TOMBSTONES);
      const snapshot = localData();
      const remote = await loadCloud();
      if (!sameAccount(operationAccount)) throw Error('A conta mudou durante a leitura. Refaça a conciliação.');
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
      if (!window.confirm('O navegador iniciou o download do backup local.\n\n' +
        'Antes de enviar ou excluir registros, confirme que você realmente SALVOU o arquivo de backup.\n' +
        'Se o download foi bloqueado, escolha Cancelar e exporte seus dados manualmente.\n\n' +
        'Backup salvo com segurança?')) {
        mode('Operação interrompida. Verifique o arquivo de backup antes de conciliar.'); return;
      }
      if (!sameAccount(operationAccount)) throw Error('A conta mudou. Nenhuma gravação deve continuar.');
      if (localStorage.getItem(STORE) !== originalStore ||
          localStorage.getItem(TOMBSTONES) !== originalTombstones) {
        throw Error('Houve outra alteração neste navegador. Refaça a conciliação.');
      }
      for (const item of plan.upserts) {
        if (!sameAccount(operationAccount)) throw Error('A conta mudou durante o envio.');
        await request('/rest/v1/orbita_records?on_conflict=id', 'POST', {
          id: item.id, user_id: operationAccount, payload: item,
          created_at: item.created_at || new Date().toISOString(),
          updated_at: item.updated_at || new Date().toISOString()
        }, {prefer: 'resolution=merge-duplicates,return=minimal'});
      }
      for (const id of plan.deletions) {
        if (!sameAccount(operationAccount)) throw Error('A conta mudou durante as exclusões.');
        await request('/rest/v1/orbita_records?id=eq.' + encodeURIComponent(id), 'DELETE',
          undefined, {prefer:'return=minimal'});
      }
      const clear = {...deleted};
      plan.clearTombstones.concat(plan.deletions).forEach(id => delete clear[id]);
      // Evita perda silenciosa se a sessão ou os registros mudaram enquanto a API respondia.
      if (!sameAccount(operationAccount)) throw Error('A conta mudou. O navegador não foi atualizado.');
      if (localStorage.getItem(STORE) !== originalStore ||
          localStorage.getItem(TOMBSTONES) !== originalTombstones) {
        throw Error('Os registros mudaram durante a conciliação. A nuvem pode ter alterações parciais; refaça a comparação.');
      }
      // Backup foi exigido acima; localStorage não oferece transações entre chaves.
      localStorage.setItem(STORE, JSON.stringify({...snapshot, records:plan.records}));
      localStorage.setItem(TOMBSTONES, JSON.stringify(clear));
      localStorage.setItem(BINDING, operationAccount);
      dirty = false;
      mode('Sincronização confirmada: ' + plan.records.length + ' registros conciliados. Atualizando a tela...');
      setTimeout(() => location.reload(), 500);
    } catch (e) { dirty = true; mode('Sincronização não concluída: ' + e.message +
      '. Verifique o backup; operações remotas anteriores à falha podem ter sido aplicadas.'); }
    finally { busy = false; renderButtons(); }
  }
  let telegramInspecting = false;
  function telegramNode(tag, className, content) {
    const node = document.createElement(tag);
    node.className = className;
    node.textContent = content;
    return node;
  }
  async function inspectTelegram() {
    if (!auth.isAuthenticated() || busy || telegramInspecting) return;
    const viewingAccount = auth.getUser().id;
    const status = el('orbitaTelegramStatus');
    const list = el('orbitaTelegramList');
    const refresh = el('orbitaTelegramRefresh');
    if (!status || !list || !refresh) return;
    telegramInspecting = true;
    refresh.disabled = true;
    status.textContent = 'Consultando registros do Telegram na sua conta...';
    list.replaceChildren();
    try {
      // RLS no Supabase limita o resultado à conta autenticada no painel.
      // JSONB filtra na origem; nenhuma chave privilegiada é exposta no cliente.
      const query = new URLSearchParams();
      query.set('select', 'id,payload,updated_at');
      query.set('payload->>source', 'eq.Telegram ORBITA');
      query.set('order', 'updated_at.desc,id.asc');
      query.set('limit', '5');
      const rows = await request('/rest/v1/orbita_records?' + query.toString());
      if (!sameAccount(viewingAccount)) return;
      if (!Array.isArray(rows)) throw Error('Resposta inesperada do servidor');
      const valid = rows.filter(row => row && row.payload &&
        row.payload.id === row.id && row.payload.source === 'Telegram ORBITA');
      if (!valid.length) {
        status.textContent = 'Nenhum registro do Telegram encontrado nesta conta. Verifique se o painel usa a mesma conta Auth configurada no bot.';
        return;
      }
      status.textContent = 'Últimos ' + valid.length +
        ' registro(s) do Telegram · consulta somente de leitura.';
      for (const row of valid) {
        const p = row.payload;
        const item = telegramNode('li', 'orbita-telegram-item', '');
        const info = telegramNode('div', 'orbita-telegram-item-info', '');
        info.append(telegramNode('strong', '', String(p.title || 'Sem título')));
        const kind = p.type === 'ideia' ? 'Ideia' : p.type === 'tarefa' ? 'Tarefa' : 'Registro';
        const priority = /^P[0-3]$/.test(p.priority || '') ? p.priority : '';
        info.append(telegramNode('small', '', kind + (priority ? ' · ' + priority : '')));
        const completed = p.status === 'concluida';
        const label = telegramNode('span', 'orbita-telegram-state' +
          (completed ? ' is-done' : ''), completed ? 'Concluída' : 'Em aberto');
        item.append(info, label);
        list.append(item);
      }
    } catch (_) {
      if (sameAccount(viewingAccount)) status.textContent = 'Não foi possível consultar os registros do Telegram. Os dados locais não foram alterados.';
    } finally {
      telegramInspecting = false;
      refresh.disabled = !auth.isAuthenticated();
    }
  }
  function buildPanel() {
    const parent = document.getElementById('view-data');
    if (!parent) return;
    const card = document.createElement('section');
    card.className = 'card orbita-cloud-panel';
    card.innerHTML = '<div class="sectionhead"><h2>Memória central</h2><span class="chip">SUPABASE · RLS</span></div>' +
      '<p class="small muted">Sua conta está autenticada. Dados deste navegador só serão enviados após confirmação da conciliação. O Telegram registra dados diretamente na memória central. Você pode conferi-los abaixo; a inclusão na lista e nos indicadores deste aparelho continua manual, após backup.</p>' +
      '<p class="small" id="orbitaCloudAccount"></p>' +
      '<p class="small" id="orbitaCloudStatus" role="status" aria-live="polite"></p>' +
      '<div class="orbita-telegram-preview" aria-labelledby="orbitaTelegramTitle">' +
      '<div class="orbita-telegram-heading"><div><h3 id="orbitaTelegramTitle">Recebidos do Telegram</h3>' +
      '<p class="small muted">Prévia segura da sua nuvem — sem importar ou alterar registros neste aparelho.</p></div>' +
      '<button type="button" class="btn sm" id="orbitaTelegramRefresh">Atualizar</button></div>' +
      '<p class="small" id="orbitaTelegramStatus" role="status" aria-live="polite">Aguardando autenticação...</p>' +
      '<ul class="orbita-telegram-list" id="orbitaTelegramList" aria-label="Últimos registros do Telegram"></ul></div>' +
      '<div class="actions orbita-cloud-actions"><button id="orbitaCloudSync" type="button" class="btn primary">Conciliar registros agora</button></div>';
    parent.append(card);
    el('orbitaCloudSync').addEventListener('click', sync);
    el('orbitaTelegramRefresh').addEventListener('click', inspectTelegram);
    mode(allowed ? 'Aguardando autenticação para sincronizar.' : 'O projeto exclusivo do ORBITA ainda não está configurado.');
    renderButtons();
    auth.onReady(() => {
      const identity = auth.getUser();
      accountId = identity.id;
      setText('orbitaCloudAccount', 'Conectado como ' + (identity.email || identity.id));
      mode('Conexão pronta. Os registros locais não foram enviados automaticamente.');
      renderButtons();
      inspectRemote();
      inspectTelegram();
    });
    window.addEventListener('orbita:local-change', () => {
      if (auth.isAuthenticated()) {
        dirty = true;
        mode('Alterações locais pendentes. Clique em “Conciliar registros agora”.');
        const localCount = (() => { try { return localData().records.length } catch (_) { return null } })();
        dashboardStatus((localCount === null ? 'Registros locais inconsistentes' :
          localCount + ' registro(s) neste dispositivo') +
          ' · alterações ainda não conciliadas' +
          (lastRemoteCount === null ? '' : ' · última consulta: ' + lastRemoteCount + ' na nuvem'));
      }
    });
  }
  buildBridge();
  buildPanel();
})();
