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
  const api = Object.freeze({reconcile, stamp, planCloudImport});
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.OrbitaCloudCore = api;
})(typeof window === 'undefined' ? null : window);
