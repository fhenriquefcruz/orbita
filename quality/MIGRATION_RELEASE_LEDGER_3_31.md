# ORBITA — Aurora 3.31 | Registro real das migrações e gate de recuperação

**Projeto exclusivo:** `tbqfymedgdsdrgkqmuni` (sa-east-1).  
**Data da consulta remota somente-leitura:** 26/10/2026, horário local de Campo Grande.  
**Política:** este documento não é instrução para executar migração imediatamente.

## Aplicadas no Supabase (confirmadas pelo histórico do projeto)

| Versão remota | Migração no histórico | Situação | Contexto |
|---|---|---|---|
| `20261024162354` | `orbita_core_records_chat_telegram` | APLICADA | Tabelas base e RLS |
| `20261024162455` | `orbita_least_privilege_api_grants` | APLICADA | Grants restritos; arquivo de referência em `main`: `infra/supabase/002_least_privilege.sql` |
| `20261024163757` | `orbita_telegram_reply_delivery` | APLICADA | `received` → `replied` → `processed`; arquivo de referência em `main`: `infra/supabase/003_telegram_reply_delivery.sql` |
| `20261025103735` | `orbita_telegram_update_owner_index` | APLICADA | Índice de acesso do Telegram |

**Evidência SQL read-only:** `public.orbita_telegram_updates` aceita somente os estados
`received`, `replied` e `processed` no constraint `orbita_telegram_updates_status_check`.
A tabela já contém quatro registros de update do Telegram; **não reinterpretar retrospectivamente
esses registros como entregas verificadas**. A tabela `orbita_records` contém 1 registro,
e `orbita_chat_messages` contém 0 mensagens, nesta consulta.

### Migrações NOVAS, ainda NÃO aplicadas

| Arquivo exato na homologação | Estado real | Dependências |
|---|---|---|
| `infra/supabase/002_action_proposals.sql` | **PENDENTE** | Backup restaurável, autorização específica, teste RPC/RLS e ativação controlada da flag de ações naturais |
| `infra/supabase/003_telegram_delivery.sql` | **PENDENTE** | Backup restaurável, compatibilidade com `replied`, testes de replay, ativação posterior e isolada de `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` |

**Atenção à numeração:** `002_least_privilege.sql` **não** é a migração
`002_action_proposals.sql`; `003_telegram_reply_delivery.sql` **não** é
`003_telegram_delivery.sql`. O número curto no nome do arquivo não
comprova execução. Identifique a operação pelo **nome completo e versão
registrada no Supabase**. Não executar arquivos antigos outra vez nem
aplicar os novos em lote.

## Controles de segurança observados

- `public.orbita_action_proposals`: **não existe**.
- RPC `public.orbita_confirm_action_proposal(text,uuid,bigint)`: **não existe**.
- `anon` e `authenticated` não possuem permissão `SELECT` sobre
  `public.orbita_telegram_updates`; acesso da fila continua exclusivo do backend.
- `authenticated` possui acesso `SELECT` aos registros sujeito a políticas RLS.
- Aurora 3.30 preserva o fluxo legado, com resposta salva em `replied` e
  finalizada em `processed` **depois do envio**.
- O fluxo v2 `processed` → `delivered` ainda não pode ser habilitado.

## Portões antes de executar qualquer SQL pendente

1. Diagnosticar bloqueio de rede ao Session pooler, PostgreSQL porta 5432,
   no computador privado. **Timeout não indica senha incorreta.**
2. Criar backup privado real abrangendo tabelas `auth.users`,
   `public.orbita_records`, `public.orbita_chat_messages`,
   `public.orbita_telegram_updates` e demais objetos necessários.
3. Verificar integridade (catálogo e SHA-256) e **restaurar efetivamente em
   ambiente isolado**, inclusive revisão de RLS, Auth, papéis e dependências.
4. Aprovar separadamente o ensaio de migração de propostas, testes de
   race/expiração/proteção RLS e liga/desliga de flag.
5. Aprovar separadamente ensaio de entrega Telegram v2, timeout, replay,
   idempotência e compatibilidade dos registros `replied` anteriores.
6. Somente depois, com autorização explícita, aplicar SQL controladamente,
   consultar histórico e schema, validar integrações e considerar release.

**Proibido** mesclar a PR #7 em `main` ou afirmar backup recuperável com
apenas `pg_restore --list`. Nenhuma senha, dump, token ou conexão privada
deve entrar no Git ou no chat.

## Consulta de inspeção, sem alterações

```sql
select
  to_regclass('public.orbita_action_proposals') is not null as proposals_exist,
  to_regprocedure(
    'public.orbita_confirm_action_proposal(text,uuid,bigint)'
  ) is not null as proposal_rpc_exists,
  (
    select pg_get_constraintdef(c.oid)
    from pg_constraint c
    where c.conrelid = 'public.orbita_telegram_updates'::regclass
      and c.conname = 'orbita_telegram_updates_status_check'
    limit 1
  ) as telegram_statuses,
  has_table_privilege(
    'authenticated', 'public.orbita_telegram_updates', 'SELECT'
  ) as authenticated_can_select_telegram_queue;
```

Se qualquer evidência remota mudar, revalidar o plano antes de aplicar migração.
