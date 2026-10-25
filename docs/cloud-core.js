/* ORBITA 3.7 | Conciliação pura e conservadora: conflitos não são decididos silenciosamente. */
(function (root) {
  'use strict';
  const stamp = x => {
    const n = Date.parse(x || '');
    return Number.isFinite(n) ? n : 0;
  };
  // JSONB pode alterar a ordem das chaves. Comparação canônica não produz falsos conflitos.
  const canonical = value => {
    if (Array.isArray(value)) return value.map(canonical);
    if (value && typeof value === 'object') {
      const result = Object.create(null);
      for (const key of Object.keys(value).sort()) result[key] = canonical(value[key]);
      return result;
    }
    return value;
  };
  const samePayload = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));

  function reconcile(local, cloudRows, tombstones = {}) {
    const mine = new Map(), remote = new Map();
    for (const x of local) {
      if (x && typeof x.id === 'string' && x.id.length > 0 && x.id.length <= 128) mine.set(x.id, x);
    }
    for (const row of cloudRows) {
      if (row && typeof row.id === 'string' && row.id.length > 0 && row.payload &&
          row.payload.id === row.id) remote.set(row.id, row.payload);
    }
    const merged = new Map(mine);
    const upserts = [], deletions = [], clearTombstones = [], conflicts = [];
    const supersededDeletions = new Set();
    let fromCloud = 0, replacedByCloud = 0;
    for (const [id, other] of remote) {
      const original = mine.get(id);
      const tombstone = tombstones[id];
      const deletedAt = stamp(tombstone);
      const remoteAt = stamp(other.updated_at);
      if (tombstone && !deletedAt) {
        conflicts.push({id, reason:'invalid_deletion_time'});
        continue;
      }
      if (deletedAt && remoteAt && deletedAt >= remoteAt) {
        merged.delete(id);
        deletions.push(id);
        continue;
      }
      if (tombstone && !remoteAt) {
        conflicts.push({id, reason:'unknown_remote_time'});
        continue;
      }
      if (tombstone) {
        clearTombstones.push(id);
        supersededDeletions.add(id);
      }
      if (original && !tombstone && !samePayload(original, other)) {
        const localAt = stamp(original.updated_at);
        if (!localAt || !remoteAt || localAt === remoteAt) {
          conflicts.push({id, reason:'ambiguous_revision'});
          continue;
        }
      }
      if (!original) {
        merged.set(id, other);
        fromCloud++;
      } else if (remoteAt >= stamp(original.updated_at)) {
        if (!samePayload(original, other)) replacedByCloud++;
        merged.set(id, other);
      }
    }
    for (const [id, item] of mine) {
      if (tombstones[id]) {
        if (!supersededDeletions.has(id)) merged.delete(id);
        continue;
      }
      if (conflicts.some(c => c.id === id)) continue;
      const r = remote.get(id);
      if (!r || stamp(item.updated_at) > stamp(r.updated_at)) upserts.push(item);
    }
    for (const id of Object.keys(tombstones)) if (!remote.has(id)) clearTombstones.push(id);
    const stats = {
      local:mine.size, cloud:remote.size, after:merged.size,
      fromCloud, replacedByCloud,
      create:upserts.filter(item => !remote.has(item.id)).length,
      update:upserts.filter(item => remote.has(item.id)).length,
      delete:deletions.length, conflicts:conflicts.length
    };
    return {records:Array.from(merged.values()), upserts, deletions,
      clearTombstones, conflicts, stats};
  }
  // Importação unidirecional: nunca grava/exclui na nuvem e nunca ressuscita tombstones.
  function planCloudImport(local, cloudRows, tombstones = {}) {
    if (!Array.isArray(local) || !Array.isArray(cloudRows) ||
        !tombstones || typeof tombstones !== 'object' || Array.isArray(tombstones)) {
      throw Error('Dados inválidos para a importação segura');
    }
    const records = [...local], known = new Map();
    for (const entry of local) {
      if (entry && typeof entry.id === 'string') known.set(entry.id, entry);
    }
    const observed = new Set();
    const stats = {cloud:cloudRows.length,local:local.length,imported:0,
      alreadyLocal:0, divergent:0, locallyDeleted:0, invalid:0, duplicates:0};
    for (const row of cloudRows) {
      const item = row && row.payload;
      if (!row || typeof row.id !== 'string' || row.id.length < 1 || row.id.length > 128 ||
          !item || typeof item !== 'object' || Array.isArray(item) ||
          item.id !== row.id || typeof item.title !== 'string' ||
          item.title.trim().length < 1) {
        stats.invalid++;
        continue;
      }
      if (observed.has(row.id)) {
        stats.duplicates++;
        continue;
      }
      observed.add(row.id);
      // Um registro marcado para exclusão local não pode ser recriado por uma leitura.
      if (Object.prototype.hasOwnProperty.call(tombstones, row.id)) {
        stats.locallyDeleted++;
      } else if (known.has(row.id)) {
        if (samePayload(known.get(row.id), item)) stats.alreadyLocal++;
        else stats.divergent++;
      } else {
        records.push(item);
        known.set(row.id, item);
        stats.imported++;
      }
    }
    return {records, stats};
  }
  // Full local backup restore: validate the entire payload before allowing any write.
  function planBackupRestore(backup, current, ownerId) {
    const validObject = x => x && typeof x === 'object' && !Array.isArray(x);
    const validId = id => typeof id === 'string' && id.length > 0 && id.length <= 128;
    if (!validObject(backup) || backup.schema_version !== 1 ||
        !Array.isArray(backup.records) || backup.records.length > 5000) {
      throw Error('Formato de backup incompatível ou tamanho excedido');
    }
    if (!validObject(current) || !Array.isArray(current.records) ||
        !validObject(current.tombstones) || typeof ownerId !== 'string' || !ownerId) {
      throw Error('Estado local ou autenticação inválidos');
    }
    if (backup.account_id !== undefined &&
        (!validId(backup.account_id) || backup.account_id !== ownerId)) {
      throw Error('Este backup pertence a outra conta ORBITA');
    }
    const types = new Set(['compromisso','tarefa','projeto','pendência','ideia',
      'aprendizado','decisão','informação','oportunidade']);
    const states = new Set(['a_fazer','programada','em_execucao','em_andamento',
      'aguardando','bloqueada','concluida','cancelada','arquivada']);
    const seen = new Set();
    for (const item of backup.records) {
      if (!validObject(item) || !validId(item.id) || seen.has(item.id) ||
          typeof item.title !== 'string' || !item.title.trim() ||
          item.title.length > 1000 || !types.has(item.type) ||
          !states.has(item.status) ||
          !['P0','P1','P2','P3'].includes(item.priority)) {
        throw Error('O backup contém registro duplicado, inválido ou incompatível');
      }
      seen.add(item.id);
    }
    const hasTombstones = Object.prototype.hasOwnProperty.call(backup,'tombstones');
    const source = hasTombstones ? backup.tombstones : {};
    if (!validObject(source) || Object.keys(source).length > 10000 ||
        Object.keys(current.tombstones).length > 10000) {
      throw Error('Lista de exclusões inválida ou acima do limite');
    }
    const merged = Object.create(null);
    for (const collection of [current.tombstones, source]) {
      for (const [id, date] of Object.entries(collection)) {
        if (!validId(id) || typeof date !== 'string' || !stamp(date)) {
          throw Error('O backup ou navegador contém exclusões com datas inválidas');
        }
        if (!merged[id] || stamp(date) > stamp(merged[id])) merged[id] = date;
      }
    }
    if (backup.records.some(item => Object.prototype.hasOwnProperty.call(merged,item.id))) {
      throw Error('Há registros no backup marcados como excluídos: revise antes de restaurar');
    }
    if (backup.audit !== undefined &&
        (!Array.isArray(backup.audit) || backup.audit.length > 5000)) {
      throw Error('Trilha de auditoria do backup inválida');
    }
    if (backup.chat !== undefined &&
        (!Array.isArray(backup.chat) || backup.chat.length > 5000)) {
      throw Error('Histórico de conversa do backup inválido');
    }
    const audit = backup.audit === undefined ? (current.audit || []) : backup.audit;
    if (!Array.isArray(audit)) throw Error('Trilha local inválida');
    const chat = backup.chat === undefined ? null : backup.chat;
    return {
      records: backup.records, audit: audit.slice(0,200),
      tombstones: merged, chat: chat === null ? null : chat.slice(-100),
      summary: {
        previous: current.records.length, restored: backup.records.length,
        exclusions: Object.keys(merged).length,
        unbound: backup.account_id === undefined,
        legacy: !hasTombstones,
        chatPreserved: chat === null
      }
    };
  }
  const api = Object.freeze({reconcile, stamp, planCloudImport, planBackupRestore});
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.OrbitaCloudCore = api;
})(typeof window === 'undefined' ? null : window);
