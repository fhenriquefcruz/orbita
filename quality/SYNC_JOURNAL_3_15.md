# ORBITA Aurora 3.15 — finalização recuperável da conciliação

## Defeito de integridade

O painel gravava `orbita_v12_local` e `orbita_cloud_tombstones_v1`
sequencialmente ao finalizar `Conciliar registros agora`. Uma queda do navegador,
exceção `QuotaExceededError` ou desligamento entre operações podia persistir
somente uma das chaves. A proteção existente (Aurora 3.12/3.13) era aplicada a
exclusões individuais, mas não à conciliação de registros locais e remotos.

## Correção proposta

- `docs/local-integrity.js`: `commitSync(storage, owner, nextStore, nextTombstones, expected)`
  reutiliza o journal write-ahead persistente `orbita_local_txn_v1`.
- Exige snapshot completo de `store`, `tombstones` e `binding`; bloqueia
  troca de titular ou alteração local concorrente antes de iniciar a gravação.
- Journal salva estados **anterior** e **posterior**; em falha após a primeira
  escrita, tenta rollback; se o rollback também falhar, preserva o journal para
  recuperação na próxima inicialização. Divergências de outras abas bloqueiam
  sobrescrita automática.
- `docs/cloud-sync.js`: cria guarda da aba no início, recusa journal pendente,
  verifica as três chaves antes do envio e antes da finalização, e usa
  `commitSync` em vez de duas gravações diretas. Remove escrita redundante de
  `binding`, que já precisa estar vinculada corretamente.
- PWA cache de homologação atualizado para instalar `local-integrity.js` novo.

## Cenários automatizados

`quality/test_local_integrity.cjs` adiciona sete casos:
1. Conciliação íntegra e limpeza do journal.
2. Recusa de snapshot ausente ou incompleto.
3. Snapshot obsoleto não altera dados de outra aba.
4. Falha do segundo `setItem` reverte ambos os valores.
5. Falha no rollback preserva journal e permite recuperação posterior.
6. Interrupção após a primeira gravação é revertida na nova abertura.
7. Troca de titular bloqueia a operação.

`quality/browser_smoke.py` passa a exercitar conciliação somente nuvem → local
com autenticação simulada, falha de armazenamento na segunda chave, ausência de
estado parcialmente escrito e repetição bem-sucedida. Todo o conjunto preexistente
continua no workflow de testes.

## Limites e riscos restantes

**Não é uma transação distribuída com o Supabase.** O rollback local não reverte
POST, PATCH ou DELETE já confirmados pelo servidor. Em caso de falha, preservar
backup e executar novamente a prévia antes de nova sincronização. O rollback na
abertura recupera o estado local anterior; o Supabase permanece como estava após
as alterações já confirmadas. Persistência multi-chave no `localStorage` também
não é transação atômica entre abas. Para garantia forte, a migração para IndexedDB
multi-store e protocolo transacional no backend requerem desenho e homologação
específicos, não inclusos neste incremento.

Sem alteração de banco, produção, permissões RLS, segredos ou notificações.
Validações reais em iOS/Safari, múltiplas contas Auth e conflitos HTTP continuam
sendo gates de publicação da PR #7. A PR #23 de cache offline seguro segue separada;
ao integrá-la, resolver versões de cache com teste de regressão.
