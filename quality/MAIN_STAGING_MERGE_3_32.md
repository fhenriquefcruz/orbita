# ORBITA — Aurora 3.32 | Conciliação de histórico, SEM publicação

## Finalidade e evidência

O repositório tinha dois históricos divergentes: **3 commits exclusivos de `main`** e **57 de homologação** na consulta de 26/10/2026. A PR #7 não era automaticamente mesclável.

A homologação anterior a esta integração já preservava **o conteúdo binário exato** (SHA dos blobs Git idênticos) dos cinco arquivos legados que existiam somente em `main`:

- `infra/TELEGRAM_ACTIVATION.md`
- `infra/supabase/002_least_privilege.sql`
- `infra/supabase/003_telegram_reply_delivery.sql`
- `quality/SUPABASE_ACTIVATION_20261024.md`
- `quality/TELEGRAM_DELIVERY.md`

Os cinco arquivos são preservados como **histórico**. Alguns incluem avaliação de estado datada de 24/10, não representando automaticamente a realidade atual. Para o estado vigente, consultar `quality/MIGRATION_RELEASE_LEDGER_3_31.md` e os gates abaixo.

## Resolução dos cinco caminhos alterados nos dois históricos

| Caminho | Decisão na árvore integrada | Validação exigida |
|---|---|---|
| `api/index.py` | Preservar staging pós-Aurora 3.31, que acrescenta callback seguro, confirmações de ações e reenvio legado `replied` → `processed` após `sendMessage`; V2 isolado por flag | Testes de webhook legado, retry e callback, V2 e cutover |
| `telegram/cloud_memory.py` | Preservar staging pós-Aurora 3.30: `stage_reply`/ACK legado, fila V2 separada, escrita otimista ao concluir tarefas | Testes `test_cloud_memory` e concorrência |
| `telegram/tests/test_webhook.py` | Preservar cobertura expandida do staging, com cenários que verificam a semântica anterior de `main` | Teste Python completo |
| `telegram/tests/test_cloud_memory.py` | Preservar cobertura expandida da homologação para ambos os modos | Teste Python completo |
| `infra/SETUP.md` | Preservar instruções mais atuais da homologação, que tratam SQL 002/003 novos como **pendentes**, não reaplicar as migrações legadas | Inspeção humana e registro de migrações |

## Estratégia de integração

Criar commit Git legítimo com **dois pais** (o SHA congelado de staging e o SHA congelado de `main`), usando a árvore de staging com apenas este documento novo. Isso registra as mudanças históricas de ambas as branches sem substituir arquivos do frontend/backend, sem force push, sem alterar `main` e sem executar SQL.

Esse commit é proposto via PR específica **para a branch de homologação**; requer CI Python, JS, navegador e sintaxe Windows aprovadas. Após integrar a PR em homologação usando **merge commit**, verificar novamente que `main` é ancestral e que a PR #7 continua **draft**, sem publicação automática.

## Gates que NÃO são eliminados por esta conciliação

1. Supabase `tbqfymedgdsdrgkqmuni`: o arquivo `infra/supabase/002_least_privilege.sql` e o histórico `003_telegram_reply_delivery.sql` já foram aplicados. **Não executar novamente.**
2. `002_action_proposals.sql` e `003_telegram_delivery.sql`: ainda **não aplicados**, sem permissão para execução até backup restaurado em ambiente isolado e autorização separada.
3. Teste real do Safari, recuperação Auth, Vercel/Telegram e conectividade 5432 pendentes.
4. Flags `ORBITA_NATURAL_ACTIONS_ENABLED` e `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` desligadas.
5. Merge `main` / publicação do painel exige autorização explícita.

**Escopo:** só Git staging; não toca ambiente produtivo, banco, tokens, webhook nem arquivos privados.
