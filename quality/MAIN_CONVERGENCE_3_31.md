# ORBITA Aurora 3.31 — convergência seletiva com main, sem release

## Resultado desta etapa

A branch `main` tem três commits exclusivos sobre a ancestralidade da
homologação. PR #7 continua `draft` e `mergeable=false`. PR #41 (Aurora 3.30)
já restaurou a fila durável **replied** no modo legado (flag v2 OFF).
A PR #42, que duplicava essa correção, foi encerrada sem merge.

Esta fase **não mescla `main`**, **não faz rebase/force-push** e não
ativa webhooks. Preserva arquivos históricos exclusivos de `main` que faltavam
na homologação, sem reexecutar SQL nem declarar conflitos solucionados.

### Migrações com mesmo número, mas funções diferentes

| Origem original de main, já executada | Opcional de homologação, NÃO aplicada |
| --- | --- |
| `infra/supabase/002_least_privilege.sql`: grants da Data API | `infra/supabase/002_action_proposals.sql`: propostas de ação e RPC |
| `infra/supabase/003_telegram_reply_delivery.sql`: estados received/replied/processed | `infra/supabase/003_telegram_delivery.sql`: adiciona estado delivered |

Copiar arquivos para Git **não significa aplicar migrações**. As
migrações opcionais 002/003 continuam bloqueadas até dump privado,
restauração isolada bem-sucedida, homologação de SQL e autorização de rollout.

### Compatibilidade no corte de V2

Se um update já estiver no estado legado `replied` quando a flag
`ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` for autorizada futuramente,
o novo código:

1. Usa a resposta persistida, sem reexecutar `reply_text` e sem recriar
   tarefa/ideia.
2. Só depois de `sendMessage` bem-sucedido executa o ACK
   `replied -> processed`, exigindo a mesma revisão e identificador.
3. Confirma em seguida o ACK `processed -> delivered`.
4. Se uma das chamadas falhar, responde 503 e não declara a entrega como
   sucesso. Enviar uma resposta duplicada é possível em falha de ACK
   depois do envio — **não prometer exatamente uma vez**.

Cobertura de testes offline em `telegram/tests/test_webhook.py`.
O fluxo legado de PR #41 continua intacto para flag v2 OFF.

## Limites do avanço

- O conflito histórico de PR #7 **ainda** exige reconciliação de commits,
  revisão dos conflitos Git remanescentes e CI completa antes de publicação.
- Não houve teste real de webhook Telegram, Safari/iPhone ou recuperação
  de senha; mocks não contam como prova E2E real.
- O `pg_dump` no Windows expira por indisponibilidade da porta 5432;
  continua sem backup restaurável.
- Não copiar documentação histórica antiga como status atual. Conferir
  `quality/AUTH_RELEASE_GATE.md` e a PR #7 para o estado verificado.

**Sem alterações no banco, produção, tokens, APIs externas ou flags.**
