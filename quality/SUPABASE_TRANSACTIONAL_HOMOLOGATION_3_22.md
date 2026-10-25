# ORBITA Aurora 3.22 — Homologação transacional das migrações 002 e 003

**Objetivo:** comprovar que a proposta de tarefa/ideia é gravada uma vez e somente por confirmação válida, sem aplicar definitivamente o esquema nem modificar dados existentes.

**Ambiente verificado:** projeto Supabase **exclusivo ORBITA**, em 24/10/2026. O ensaio foi executado por conexão autorizada, em uma única transação PostgreSQL delimitada por `BEGIN` e `ROLLBACK`.

## Resultado real do ensaio

| Caso | Resultado |
| --- | --- |
| Criar tabela de propostas em transação isolada | Aprovado |
| Criar RPC de confirmação `SECURITY INVOKER` | Aprovado |
| Habilitar RLS e negar acesso de `anon` e `authenticated` | Aprovado no catálogo SQL |
| Garantir `EXECUTE` da RPC apenas ao backend privilegiado | Aprovado no catálogo SQL |
| Acrescentar `delivered` mantendo `replied` | Aprovado |
| Confirmar tarefa e obter identificador uma única vez | Aprovado |
| Repetir confirmação e obter `already` com mesmo identificador | Aprovado |
| Confirmar com outro UUID de titular | Recusado (`missing`) |
| Confirmar com outro Telegram ID | Recusado (`missing`) |
| Confirmar proposta cancelada | Recusado (`cancelled`) |
| Confirmar proposta expirada | Recusado (`expired`) |
| Reverter transação com `ROLLBACK` | Aprovado |

**Verificação independente após o ensaio:** tabela `orbita_action_proposals` continua ausente; RPC `orbita_confirm_action_proposal` continua ausente; a constraint do Telegram não contém `delivered`; o registro de teste não permaneceu na memória. Nenhuma migração real foi aplicada.

## Repetir o ensaio

A partir da raiz do repositório, monte o SQL de homologação com:

```bash
python quality/build_supabase_dryrun.py > /tmp/orbita-dryrun.sql
```

O utilitário **não possui conexão com Supabase** e não executa o SQL. Ele concatena os dois arquivos existentes de migração e a bateria de verificações, envolvendo todo o conjunto em `BEGIN`, limites de lock/tempo e `ROLLBACK`. O `COMMIT` interno da migração 003 é removido **somente do SQL gerado para o ensaio**.

Após revisão humana, o operador pode executar o SQL gerado no editor do projeto exclusivo e conferir o objeto `homologation_evidence`. A confirmação definitiva de reversão requer uma consulta independente, em sessão posterior, como:

```sql
select
  to_regclass('public.orbita_action_proposals') is null as proposals_not_persisted,
  to_regprocedure('public.orbita_confirm_action_proposal(text,uuid,bigint)') is null as rpc_not_persisted,
  not exists (
    select 1 from public.orbita_records
    where payload->>'title' = 'ORBITA DRY-RUN TEMPORARY TASK'
      and id like 'tg-action-%'
  ) as test_record_not_persisted;
```

**Cuidado operacional:** se o SQL falhar ou a ferramenta desconectar, confirme explicitamente que o banco descartou a transação. O script usa uma conta Auth já existente **apenas como referência de chave estrangeira** durante a transação não confirmada, sem expor o UUID, nome ou e-mail. O teste não cria usuários ou envia mensagens Telegram.

## Limites importantes

- As checagens SQL de privilégios e isolamento de parâmetros não substituem **duas sessões Auth HTTP reais**, com JWTs diferentes e operações PostgREST.
- Repetição em sequência dentro da transação não substitui prova de concorrência em **duas conexões paralelas**, embora a função utilize `FOR UPDATE`.
- Não houve webhook, resposta OpenAI, callback em Telegram real, teste Safari nem publicação de frontend.
- A migração SQL 002 e a 003 continuam **pendentes no banco real**. As flags `ORBITA_NATURAL_ACTIONS_ENABLED` e `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` permanecem desligadas por padrão.
- Não foi realizado backup/restauração operacional da base. Isso é um gate antes de um rollout permanente.
- O código de confirmação identifica uma proposta aleatória e limita o acesso por usuário e Telegram ID; ele não concede autenticação por si só. Somente o webhook autenticado deve controlar esses parâmetros.
- Um teste passando e um `ROLLBACK` verificado são **evidência de compatibilidade**, não uma aprovação automática para alterar `main` ou ativar notificações.

## Próxima decisão de publicação

Após aprovação operacional específica para alterar o banco do projeto ORBITA, realizar backup, revisar as migrações 002/003 e aplicá-las, repetir `infra/supabase/preflight_readonly.sql`, conferir Security Advisors e executar casos reais de Auth, RLS e Telegram. Só então avaliar a ativação das flags no servidor privado.

A suíte `telegram/tests/test_supabase_migration_dryrun.py` contém nove testes offline para garantir que o roteiro gerado sempre termina em `ROLLBACK` e identifica mudanças inesperadas.
