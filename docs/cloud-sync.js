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
  let accountId = '', busy = false, dirty = false, inspecting = false, previewing = false;
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
    // Preserva também exclusões locais; caso contrário uma restauração poderia ressuscitar itens.
    const blob = new Blob([JSON.stringify({...snapshot, tombstones: tombstones(),
      exported_at: new Date().toISOString()}, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'orbita-backup-antes-sincronizacao-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 15000);
  }
  function renderButtons() {
    if (el('orbitaCloudSync')) el('orbitaCloudSync').disabled = busy || !auth.isAuthenticated();
    if (el('orbitaCloudInspect')) el('orbitaCloudInspect').disabled = inspecting || busy || !auth.isAuthenticated();
    if (el('orbitaCloudPreview')) el('orbitaCloudPreview').disabled = previewing || busy || !auth.isAuthenticated();
    if (el('orbitaCloudImport')) el('orbitaCloudImport').disabled = previewing || busy || !auth.isAuthenticated();
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
  function summaryForPlan(plan) {
    const s = plan.stats;
    return s.fromCloud + ' a receber, ' + s.replacedByCloud +
      ' atualização(ões) da nuvem, ' + s.create + ' nova(s) a enviar, ' +
      s.update + ' atualização(ões) a enviar, ' + s.delete +
      ' exclusão(ões), ' + s.conflicts + ' conflito(s).';
  }
  function displayPreview(plan) {
    const message = el('orbitaCloudPreviewStatus');
    if (!message) return;
    if (plan.conflicts.length) {
      message.textContent = 'Conflitos detectados (' + plan.conflicts.length +
        '): mesmos registros com revisões ambíguas. Nenhuma gravação é permitida; ' +
        'revise os dados e preserve seus backups. ' + summaryForPlan(plan);
    } else {
      message.textContent = 'Simulação segura: ' + summaryForPlan(plan) +
        ' Total após conciliação: ' + plan.stats.after +
        '. Ainda não foi gravado nada.';
    }
  }
  async function inspectPlan() {
    if (!auth.isAuthenticated() || busy || previewing) return;
    const owner = auth.getUser().id;
    previewing = true;
    renderButtons();
    setText('orbitaCloudPreviewStatus', 'Comparando dados sem gravar...');
    try {
      const local = localData(), deleted = tombstones();
      const remote = await loadCloud();
      if (!sameAccount(owner)) return;
      displayPreview(core.reconcile(local.records, remote, deleted));
    } catch (_) {
      if (sameAccount(owner)) setText('orbitaCloudPreviewStatus',
        'A simulação não pôde ser concluída. Os dados locais não foram alterados.');
    } finally {
      previewing = false;
      renderButtons();
    }
  }
  async function importCloudOnly() {
    if (!auth.isAuthenticated() || busy || previewing) return;
    const owner = auth.getUser().id;
    busy = true;
    renderButtons();
    mode('Preparando importação apenas da nuvem; nenhuma gravação será enviada ao servidor...');
    try {
      const originalStore = localStorage.getItem(STORE);
      const originalTombstones = localStorage.getItem(TOMBSTONES);
      const originalBinding = localStorage.getItem(BINDING);
      const snapshot = localData();
      const pendingDeletions = tombstones();
      const remote = await loadCloud();
      if (!sameAccount(owner)) throw Error('A conta mudou durante a consulta');
      const plan = core.planCloudImport(snapshot.records, remote, pendingDeletions);
      const s = plan.stats;
      const detail = s.imported + ' novo(s) para este dispositivo; ' +
        s.alreadyLocal + ' já existente(s); ' + s.divergent + ' diferente(s), ' +
        s.locallyDeleted + ' excluído(s) localmente e ' + s.invalid +
        ' inválido(s), todos preservados sem sobrescrita.';
      setText('orbitaCloudImportStatus', 'Resultado da comparação: ' + detail);
      if (!s.imported) {
        mode('Nenhum registro novo a importar. A nuvem e o navegador não foram alterados.');
        return;
      }
      if (!window.confirm('ORBITA — trazer apenas da nuvem\n\n' + detail +
        '\n\nEsta ação não escreve nem exclui registros no Supabase. Será exigido um backup antes de alterar este dispositivo. Continuar?')) {
        mode('Importação cancelada sem alterações.');
        return;
      }
      saveBackup(snapshot);
      if (!window.confirm('O download do backup local foi iniciado.\n\n' +
        'CONFIRME que o arquivo foi realmente salvo no dispositivo antes de importar. ' +
        'Se o download foi bloqueado, escolha Cancelar.\n\nBackup salvo?')) {
        mode('Importação cancelada. Confira primeiro o arquivo de backup.');
        return;
      }
      if (!sameAccount(owner) ||
          localStorage.getItem(STORE) !== originalStore ||
          localStorage.getItem(TOMBSTONES) !== originalTombstones ||
          localStorage.getItem(BINDING) !== originalBinding) {
        throw Error('A conta ou os registros locais mudaram. Refaça a importação.');
      }
      // Única escrita: armazenamento local do navegador. Não há POST/PATCH/DELETE.
      localStorage.setItem(STORE, JSON.stringify({...snapshot, records:plan.records}));
      localStorage.setItem(BINDING, owner);
      mode(s.imported + ' registro(s) importado(s) somente neste dispositivo. Atualizando o painel...');
      setTimeout(() => location.reload(), 500);
    } catch (err) {
      mode('Importação não concluída: ' + err.message + '. Nenhuma gravação foi enviada à nuvem.');
    } finally {
      busy = false;
      renderButtons();
    }
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
      displayPreview(plan);
      if (plan.conflicts.length) throw Error(
        'Existem ' + plan.conflicts.length + ' revisão(ões) conflitantes; nenhuma gravação foi iniciada');
      const versions = new Map(remote.map(row => [row.id, row.updated_at]));
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
        const now = item.updated_at || new Date().toISOString();
        const oldVersion = versions.get(item.id);
        let result;
        if (versions.has(item.id)) {
          if (!oldVersion || !Number.isFinite(Date.parse(oldVersion))) {
            throw Error('Revisão remota indisponível; operação interrompida');
          }
          // PATCH condicional: se Telegram/outra aba editou desde o GET, retorna [].
          const params = new URLSearchParams({
            id:'eq.' + item.id, updated_at:'eq.' + oldVersion
          });
          result = await request('/rest/v1/orbita_records?' + params.toString(),
            'PATCH', {payload:item, updated_at:now}, {prefer:'return=representation'});
        } else {
          // Nunca fazer merge-duplicates de criação: colisão de ID deve falhar.
          result = await request('/rest/v1/orbita_records', 'POST', {
            id:item.id, user_id:operationAccount, payload:item,
            created_at:item.created_at || now, updated_at:now
          }, {prefer:'return=representation'});
        }
        if (!Array.isArray(result) || result.length !== 1) {
          throw Error('Um registro mudou na nuvem durante a gravação. Interrompido para evitar sobrescrita.');
        }
      }
      for (const id of plan.deletions) {
        if (!sameAccount(operationAccount)) throw Error('A conta mudou durante as exclusões.');
        const oldVersion = versions.get(id);
        if (!oldVersion || !Number.isFinite(Date.parse(oldVersion))) {
          throw Error('Revisão da exclusão indisponível; operação interrompida');
        }
        const params = new URLSearchParams({
          id:'eq.' + id, updated_at:'eq.' + oldVersion
        });
        const result = await request('/rest/v1/orbita_records?' + params.toString(),
          'DELETE', undefined, {prefer:'return=representation'});
        if (!Array.isArray(result) || result.length !== 1) {
          throw Error('A exclusão foi cancelada: o registro remoto mudou desde a comparação.');
        }
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
  // Central do Telegram: consulta por iniciativa do usuário, sem sincronizar ou mutar dados.
  let telegramInspecting = false;
  let telegramRows = [];
  let telegramAccount = '';
  const telegramStatuses = Object.freeze({
    a_fazer: 'A fazer', em_andamento: 'Em andamento',
    concluida: 'Concluída', cancelada: 'Cancelada', arquivada: 'Arquivada'
  });
  function telegramNode(tag, className, content) {
    const node = document.createElement(tag);
    node.className = className;
    node.textContent = content;
    return node;
  }
  function normalized(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
  }
  function resetTelegramMetrics() {
    for (const id of ['orbitaTelegramOpen', 'orbitaTelegramDone', 'orbitaTelegramIdeas']) {
      setText(id, '—');
    }
  }
  function renderTelegram() {
    if (!sameAccount(telegramAccount)) return;
    const list = el('orbitaTelegramList');
    const status = el('orbitaTelegramStatus');
    if (!list || !status) return;
    const tasks = telegramRows.filter(row => row.payload.type === 'tarefa');
    const open = tasks.filter(row => ['a_fazer', 'em_andamento'].includes(row.payload.status)).length;
    const done = tasks.filter(row => row.payload.status === 'concluida').length;
    const ideas = telegramRows.filter(row => row.payload.type === 'ideia').length;
    setText('orbitaTelegramOpen', String(open));
    setText('orbitaTelegramDone', String(done));
    setText('orbitaTelegramIdeas', String(ideas));
    const selection = el('orbitaTelegramFilter')?.value || 'all';
    const search = normalized(el('orbitaTelegramSearch')?.value.trim());
    const visible = telegramRows.filter(row => {
      const p = row.payload;
      const matchFilter = selection === 'all' ||
        (selection === 'open' && p.type === 'tarefa' && ['a_fazer','em_andamento'].includes(p.status)) ||
        (selection === 'done' && p.type === 'tarefa' && p.status === 'concluida') ||
        (selection === 'ideas' && p.type === 'ideia');
      return matchFilter && (!search || normalized(p.title).includes(search));
    });
    list.replaceChildren();
    status.textContent = 'Exibindo ' + visible.length + ' de ' + telegramRows.length +
      ' registro(s) consultado(s)' + (telegramRows.length >= 100 ? ' · limite de 100 itens recentes' : '') +
      '. Apenas leitura; nenhuma alteração local.';
    if (!visible.length) {
      list.append(telegramNode('li', 'orbita-telegram-empty',
        telegramRows.length ? 'Nenhum item corresponde aos filtros.' :
          'Nenhum registro do Telegram nesta conta. Confira se ela é a mesma vinculada ao bot.'));
      return;
    }
    for (const row of visible) {
      const p = row.payload;
      const item = telegramNode('li', 'orbita-telegram-item', '');
      const info = telegramNode('div', 'orbita-telegram-item-info', '');
      const title = String(p.title || 'Sem título');
      info.append(telegramNode('strong', '', title));
      const kind = p.type === 'ideia' ? 'Ideia' : p.type === 'tarefa' ? 'Tarefa' : 'Registro';
      const priority = /^P[0-3]$/.test(p.priority || '') ? ' · ' + p.priority : '';
      const sequence = Number.isSafeInteger(row.telegram_seq) && row.telegram_seq > 0 ?
        ' · #' + row.telegram_seq : '';
      const date = new Date(row.updated_at || p.updated_at || '');
      const dateLabel = Number.isFinite(date.valueOf()) ?
        ' · ' + new Intl.DateTimeFormat('pt-BR', {day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}).format(date) : '';
      info.append(telegramNode('small', '', kind + priority + sequence + dateLabel));
      const state = telegramStatuses[p.status] || 'Sem situação';
      const stateClass = p.status === 'concluida' ? ' is-done' :
        p.status === 'em_andamento' ? ' is-progress' :
        ['cancelada','arquivada'].includes(p.status) ? ' is-muted' : '';
      const label = telegramNode('span', 'orbita-telegram-state' + stateClass, state);
      item.append(info, label);
      list.append(item);
    }
  }
  async function inspectTelegram() {
    if (!auth.isAuthenticated() || busy || telegramInspecting) return;
    const viewingAccount = auth.getUser().id;
    const status = el('orbitaTelegramStatus');
    const list = el('orbitaTelegramList');
    const refresh = el('orbitaTelegramRefresh');
    if (!status || !list || !refresh) return;
    telegramInspecting = true;
    telegramAccount = viewingAccount;
    telegramRows = [];
    refresh.disabled = true;
    status.textContent = 'Consultando atividades do Telegram na sua conta...';
    list.replaceChildren();
    resetTelegramMetrics();
    try {
      // Retorna apenas registros acessíveis via JWT Auth + políticas RLS.
      const query = new URLSearchParams();
      query.set('select', 'id,telegram_seq,payload,updated_at');
      query.set('payload->>source', 'eq.Telegram ORBITA');
      query.set('order', 'updated_at.desc,id.asc');
      query.set('limit', '100');
      const rows = await request('/rest/v1/orbita_records?' + query.toString());
      if (!sameAccount(viewingAccount)) return;
      if (!Array.isArray(rows)) throw Error('Resposta inesperada do servidor');
      telegramRows = rows.filter(row => row && row.payload &&
        row.payload.id === row.id && row.payload.source === 'Telegram ORBITA');
      renderTelegram();
    } catch (_) {
      if (sameAccount(viewingAccount)) {
        telegramRows = [];
        list.replaceChildren();
        resetTelegramMetrics();
        status.textContent = 'Não foi possível consultar as atividades do Telegram. Os dados locais não foram alterados.';
      }
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
      '<div class="orbita-telegram-heading"><div><h3 id="orbitaTelegramTitle">Atividades do Telegram</h3>' +
      '<p class="small muted">Tarefas e ideias em nuvem, sem importar ou alterar os dados deste dispositivo.</p></div>' +
      '<button type="button" class="btn sm" id="orbitaTelegramRefresh">Atualizar</button></div>' +
      '<div class="orbita-telegram-metrics" aria-label="Indicadores dos últimos 100 registros do Telegram">' +
      '<div><span id="orbitaTelegramOpen">—</span><small>Em aberto</small></div>' +
      '<div><span id="orbitaTelegramDone">—</span><small>Concluídas</small></div>' +
      '<div><span id="orbitaTelegramIdeas">—</span><small>Ideias</small></div></div>' +
      '<div class="orbita-telegram-filters">' +
      '<label><span>Situação</span><select class="input" id="orbitaTelegramFilter">' +
      '<option value="all">Todas</option><option value="open">Tarefas em aberto</option>' +
      '<option value="done">Tarefas concluídas</option><option value="ideas">Ideias</option></select></label>' +
      '<label><span>Pesquisar título</span><input class="input" type="search" id="orbitaTelegramSearch" maxlength="100" placeholder="Buscar na nuvem"></label></div>' +
      '<p class="small" id="orbitaTelegramStatus" role="status" aria-live="polite">Aguardando autenticação...</p>' +
      '<ul class="orbita-telegram-list" id="orbitaTelegramList" aria-label="Atividades recentes do Telegram"></ul></div>' +
      '<div class="orbita-cloud-preflight" aria-label="Prévia da conciliação manual">' +
      '<strong>Antes de sincronizar</strong>' +
      '<p class="small muted">Confira quantos registros serão recebidos, enviados ou excluídos. Esta análise é somente de leitura.</p>' +
      '<p class="small" id="orbitaCloudPreviewStatus" role="status" aria-live="polite">Nenhuma simulação executada.</p></div>' +
      '<p class="small" id="orbitaCloudImportStatus" role="status" aria-live="polite"></p>' +
      '<div class="actions orbita-cloud-actions">' +
      '<button id="orbitaCloudPreview" type="button" class="btn">Simular sem alterar</button>' +
      '<button id="orbitaCloudImport" type="button" class="btn">Trazer da nuvem</button>' +
      '<button id="orbitaCloudSync" type="button" class="btn primary">Conciliar registros agora</button></div>';
    parent.append(card);
    el('orbitaCloudSync').addEventListener('click', sync);
    el('orbitaCloudPreview').addEventListener('click', inspectPlan);
    el('orbitaCloudImport').addEventListener('click', importCloudOnly);
    el('orbitaTelegramRefresh').addEventListener('click', inspectTelegram);
    el('orbitaTelegramFilter').addEventListener('change', renderTelegram);
    el('orbitaTelegramSearch').addEventListener('input', renderTelegram);
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
