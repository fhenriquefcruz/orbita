# ORBITA | Decisao de arquitetura de recuperacao (29/10/2026)

## Evidencia real: backup ORBITA em formato PostgreSQL custom

O operador executou `quality/private_restore_archive_inventory_windows.ps1` no Windows. Relatorio **somente leitura**:

| Dimensao do catalogo | Valor observado |
| --- | ---: |
| Integridade SHA256, manifesto, ACL, TOC | Aprovada |
| Versao major da origem | PostgreSQL 17 |
| Entradas TOC | 599 |
| TABLE DATA | 42 |
| POLICY | 7 |
| SCHEMA | 9 |
| EXTENSION | 4 |
| ACL | 137 |
| DEFAULT ACL | 24 |
| ROW SECURITY | 28 |
| FUNCTION/PROCEDURE | 49 |
| TRIGGER/EVENT TRIGGER | 14 |
| SEQUENCE SET | 4 |
| PUBLICATION/SUBSCRIPTION | 1 |
| Entradas reconhecidas como objetos em schemas gerenciados | 403 |
| TABLE DATA em `auth.users` | Presente |
| TABLE DATA em `public.orbita_records` | Presente |
| TABLE DATA em `public.orbita_chat_messages` | Presente |
| TABLE DATA em `public.orbita_telegram_updates` | Presente |

**Interpretação rigorosa:** 403/599 (~67,3%) representa **entradas categorizadas pelo classificador baseado no TOC**, não 67,3% dos dados em bytes, nem 67,3% de registros de usuários. Classes podem se sobrepor às demais contagens por tipo. Não inferir quantidades de linhas, tamanhos ou conteúdo.

## Resultado: bifurcar em duas estrategias, nao executar restore integral

**A — Extrair dados e estruturas pertencentes ao ORBITA, somente quando dependencias forem resolvidas.**
- O novo inventario classifica a quantidade de `TABLE DATA public orbita_*` e separa dos dados em schemas gerenciados.
- Objetos em `public` com prefixo `orbita_` sao **candidatos**, nao uma allowlist executavel.
- **Dependencia confirmada no codigo-fonte:** `infra/supabase/001_core.sql` define `public.orbita_records.user_id`, `public.orbita_chat_messages.user_id` e `public.orbita_telegram_updates.user_id` com `REFERENCES auth.users(id) ON DELETE CASCADE`. As politicas de registros e mensagens verificam `auth.uid()`. Assim, a recuperacao apenas das tabelas `orbita_*` em PostgreSQL nativo vazio **falharia ou perderia a semantica de acesso**, salvo reconstrucao explicitamente projetada de roles/Auth/FK/RLS. **Nao restaurar APP_ONLY automaticamente**.

- Devem ser revisados proprietarios, FK, constraints, triggers, funcoes, sequencias, politicas RLS e eventuais dependencias de `auth.uid()`.
- Importar dados de usuarios `auth.users` separadamente em PostgreSQL nativo nao equivale a criar um sistema Supabase Auth funcional.
- Sem execucao de `pg_restore`, sem criar SQL de restore nem lista `-L` automaticamente.

**B — Recuperacao integral com semantica Supabase em um ambiente Supabase isolado.**
- Investigar uma instancia descartavel Supabase compativel, com isolamento e custos revisados. Nao apontar para o projeto Supabase ORBITA ativo.
- A ferramenta oficial "Restore to a new project" depende de plano pago com backups fisicos habilitados; pode envolver custo e reconfiguracao de Auth/Storage/Edge Functions.
- Cuidado especial: workflows e extensoes que fazem chamadas externas podem reativar ao clonar; isolar tarefas, chaves e redes antes de qualquer recuperacao.
- Um dump logico pode demandar roles/extensoes e configuracoes de Auth que nao existem no Postgres nativo.

Documentacao: [PostgreSQL 17 pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html), [Supabase database backups](https://supabase.com/docs/guides/platform/backups), [Supabase restore to a new project](https://supabase.com/docs/guides/platform/clone-project).

## O que foi alterado nesta PR

O script **existente** `quality/private_restore_archive_inventory_windows.ps1` ganha `Summarize-RestoreScope` e `Show-RestoreScope`, sem criar novos comandos de restauracao.

Novo output (somente totais):
- `TABLE_DATA_PUBLIC_ORBITA`
- `TABLE_DATA_SCHEMAS_GERENCIADOS`
- `TABLE_DATA_OUTROS`
- `TABLE_DATA_PUBLIC_NAO_ORBITA`
- `ENTRADAS_PUBLIC_ORBITA_CANDIDATAS`

A soma dos tres grupos TABLE DATA deve dar **exatamente 42** para o backup analisado, ou o procedimento aborta. Os limites significam apenas escopo candidato; **nao comprovam recuperabilidade nem seguranca de codigo presente no dump**. O classificador sempre preserva o bloqueio contra restauracao nativa integral quando detecta dependencias gerenciadas/extensoes/publicacao.

A CI Windows executa autotestes usando TOC artificial e obriga a abortar diante de classificacao inconsistente. Nada em CI le o arquivo privado nem conecta ao banco.

## Proximo unico bloco no Windows

Se os scripts da branch de homologacao estiverem atualizados, rodar o **inventario em modo offline**, sem repetir inicializacao:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_archive_inventory_windows.ps1"
```

Separadamente, **se a senha propria do sandbox for conhecida**, o `quality/private_restore_native_windows_local_auth.ps1` pode executar a verificacao SCRAM 3.47 somente depois de aprovar prontidao 3.46; entrada oculta e apenas uma tentativa. Nao substituir por senha do projeto Supabase, Windows, Gmail, GitHub ou produção.

## Definicao de pronto para autorizar teste de recuperacao

1. Classificacao de `TABLE DATA` e classes de dependencias reais conferida, sem nomes ou dados privados no repositorio.
2. Credencial local do sandbox validada em dispositivo confiavel, quando necessaria.
3. **Destino efetivamente descartavel** definido e confirmado, sem uso do banco `postgres` local e sem atingir `postgresql-x64-17` em 5432.
4. Compatibilidade de ownership, roles, policies, extensoes e funcoes revisada sem executar SQL do backup.
5. Plano de rollback e verificacao funcional aprovado antes da primeira escrita.
6. Autorizacao expressa e separada para qualquer `pg_restore`, SQL 002/003, criacao de banco ou modificacao de Auth/RLS.

**Estado:** esquema de recuperacao definido; nenhuma restauracao realizada ou autorizada. Estabilidade local, SHA256 e prontidao TCP ja obtidas. Auth/JWT/RLS com duas contas reais seguem pendentes, e os testes feitos no Postgres nativo nunca os substituem.
