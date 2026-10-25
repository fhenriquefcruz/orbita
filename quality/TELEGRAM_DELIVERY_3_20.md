# ORBITA Aurora 3.20 — Entrega verificável no webhook Telegram

## Defeito investigado

A implementação anterior chamava `finish_update` (status `processed`)
antes de enviar a resposta com `sendMessage`. Se o Telegram recusasse,
estourasse o timeout ou a invocação parasse após `finish_update`, o mesmo
`update_id` era considerado duplicado e a resposta armazenada deixava de
ser entregue. Um usuário poderia ter sua tarefa gravada, sem receber confirmação.

Também faltava verificar a quantidade de linhas alteradas em
`CloudMemory.finish_update`: `Prefer: return=minimal` não prova que a
resposta foi persistida.

## Correção

- `finish_update` agora só aceita resposta não vazia e exige uma linha com
  o `update_id` esperado e status `processed`, usando PATCH condicional
  `status=eq.received` e `return=representation`.
- Migração incremental **staged** `infra/supabase/003_telegram_delivery.sql`
  amplia a constraint do status de `orbita_telegram_updates` para
  `received | processed | delivered`. Não altera dados nem privilégio RLS.
- `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` = `0` (padrão). Somente após
  migração e homologação, definir `1` no backend privado.
- Com v2 ativa, uma entrega bem-sucedida chama `mark_delivered` e exige
  confirmação de uma linha. Um webhook repetido para `delivered` é ignorado.
- Para um `update_id` repetido com status `processed` e resposta persistida,
  o webhook reenvia **somente a resposta salva**, sem invocar `reply_text`,
  nem recriar tarefas, repetir chamadas à OpenAI ou interpretar novamente a
  mensagem. Botões de propostas continuam condicionados à origem da mensagem
  e à estrutura válida do preview original.
- `received` sem resposta não é reprocessado cegamente, pois uma invocação
  paralela pode estar em andamento.

## Matriz de estados

| Estado na nuvem | Novo update? | Ação de entrega (v2) |
| --- | --- | --- |
| received | sim | Executar uma vez e persistir a resposta |
| received | não | Não reexecutar; pendente |
| processed com response | não | Reenviar apenas resposta persistida |
| processed com response vazia | não | Pendente para auditoria |
| replied (legado) | não | Preservado; não reexecutar ações antigas |
| delivered | não | Não enviar novamente |
| enviado mas mark_delivered falhou | não | Reenviar após retry; possível duplicação de mensagem |

O recurso oferece **pelo menos uma tentativa recuperável de entrega** por
repetição do webhook, e deduplicação de ações; não é exatamente uma entrega
física. A API Telegram não oferece uma chave idempotente para `sendMessage`.
Se houve sucesso no Telegram mas falha/crash antes do registro `delivered`,
o retry pode duplicar a **mensagem**, embora não duplique a **tarefa**.
Esse risco precisa de aceitação explícita no rollout.

## Garantias e limitações

- Nesta PR, o SQL 003 **não foi aplicado** no projeto Supabase real.
- Sem alterar `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` no servidor, nenhuma
  gravação com status `delivered` será tentada: compatibilidade legado.
- É necessário testar o webhook com Telegram real, chave privada e conta
  vinculada. Não enviar tokens ao GitHub, logs ou conversa.
- A recuperação exige que o Telegram realmente **reenvie o mesmo update**.
  Se o Telegram não tentar novamente, não há job que envie respostas
  pendentes sozinho. O próximo passo para garantia maior é uma outbox com
  worker agendado, lease renovável por update e reenvio com backoff.
- O caso `received` interrompido antes da persistência ainda requer análise
  manual; não executar uma ação possivelmente parcial por mera retransmissão.
- No polling local, o envio permanece independente desta feature flag.
- A PR #7 continua em draft: Auth HTTP real, RLS com duas contas, Safari,
  ativação da migração 002 e da 003 e teste dos botões no Telegram pendentes.

## Testes automatizados

`telegram/tests/test_webhook.py`: falha do `sendMessage`, recuperação do
payload original, ausência de repetição de ações, supressão de duplicatas
entregues, estado pendente, falha de `mark_delivered` e compatibilidade v1.

`telegram/tests/test_cloud_memory.py`: resposta persistida com row count
confirmada, falha fechada para zero linhas/status errado, proibição de
respostas vazias, atualização condicional para `delivered`.

Testes Python/Node/Playwright na CI; estes mocks não substituem E2E com
Supabase/Telegram reais.
