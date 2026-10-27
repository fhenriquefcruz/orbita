# ORBITA Aurora 3.29 — Convergência controlada com main

## Diagnóstico de divergência

No dia 26/10/2026, `main` possui **3 commits** não presentes no
histórico de `feat/supabase-auth-protected-panel`; a homologação tem 53
commits distintos desde o ancestral comum. A PR principal #7 está em draft
e GitHub informa `mergeable=false`. **Nunca dar force push ou mesclar
para produção só porque os testes da homologação passaram.**

A revisão de código encontrou uma regressão potencial:
- Em `main`, o fluxo Telegram faz
  `received -> replied` (resposta gravada antes de enviar) ->
  `processed` (ACK depois do envio). Se o Telegram não responder, um
  novo webhook recupera a mesma resposta sem repetir `/tarefa` ou
  `/feito`.
- Em homologação, a evolução V2 armazena a resposta em `processed` antes
  do envio e transita para `delivered` após o ACK; essa mudança exige
  a SQL adicional `003_telegram_delivery.sql`, ainda não instalada.
  Quando a flag estava OFF, o código de homologação também usava esse
  caminho, mas não retomava falhas legadas em `replied`.

## Solução compatível e testada em CI (sem habilitar produção)

1. A implementação Aurora 3.29 preserva `CloudMemory.stage_reply` para
   criar `replied` **apenas com revisão `received`** e ACK verificável.
   `CloudMemory.confirm_legacy_sent` confirma
   `replied -> processed` somente depois de `sendMessage` retornar.
   Todas as mudanças exigem `user_id`, `update_id` e confirmação da
   linha efetivamente alterada; zero rows ou linha errada é falha.
2. Com `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED=0` (padrão atual), o webhook
   mantém o protocolo legado de `main`. Se uma resposta já estiver em
   `replied`, a reenvia sem reexecutar a ação de memória.
3. Com `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED=1`, o webhook permanece
   compatível com `processed -> delivered` e, durante a troca de versão,
   sabe retomar um `replied` legado por
   `replied -> processed -> delivered` sem novo `reply_text`.
4. Atualizados testes para ordem de gravação/envio/ACK, erro de
   persistência, reenvio após falha, duplicata após `processed`,
   migração `replied` para V2 e isolamento do usuário nas mudanças.
   Testes usam mocks; não acionam Telegram nem Supabase real.

## Arquivos exclusivos de main preservados em homologação

- `infra/TELEGRAM_ACTIVATION.md`
- `infra/supabase/002_least_privilege.sql`
- `infra/supabase/003_telegram_reply_delivery.sql`
- `quality/SUPABASE_ACTIVATION_20261024.md`
- `quality/TELEGRAM_DELIVERY.md`

Esses arquivos servem de **histórico ou referência**. Não executar
migrações antigas novamente só porque foram copiadas. A nomenclatura
numérica 002/003 identifica **duas famílias diferentes** de SQL:

| Existentes no banco (24/10/2026) | Novas, ainda BLOQUEADAS |
| --- | --- |
| `002_least_privilege.sql` | `002_action_proposals.sql` |
| `003_telegram_reply_delivery.sql` | `003_telegram_delivery.sql` |

O Supabase conectado foi verificado em 26/10/2026:
`public.orbita_action_proposals` ausente;
`orbita_telegram_updates.status` ainda **sem** `delivered`.
**Não aplicar o par novo** até backup + restauração isolada e autorização
separada. Não deixar o nome do arquivo ditar o que já está aplicado.

## O que ainda falta para resolver conflito histórico PR #7

A presente PR traz as **mudanças de conteúdo** necessárias para conciliar
o mecanismo de resposta. Ela não adiciona automaticamente os três
commits de `main` ao histórico Git de homologação. É necessário
reconciliar a ancestralidade das branches por um merge real e revisar
o resultado antes da integração final. Quando possível, preferir
merge sem rebase destrutivo, com validação CI e testes de webhook.
Não declarar `mergeable=true` só porque conteúdos foram copiados.

**Limites operacionais:** nenhum deploy, webhook, flag, migração ou dado
pessoal foi modificado por esta etapa. `main` permanece intocada.
A publicação final da PR #7 continua expressamente bloqueada.
