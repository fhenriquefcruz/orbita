# Aurora 3.29 — Auditoria de integração sem publicação

Estado em 26/10/2026. **Não realizar merge automático de staging em main.**

## Evidência GitHub

Comparação `feat/supabase-auth-protected-panel...main`: três commits exclusivos de `main`, 53 commits exclusivos da homologação; PR #7 em rascunho, `mergeable=false`.

Arquivos de `main` a preservar/reconciliar:

- `api/index.py`: em `main`, entrega Telegram usa resposta persistida em status `replied` e recuperação após falha; em staging, fluxo `processed/delivered` fica atrás de flag desligada. Exigir testes de ambos os modos antes de qualquer integração.
- `telegram/cloud_memory.py`: diferenças no método `stage_reply`, `finish_update` e estados de entrega; evitar substituir sem migração compatível.
- `telegram/tests/test_webhook.py` e `telegram/tests/test_cloud_memory.py`: preservar cobertura de retry e idempotência do modo legado de `main` e do modo v2 de staging.
- `infra/SETUP.md`, `infra/TELEGRAM_ACTIVATION.md`, `quality/SUPABASE_ACTIVATION_20261024.md`, `quality/TELEGRAM_DELIVERY.md`: preservar instruções operacionais existentes.
- `infra/supabase/002_least_privilege.sql` e `003_telegram_reply_delivery.sql`: são scripts **diferentes** de `002_action_proposals.sql` e `003_telegram_delivery.sql` de staging. Não tratar nomes numerados como migrações equivalentes.

## Gates antes da publicação

1. Resolver conflitos em branch temporária, sem alterar `main` ou staging diretamente; conferir comportamento Telegram antigo e novo.
2. CI completa, testes de Auth em dispositivos e ensaio real de Telegram.
3. Diagnosticar timeout de rede 5432, obter backup privado e **restaurar em ambiente isolado**.
4. SQL 002/003 só após recuperação comprovada e aprovação específica; flags `ORBITA_NATURAL_ACTIONS_ENABLED` e `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` continuam OFF.
5. Publicação de `main` exige autorização explícita posterior.

Esta auditoria é documental e não modifica banco, webhook, chaves ou produção.
