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

test('mesmo instante com conteúdo divergente bloqueia substituição silenciosa', () => {
  const local={...a,title:'Concluída em outro aparelho',updated_at:t1};
  const nuvem={...b,updated_at:t1};
  const out=reconcile([local],[{id:local.id,payload:nuvem,updated_at:t1}],{});
  assert.equal(out.conflicts.length,1);
  assert.equal(out.conflicts[0].reason,'ambiguous_revision');
  assert.deepEqual(out.upserts,[]);
  assert.equal(out.stats.conflicts,1);
});
test('JSONB com chaves em ordem diferente não é falso conflito', () => {
  const first={id:'tg-9',title:'Mesmo conteúdo',type:'tarefa',updated_at:t1};
  const second={updated_at:t1,type:'tarefa',title:'Mesmo conteúdo',id:'tg-9'};
  const out=reconcile([first],[{id:'tg-9',payload:second,updated_at:t1}],{});
  assert.equal(out.conflicts.length,0);
  assert.equal(out.upserts.length,0);
});
test('revisões inválidas não devem sobrescrever dados divergentes', () => {
  const badLocal={...a,updated_at:'não é data'};
  const badRemote={...b,updated_at:t0};
  const out=reconcile([badLocal],[{id:badRemote.id,payload:badRemote,updated_at:t0}],{});
  assert.equal(out.conflicts.length,1);
});
test('tombstone inválido com item remoto cria conflito e não apaga na nuvem', () => {
  const out=reconcile([],[{id:a.id,payload:a,updated_at:t0}],{[a.id]:'inválido'});
  assert.deepEqual(out.deletions,[]);
  assert.equal(out.conflicts.length,1);
});
test('prévia distingue itens para criar, atualizar, importar, substituir e excluir', () => {
  const r0={id:'shared',title:'Remoto antigo',type:'tarefa',updated_at:t0};
  const l0={id:'shared',title:'Local mais novo',type:'tarefa',updated_at:t1};
  const remoteOnly={id:'from-telegram',title:'Telegram',updated_at:t1};
  const localOnly={id:'local-new',title:'Só local',updated_at:t1};
  const deleted={id:'delete',title:'Remover',updated_at:t0};
  const out=reconcile([l0,localOnly],[
    {id:'shared',payload:r0,updated_at:t0},
    {id:'from-telegram',payload:remoteOnly,updated_at:t1},
    {id:'delete',payload:deleted,updated_at:t0}
  ],{delete:t1});
  assert.deepEqual(out.stats,{local:2,cloud:3,after:3,fromCloud:1,
    replacedByCloud:0,create:1,update:1,delete:1,conflicts:0});
});
