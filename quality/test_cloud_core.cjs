const test = require('node:test');
const assert = require('node:assert/strict');
const {reconcile,planCloudImport,planBackupRestore} = require('../docs/cloud-core.js');
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

test('importação somente leitura incorpora somente IDs ausentes e conserva o original', () => {
  const remoteOnly={id:'tg-1',title:'Tarefa Telegram',type:'tarefa',updated_at:t1};
  const mine=[a];
  const remote=[{id:'orb-a',payload:b},{id:'tg-1',payload:remoteOnly}];
  const out=planCloudImport(mine,remote,{});
  assert.equal(out.stats.imported,1);
  assert.equal(out.stats.divergent,1);
  assert.equal(out.records.length,2);
  assert.equal(out.records[0],a);
  assert.equal(out.records[1],remoteOnly);
  assert.equal(mine.length,1);
});
test('exclusão local pendente impede ressurreição por importação da nuvem', () => {
  const remote={id:'tg-del',title:'Já excluído',type:'tarefa'};
  const out=planCloudImport([],[{id:'tg-del',payload:remote}],{'tg-del':t1});
  assert.equal(out.records.length,0);
  assert.equal(out.stats.locallyDeleted,1);
});
test('importação não duplica registros locais e trata payloads equivalentes', () => {
  const local={id:'same',title:'Mesmo',type:'tarefa'};
  const remote={type:'tarefa',title:'Mesmo',id:'same'};
  const out=planCloudImport([local],[{id:'same',payload:remote}],{});
  assert.equal(out.stats.alreadyLocal,1);
  assert.equal(out.stats.divergent,0);
  assert.deepEqual(out.records,[local]);
});
test('a importação bloqueia payload sem título ou id incorreto e entradas duplicadas', () => {
  const valid={id:'tg-1',title:'Novo',type:'ideia'};
  const out=planCloudImport([],[
    {id:'bad',payload:{id:'outro',title:'Inválido'}},
    {id:'empty',payload:{id:'empty',title:' '}},
    {id:'tg-1',payload:valid},
    {id:'tg-1',payload:valid}
  ],{});
  assert.deepEqual(out.stats,{cloud:4,local:0,imported:1,alreadyLocal:0,
    divergent:0,locallyDeleted:0,invalid:2,duplicates:1});
});
test('importação rejeita tombstones e formatos de entradas inválidos', () => {
  assert.throws(()=>planCloudImport([],[],[]),/Dados inválidos/);
  assert.throws(()=>planCloudImport({},[],{}),/Dados inválidos/);
  assert.throws(()=>planCloudImport([],{},{}),/Dados inválidos/);
});

const owner='11111111-1111-4111-8111-111111111111';
const backupRecord={id:'tg-x',title:'Voltar do backup',type:'tarefa',status:'a_fazer',priority:'P1'};
const current={records:[],audit:[],tombstones:{'old-delete':t0}};
test('backup completo restaura marcadores e preserva conversas ausentes',()=>{
  const backup={schema_version:1,account_id:owner,records:[backupRecord],audit:[],
    tombstones:{'new-delete':t1}};
  const plan=planBackupRestore(backup,current,owner);
  assert.equal(plan.records.length,1);
  assert.equal(plan.summary.exclusions,2);
  assert.equal(plan.tombstones['old-delete'],t0);
  assert.equal(plan.tombstones['new-delete'],t1);
  assert.equal(plan.chat,null);
  assert.equal(plan.summary.chatPreserved,true);
  assert.equal(plan.summary.unbound,false);
});
test('backup de outra conta é bloqueado',()=>{
  assert.throws(()=>planBackupRestore({schema_version:1,account_id:'outro',
    records:[backupRecord],tombstones:{}},current,owner),/outra conta/);
});
test('backup legado sem tombstones preserva exclusões locais',()=>{
  const plan=planBackupRestore({schema_version:1,records:[backupRecord]},current,owner);
  assert.equal(plan.summary.legacy,true);
  assert.equal(plan.summary.unbound,true);
  assert.equal(plan.tombstones['old-delete'],t0);
});
test('não ressuscita registro que já estava excluído localmente',()=>{
  const deleted={...backupRecord,id:'old-delete'};
  assert.throws(()=>planBackupRestore({schema_version:1,records:[deleted]},
    current,owner),/marcados como excluídos/);
});
test('backup inválido: ids duplicados, campo obrigatório e exclusão inválida',()=>{
  assert.throws(()=>planBackupRestore({schema_version:1,
    records:[backupRecord,backupRecord]},current,owner),/duplicado/);
  assert.throws(()=>planBackupRestore({schema_version:1,
    records:[{...backupRecord,priority:'P9'}]},current,owner),/inválido/);
  assert.throws(()=>planBackupRestore({schema_version:1,records:[],
    tombstones:{x:'erro'}},current,owner),/datas inválidas/);
});
test('backup de Telegram aceita título até 1000 e estado em_andamento',()=>{
  const p={...backupRecord,title:'A'.repeat(1000),status:'em_andamento'};
  const plan=planBackupRestore({schema_version:1,records:[p]},current,owner);
  assert.equal(plan.records[0].title.length,1000);
});
test('backup conserva histórico de conversa quando presente e recusa formatos errados',()=>{
  const p=planBackupRestore({schema_version:1,records:[],
    chat:[{role:'user',content:'Teste'}]},current,owner);
  assert.equal(p.chat.length,1);
  assert.equal(p.summary.chatPreserved,false);
  assert.throws(()=>planBackupRestore({schema_version:1,records:[],
    chat:{}},current,owner),/Histórico/);
});
