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
  let accountId = '', busy = false, dirty = false;
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
      const search = '?select=id,payload,updated_at&order=updated_at.desc&limit=500&offset=' + offset;
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
  }
  async function sync() {
    if (!auth.isAuthenticated() || busy) return;
    accountId = auth.getUser().id;
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
  function buildPanel() {
    const parent = document.getElementById('view-data');
    if (!parent) return;
    const card = document.createElement('section');
    card.className = 'card orbita-cloud-panel';
    card.innerHTML = '<div class="sectionhead"><h2>Memória central</h2><span class="chip">SUPABASE · RLS</span></div>' +
      '<p class="small muted">Sua conta está autenticada. Dados deste navegador só serão enviados após confirmação da conciliação. O Telegram poderá compartilhar a base quando o backend estiver configurado.</p>' +
      '<p class="small" id="orbitaCloudAccount"></p>' +
      '<p class="small" id="orbitaCloudStatus" role="status" aria-live="polite"></p>' +
      '<div class="actions orbita-cloud-actions"><button id="orbitaCloudSync" type="button" class="btn primary">Conciliar registros agora</button></div>';
    parent.append(card);
    el('orbitaCloudSync').addEventListener('click', sync);
    mode(allowed ? 'Aguardando autenticação para sincronizar.' : 'O projeto exclusivo do ORBITA ainda não está configurado.');
    renderButtons();
    auth.onReady(() => {
      const identity = auth.getUser();
      accountId = identity.id;
      setText('orbitaCloudAccount', 'Conectado como ' + (identity.email || identity.id));
      mode('Conexão pronta. Os registros locais não foram enviados automaticamente.');
      renderButtons();
    });
    window.addEventListener('orbita:local-change', () => {
      if (auth.isAuthenticated()) {
        dirty = true;
        mode('Alterações locais pendentes. Clique em “Conciliar registros agora”.');
      }
    });
  }
  buildPanel();
})();
