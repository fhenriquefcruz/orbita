# ORBITA 3.0 — Ativação da memória central (24/10/2026)

## Projeto dedicado confirmado
- Organização: **ORBITA** (`werdijemyekgdpkqovso`).
- Projeto: **orbita** (`tbqfymedgdsdrgkqmuni`).
- Região: `sa-east-1` (São Paulo).
- Provisão: `ACTIVE_HEALTHY`, plano Free, cotação de criação de US$ 0/mês.
- URL pública: `https://tbqfymedgdsdrgkqmuni.supabase.co`.
- Nenhuma informação de autenticação ou memória pessoal foi transferida.

## Migrações executadas
1. `orbita_core_records_chat_telegram` (versão Supabase `20261024162354`) a partir de `infra/supabase/001_core.sql`.
2. `orbita_least_privilege_api_grants` (versão Supabase `20261024162455`) equivalente a `infra/supabase/002_least_privilege.sql`.

As três tabelas usam RLS. As sete políticas habilitam leitura, criação, edição e exclusão **apenas da própria conta** para `orbita_records` e leitura/criação/exclusão para `orbita_chat_messages`. `orbita_telegram_updates` não tem políticas para navegador ou grants `anon/authenticated`; apenas o servidor pode utilizá-la.

## Verificação de permissões (consulta a pg_class/has_table_privilege)
| Tabela | RLS | anon SELECT | authenticated SELECT | authenticated INSERT | authenticated UPDATE | authenticated DELETE |
| --- | --- | --- | --- | --- | --- | --- |
| orbita_records | sim | não | sim | sim | sim | sim |
| orbita_chat_messages | sim | não | sim | sim | não | sim |
| orbita_telegram_updates | sim | não | não | não | não | não |

O serviço tem permissão de SELECT nas três tabelas. Consulta de 2 migrações concluída. Não foram criados usuários ou registros de teste permanentes.

## Aviso do auditor
`rls_enabled_no_policy` em `public.orbita_telegram_updates` (INFO): **intencional** por ser tabela reservada ao servidor. Mesmo que o código administre updates, nunca conceder acesso a `anon` ou `authenticated` para suprimir o aviso.
Referência: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy

## Pendências reais
- Criar/autorizar identidade Supabase Auth do proprietário sem expor senha.
- Definir Site URL e Redirect URLs para `https://fhenriquefcruz.github.io/orbita/`.
- Executar teste ponta a ponta da RLS com **duas contas reais e sem dados sensíveis** (leitura/alteração de registros entre titulares).
- Homologar o PR #7: login, restauração de sessão, recuperação, importação/exportação, compatibilidade mobile.
- Configurar no servidor, exclusivamente como variáveis privadas, o novo token Telegram revogado/reemitido, `ORBITA_USER_UUID`, chave secreta Supabase e eventual OpenAI API key. Validar API e webhook em produção.
- Sincronização no painel continua **manual**, sem notificação ou IA online até deploy e testes.

**Estado de entrega:** banco e RLS implantados; integração de usuário e Telegram bloqueada por autenticação/credenciais, não considerada aprovada.
