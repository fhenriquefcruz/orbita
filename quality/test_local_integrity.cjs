'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {commitDeletion, recover, journalKey} = require('../docs/local-integrity.js');
const OWNER = '11111111-1111-4111-8111-111111111111';
const STORE = 'orbita_v12_local';
const TOMBS = 'orbita_cloud_tombstones_v1';
const BINDING = 'orbita_cloud_binding_v1';
const BEFORE = JSON.stringify({schema_version:1,records:[{id:'one',title:'Original'}],audit:[]});
const AFTER = JSON.stringify({schema_version:1,records:[],audit:[]});
const DELETE = JSON.stringify({one:'2026-10-24T20:30:00Z'});

class FakeStorage {
  constructor(initial = {}) { this.data = new Map(Object.entries(initial)); this.fail = null; }
  getItem(key) { return this.data.has(key) ? this.data.get(key) : null; }
  setItem(key, value) {
    if (this.fail?.(key, 'set')) throw new Error('QuotaExceededError simulado');
    this.data.set(key,String(value));
  }
  removeItem(key) {
    if (this.fail?.(key, 'remove')) throw new Error('Falha simulada');
    this.data.delete(key);
  }
}
function storage() { return new FakeStorage({[STORE]:BEFORE,[TOMBS]:'{}',[BINDING]:OWNER}); }

test('exclusão bem-sucedida guarda lista e tombstone e limpa o journal', () => {
  const s=storage();
  commitDeletion(s,OWNER,AFTER,DELETE);
  assert.equal(s.getItem(STORE),AFTER);
  assert.equal(s.getItem(TOMBS),DELETE);
  assert.equal(s.getItem(journalKey),null);
  assert.equal(recover(s),false);
});
test('falha no tombstone reverte a lista e remove o journal', () => {
  const s=storage();let first=true;
  s.fail=(key,op) => key===TOMBS && op==='set' && first && !(first=false);
  // A função acima lança somente na primeira tentativa de escrita.
  assert.throws(()=>commitDeletion(s,OWNER,AFTER,DELETE),/Exclusão cancelada/);
  assert.equal(s.getItem(STORE),BEFORE);
  assert.equal(s.getItem(TOMBS),'{}');
  assert.equal(s.getItem(journalKey),null);
});
test('falha no segundo passo e na reversão deixa journal recuperável', () => {
  const s=storage();let badTombstone=true,badRollback=true;
  s.fail=(key,op) => {
    if(key===TOMBS && op==='set' && badTombstone) {badTombstone=false;return true}
    if(key===STORE && op==='set' && badRollback && s.getItem(STORE)===AFTER) {
      badRollback=false;return true
    }
    return false;
  };
  assert.throws(()=>commitDeletion(s,OWNER,AFTER,DELETE),/Não sincronize/);
  assert.notEqual(s.getItem(journalKey),null);
  s.fail=null;
  assert.equal(recover(s),true);
  assert.equal(s.getItem(STORE),BEFORE);
  assert.equal(s.getItem(TOMBS),'{}');
  assert.equal(s.getItem(journalKey),null);
});
test('queda após gravar lista é recuperada na abertura', () => {
  const s=storage();
  s.setItem(journalKey,JSON.stringify({
    version:1,owner:OWNER,
    before:{store:BEFORE,tombstones:'{}'},
    after:{store:AFTER,tombstones:DELETE}
  }));
  s.setItem(STORE,AFTER);
  assert.equal(recover(s),true);
  assert.equal(s.getItem(STORE),BEFORE);
  assert.equal(s.getItem(TOMBS),'{}');
  assert.equal(s.getItem(journalKey),null);
});
test('journal órfão ou alterado por outra aba bloqueia sobrescrita silenciosa',()=>{
  const s=storage();
  s.setItem(journalKey,JSON.stringify({
    version:1,owner:OWNER,
    before:{store:BEFORE,tombstones:'{}'},
    after:{store:AFTER,tombstones:DELETE}
  }));
  s.setItem(STORE,JSON.stringify({schema_version:1,records:[{id:'different'}]}));
  assert.throws(()=>recover(s),/mudaram/);
  assert.notEqual(s.getItem(journalKey),null);
});
test('não efetua exclusão de dados vinculados a outra conta',()=>{
  const s=storage();
  assert.throws(()=>commitDeletion(s,'22222222-2222-4222-8222-222222222222',AFTER,DELETE),/Conta não vinculada/);
  assert.equal(s.getItem(journalKey),null);
  s.setItem(journalKey,JSON.stringify({
    version:1,owner:'22222222-2222-4222-8222-222222222222',
    before:{store:BEFORE,tombstones:'{}'},
    after:{store:AFTER,tombstones:DELETE}
  }));
  assert.throws(()=>recover(s),/outra conta/);
});
test('journal danificado não é apagado automaticamente',()=>{
  const s=storage();s.setItem(journalKey,'{invalid');
  assert.throws(()=>recover(s),/danificado/);
  assert.equal(s.getItem(journalKey),'{invalid');
});
