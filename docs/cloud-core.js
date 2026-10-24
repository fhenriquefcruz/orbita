/* ORBITA 3.0 | Funções puras de conciliação de registros. Nenhuma credencial neste arquivo. */
(function (root) {
  'use strict';
  const stamp = x => {
    const n = Date.parse(x || '');
    return Number.isFinite(n) ? n : 0;
  };
  function reconcile(local, cloudRows, tombstones = {}) {
    const mine = new Map();
    const remote = new Map();
    for (const x of local) if (x && typeof x.id === 'string' && x.id.length <= 128) mine.set(x.id, x);
    for (const row of cloudRows) if (row && typeof row.id === 'string' && row.payload && row.payload.id === row.id)
      remote.set(row.id, row.payload);
    const merged = new Map(mine);
    const upserts = [];
    const deletions = [];
    const clearTombstones = [];
    const supersededDeletions = new Set();
    for (const [id, other] of remote) {
      const deletedAt = stamp(tombstones[id]);
      if (deletedAt && deletedAt >= stamp(other.updated_at)) {
        merged.delete(id);
        deletions.push(id);
        continue;
      }
      if (tombstones[id]) { clearTombstones.push(id); supersededDeletions.add(id); }
      const original = mine.get(id);
      if (!original || stamp(other.updated_at) >= stamp(original.updated_at)) merged.set(id, other);
    }
    for (const [id, item] of mine) {
      if (tombstones[id]) { if (!supersededDeletions.has(id)) merged.delete(id); continue; }
      const r = remote.get(id);
      if (!r || stamp(item.updated_at) > stamp(r.updated_at)) upserts.push(item);
    }
    for (const id of Object.keys(tombstones)) if (!remote.has(id)) clearTombstones.push(id);
    return {records: Array.from(merged.values()), upserts, deletions, clearTombstones};
  }
  const api = Object.freeze({reconcile, stamp});
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.OrbitaCloudCore = api;
})(typeof window === 'undefined' ? null : window);
