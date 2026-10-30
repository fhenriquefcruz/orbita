/* ORBITA 3.15 — Journal de transações locais: exclusões e conciliações recuperáveis.
 * Chaves existentes permanecem legíveis; não armazena tokens, senhas ou chat.
 */
(function (root) {
  'use strict';
  const STORE = 'orbita_v12_local';
  const TOMBSTONES = 'orbita_cloud_tombstones_v1';
  const BINDING = 'orbita_cloud_binding_v1';
  const JOURNAL = 'orbita_local_txn_v1';
  const MAX_BYTES = 8 * 1024 * 1024;
  let startupError = '';

  function validRaw(raw) {
    return raw === null || (typeof raw === 'string' && raw.length <= MAX_BYTES);
  }
  function readJournal(storage) {
    const raw = storage.getItem(JOURNAL);
    if (raw === null) return null;
    if (!validRaw(raw)) throw Error('Journal local muito grande');
    let entry;
    try { entry = JSON.parse(raw); } catch (_) { throw Error('Journal local danificado'); }
    if (!entry || entry.version !== 1 || typeof entry.owner !== 'string' ||
        !/^[a-f0-9-]{36}$/i.test(entry.owner) || !entry.before || !entry.after ||
        !validRaw(entry.before.store) || !validRaw(entry.before.tombstones) ||
        !validRaw(entry.after.store) || !validRaw(entry.after.tombstones)) {
      throw Error('Journal local incompatível: não sobrescreva seus dados');
    }
    return entry;
  }
  function restoreKey(storage, key, value) {
    if (value === null) storage.removeItem(key);
    else storage.setItem(key, value);
  }
  function recover(storage) {
    const journal = readJournal(storage);
    if (!journal) return false;
    const binding = storage.getItem(BINDING);
    if (binding !== journal.owner)
      throw Error('Operação interrompida pertence a outra conta: recuperação bloqueada');
    // Não sobrescrever alterações de uma segunda aba que não correspondam à transação.
    const present = {
      store: storage.getItem(STORE), tombstones: storage.getItem(TOMBSTONES)
    };
    for (const prop of ['store', 'tombstones']) {
      if (present[prop] !== journal.before[prop] && present[prop] !== journal.after[prop]) {
        throw Error('Dados locais mudaram durante a recuperação. Preserve o backup.');
      }
    }
    restoreKey(storage, STORE, journal.before.store);
    restoreKey(storage, TOMBSTONES, journal.before.tombstones);
    storage.removeItem(JOURNAL);
    return true;
  }
  // Both cloud sync and deletion modify two independent localStorage keys.
  // A write-ahead journal makes interrupted writes recoverable on next startup.
  function commitPair(storage, owner, nextStore, nextTombstones, expected, action) {
    if (startupError) throw Error(startupError);
    if (readJournal(storage)) throw Error('Recupere a operação interrompida antes de continuar');
    if (typeof owner !== 'string' || storage.getItem(BINDING) !== owner)
      throw Error('Conta não vinculada ao armazenamento deste dispositivo');
    if (!validRaw(nextStore) || !validRaw(nextTombstones) ||
        nextStore === null || nextTombstones === null)
      throw Error('Alterações locais incompatíveis');
    const before = {
      store: storage.getItem(STORE), tombstones: storage.getItem(TOMBSTONES)
    };
    if (!validRaw(before.store) || !validRaw(before.tombstones))
      throw Error('Dados locais acima do limite seguro');
    if (expected) {
      if (!['store', 'tombstones', 'binding'].every(key =>
          Object.prototype.hasOwnProperty.call(expected, key)))
        throw Error('Snapshot anterior incompleto; operação bloqueada');
      if (before.store !== expected.store ||
          before.tombstones !== expected.tombstones ||
          storage.getItem(BINDING) !== expected.binding)
        throw Error('Os dados locais mudaram durante a conciliação; recarregue antes de alterar');
    }
    const after = {store: nextStore, tombstones: nextTombstones};
    const entry = {version:1, owner, before, after};
    storage.setItem(JOURNAL, JSON.stringify(entry));
    try {
      storage.setItem(STORE, nextStore);
      storage.setItem(TOMBSTONES, nextTombstones);
      storage.removeItem(JOURNAL);
    } catch (_) {
      try {
        recover(storage);
      } catch (_) {
        throw Error('Falha ao concluir ou reverter ' + action +
          '. Não sincronize; preserve o backup.');
      }
      throw Error('Armazenamento indisponível. ' + action +
        ' cancelada sem alterar os registros locais.');
    }
  }
  function commitDeletion(storage, owner, nextStore, nextTombstones) {
    return commitPair(storage, owner, nextStore, nextTombstones, null, 'Exclusão');
  }
  function commitSync(storage, owner, nextStore, nextTombstones, expected) {
    if (!expected || typeof expected !== 'object')
      throw Error('Snapshot da conciliação obrigatório');
    return commitPair(storage, owner, nextStore, nextTombstones, expected, 'Conciliação');
  }
  const TRACKED_KEYS = new Set([STORE, TOMBSTONES, BINDING, JOURNAL]);
  // A snapshot is captured after initial hydration and after this tab's successful writes.
  // A different tab may not overwrite an older local copy silently.
  function createTabGuard(storage) {
    const snapshot = () => ({
      store: storage.getItem(STORE),
      tombstones: storage.getItem(TOMBSTONES),
      binding: storage.getItem(BINDING)
    });
    let expected = snapshot();
    let changedElsewhere = false;
    function assertCurrent() {
      if (changedElsewhere) throw Error(
        'Outra aba modificou a memória ORBITA. Recarregue esta aba antes de salvar.');
      if (readJournal(storage)) throw Error(
        'Há uma exclusão interrompida. Recarregue o ORBITA para recuperação.');
      const current = snapshot();
      if (Object.keys(expected).some(key => expected[key] !== current[key]))
        throw Error('Os dados locais mudaram em outra aba. Recarregue antes de alterar.');
    }
    function markExternalChange(key) {
      if (key === null || TRACKED_KEYS.has(key)) changedElsewhere = true;
    }
    return Object.freeze({
      assertCurrent,
      markExternalChange,
      refresh() {
        if (readJournal(storage)) throw Error(
          'Há uma exclusão interrompida. Recarregue o ORBITA para recuperação.');
        expected = snapshot();
        changedElsewhere = false;
      },
      isStale() {
        const current = snapshot();
        return changedElsewhere || Object.keys(expected).some(key => expected[key] !== current[key]);
      }
    });
  }
  const api = Object.freeze({
    createTabGuard,
    commitDeletion,
    commitSync,
    recover,
    assertReady() {
      if (startupError) throw Error(startupError);
    },
    journalKey: JOURNAL
  });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root && root.localStorage) {
    root.OrbitaLocalIntegrity = api;
    try { recover(root.localStorage); }
    catch (error) { startupError = 'Armazenamento local exige recuperação: ' + error.message; }
  }
})(typeof window === 'undefined' ? null : window);
