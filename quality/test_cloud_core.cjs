const test = require('node:test');
const assert = require('node:assert/strict');
const {reconcile} = require('../docs/cloud-core.js');
const t0 = '2026-10-20T12:00:00-04:00', t1 = '2026-10-24T13:00:00-04:00';
const a = {id:'orb-a',title:'Local',type:'tarefa',updated_at:t0};
const b = {id:'orb-a',title:'Nuvem',type:'tarefa',updated_at:t1};
test('prefere versão nova da nuvem e preserva UUID/id', () => {
  const out=reconcile([a],[{id:b.id,payload:b}],{});
  assert.equal(out.records[0].title,'Nuvem');
  assert.equal(out.upserts.length,0);
});
test('envia atualizações locais mais recentes', () => {
  const out=reconcile([b],[{id:a.id,payload:a}],{});
  assert.deepEqual(out.upserts,[b]);
});
test('preserva dois registros de IDs diferentes', () => {
  const out=reconcile([a],[{id:'tg-1',payload:{id:'tg-1',title:'Telegram',updated_at:t1}}],{});
  assert.equal(out.records.length,2);
  assert.equal(out.upserts.length,1);
});
test('exclusão local mais nova gera tombstone no servidor', () => {
  const out=reconcile([],[{id:'orb-a',payload:a}],{'orb-a':t1});
  assert.deepEqual(out.deletions,['orb-a']);
  assert.equal(out.records.length,0);
});
test('exclusão antiga não elimina atualização nova na nuvem', () => {
  const out=reconcile([],[{id:'orb-a',payload:b}],{'orb-a':t0});
  assert.equal(out.records.length,1);
  assert.deepEqual(out.clearTombstones,['orb-a']);
});
test('exclusão antiga com cópia local não apaga atualização recente', () => {
  const out=reconcile([a],[{id:'orb-a',payload:b}],{'orb-a':t0});
  assert.equal(out.records.length,1);
  assert.equal(out.records[0].title,'Nuvem');
});
test('linhas inconsistentes na nuvem são ignoradas', () => {
  const out=reconcile([a],[{id:'x',payload:{id:'y'}}],{});
  assert.equal(out.records.length,1);
});
