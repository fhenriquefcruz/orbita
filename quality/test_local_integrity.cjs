'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {commitDeletion, commitSync, recover, journalKey, createTabGuard} = require('../docs/local-integrity.js');
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

test('duas abas: gravar a partir de snapshot antigo é bloqueado sem sobrescrever',()=>{
  const s=storage();
  const first=createTabGuard(s),second=createTabGuard(s);
  first.assertCurrent();
  second.assertCurrent();
  s.setItem(STORE,AFTER);
  first.refresh();
  assert.throws(()=>second.assertCurrent(),/mudaram em outra aba/);
  assert.equal(s.getItem(STORE),AFTER);
});
test('notificação entre abas bloqueia escrita, inclusive se o valor voltou ao anterior',()=>{
  const s=storage(), guard=createTabGuard(s);
  guard.markExternalChange(STORE);
  assert.throws(()=>guard.assertCurrent(),/Outra aba/);
  guard.refresh();
  guard.assertCurrent();
});
test('chaves não pertencentes à memória não interrompem o cadastro',()=>{
  const s=storage(), guard=createTabGuard(s);
  guard.markExternalChange('orbita_theme');
  guard.assertCurrent();
});
test('journal pendente impede escrita por outra aba',()=>{
  const s=storage(), guard=createTabGuard(s);
  s.setItem(journalKey,JSON.stringify({
    version:1,owner:OWNER,
    before:{store:BEFORE,tombstones:'{}'},
    after:{store:AFTER,tombstones:DELETE}
  }));
  assert.throws(()=>guard.assertCurrent(),/exclusão interrompida/);
  assert.throws(()=>guard.refresh(),/exclusão interrompida/);
});
test('alteração de titular invalida o snapshot existente',()=>{
  const s=storage(), guard=createTabGuard(s);
  s.setItem(BINDING,'22222222-2222-4222-8222-222222222222');
  assert.throws(()=>guard.assertCurrent(),/mudaram em outra aba/);
  assert.equal(s.getItem(STORE),BEFORE);
});
test('após escrita válida e atualização de snapshot, a aba pode continuar editando',()=>{
  const s=storage(), guard=createTabGuard(s);
  guard.assertCurrent();
  s.setItem(STORE,AFTER);
  guard.refresh();
  guard.assertCurrent();
  assert.equal(guard.isStale(),false);
});

function expectation(s) {
  return {store:s.getItem(STORE),tombstones:s.getItem(TOMBS),binding:s.getItem(BINDING)};
}

test('conciliação salva registros e exclusões juntos e remove journal', () => {
  const s=storage();
  commitSync(s,OWNER,AFTER,DELETE,expectation(s));
  assert.equal(s.getItem(STORE),AFTER);
  assert.equal(s.getItem(TOMBS),DELETE);
  assert.equal(s.getItem(journalKey),null);
});

test('conciliação exige snapshot de registros, exclusões e identidade', () => {
  const s=storage();
  assert.throws(()=>commitSync(s,OWNER,AFTER,DELETE),/Snapshot da conciliação obrigatório/);
  assert.throws(()=>commitSync(s,OWNER,AFTER,DELETE,{store:BEFORE}),/Snapshot anterior incompleto/);
  assert.equal(s.getItem(journalKey),null);
  assert.equal(s.getItem(STORE),BEFORE);
});

test('conciliação rejeita dados alterados em outra aba antes da gravação', () => {
  const s=storage(), before=expectation(s);
  s.setItem(TOMBS,DELETE);
  assert.throws(()=>commitSync(s,OWNER,AFTER,'{}',before),/mudaram durante a conciliação/);
  assert.equal(s.getItem(journalKey),null);
  assert.equal(s.getItem(STORE),BEFORE);
  assert.equal(s.getItem(TOMBS),DELETE);
});

test('falha na segunda chave durante conciliação restaura o par anterior', () => {
  const s=storage(), before=expectation(s);
  let failing=true;
  s.fail=(key,op)=>key===TOMBS && op==='set' && failing && (failing=false,true);
  assert.throws(()=>commitSync(s,OWNER,AFTER,DELETE,before),/Conciliação cancelada/);
  assert.equal(s.getItem(STORE),BEFORE);
  assert.equal(s.getItem(TOMBS),'{}');
  assert.equal(s.getItem(journalKey),null);
});

test('falha irrecuperável na conciliação conserva journal para próxima abertura', () => {
  const s=storage(), before=expectation(s);
  let failedTomb=false,failedRollback=false;
  s.fail=(key,op)=>{
    if(key===TOMBS && op==='set' && !failedTomb){failedTomb=true;return true;}
    if(key===STORE && op==='set' && s.getItem(STORE)===AFTER && !failedRollback){
      failedRollback=true;return true;
    }
    return false;
  };
  assert.throws(()=>commitSync(s,OWNER,AFTER,DELETE,before),/Não sincronize/);
  assert.notEqual(s.getItem(journalKey),null);
  s.fail=null;
  assert.equal(recover(s),true);
  assert.equal(s.getItem(STORE),BEFORE);
  assert.equal(s.getItem(TOMBS),'{}');
});

test('queda entre gravações após conciliação deixa o estado anterior recuperável', () => {
  const s=storage();
  s.setItem(journalKey,JSON.stringify({
    version:1,owner:OWNER,before:{store:BEFORE,tombstones:'{}'},
    after:{store:AFTER,tombstones:DELETE}
  }));
  s.setItem(STORE,AFTER);
  assert.equal(recover(s),true);
  assert.equal(s.getItem(STORE),BEFORE);
  assert.equal(s.getItem(TOMBS),'{}');
});

test('não confirmar conciliação quando vinculação mudou', () => {
  const s=storage(), expected=expectation(s);
  s.setItem(BINDING,'22222222-2222-4222-8222-222222222222');
  assert.throws(()=>commitSync(s,OWNER,AFTER,DELETE,expected),/não vinculada/);
  assert.equal(s.getItem(journalKey),null);
});
