# ORBITA 3.0 — Homologação do Supabase Auth

## Revisão operacional de 25/10/2026 — Supabase conectado

- Organização **ORBITA** e projeto exclusivo `orbita` (`tbqfymedgdsdrgkqmuni`) confirmados como **ACTIVE_HEALTHY** na região `sa-east-1`.
- SQL read-only constatou **1 conta Auth confirmada**, três tabelas com RLS, políticas restritas por `auth.uid()` e sem `GRANT` direto para `anon`.
- Reexecutei `infra/supabase/rls_role_rehearsal.sql`: seis booleans de segurança retornaram `true` e a transação encerrou em `ROLLBACK`. Isto valida papéis/claims PostgreSQL simulados, **não** duas sessões HTTP reais.
- O projeto já tinha três migrações. A migração adicional `20261025103735` criou apenas o índice não destrutivo `orbita_telegram_updates_user_id_idx`; leitura do catálogo confirmou sua existência, e o advisor deixou de sinalizar a chave estrangeira sem índice.
- `docs/cloud-config.js` no PR 7 contém a URL correta e uma chave **publicável habilitada**, confirmada contra o projeto Supabase, sem chave privilegiada.
- Advisor de segurança: **Leaked Password Protection Disabled** continua em `WARN`. Requer configuração de Auth e recurso disponível conforme plano; tabela `orbita_telegram_updates` sem política é **intencional**, porque usuários/anônimos não têm `GRANT` de consulta.
- Ainda **não** há segunda conta real de teste, chat de teste para isolamento via HTTP, validação de recuperação de senha, backup confirmado para SQL 002/003 ou aprovação de publicação. Sem novos flags habilitados. A PR 7 continua em rascunho e o site `main` fica inalterado.

## Confirmado em 24/10/2026
- Projeto `orbita` ativo na organização ORBITA, região São Paulo.
- As **três tabelas base** da memória estão presentes e têm RLS habilitado; a contagem de tabelas não significa que as migrações opcionais recentes foram aplicadas.
- Auditoria SQL de leitura de 24/10/2026 confirmou ausência de `orbita_action_proposals` e da RPC de confirmação (SQL 002 pendente) e ausência de `delivered` no constraint do webhook (SQL 003 pendente), preservando o estado legado `replied`.
- Site URL e URL de redirecionamento confirmadas visualmente: https://fhenriquefcruz.github.io/orbita/.
- Frontend de autenticação e chave publicável já preparados no PR 7; testes simulados aprovados.

## Bloqueadores antes de mesclar o PR 7
- **Supabase ORBITA está no plano Free (25/10/2026).** O projeto não tem histórico diário gerenciado de backups dos planos pagos. Ferramentas locais de exportação/verificação criadas na Aurora 3.25, mas backup ainda NÃO gerado nem restaurado. Exigir backup privado, integridade e restauração independente antes de SQL 002/003. Ver `quality/AUTH_BACKUP_ACTIVATION_GATE_3_25.md`.
- Revisar, aplicar somente após autorização e testar as migrações SQL 002/003 no projeto dedicado, repetindo `infra/supabase/preflight_readonly.sql` e o relatório `quality/SUPABASE_RELEASE_PREFLIGHT_3_21.md`.
- **Estado Auth real em 25/10/2026:** uma única conta Auth com e-mail confirmado, segunda conta autorizada ainda pendente. `quality/auth_dual_login_runner.py` pode autenticar as duas contas **localmente sem copiar JWTs**, logo após cadastro legítimo no Dashboard. Nenhum JWT/senha real foi utilizado nesta etapa; falta a prova HTTP com duas identidades distintas.
- Testar restauração de sessão, logout, redefinição de senha e links de recuperação reais.
- Ensaio PostgreSQL com `SET LOCAL ROLE` aprovado (Aurora 3.23). Suite Aurora 3.24 verifica a lógica de HTTP/JWT com transportes mockados; **a prova real depende de duas contas, sessões JWT legítimas e teste de escrita/exclusão com fixture controlado**. O chat real possui zero mensagens e não permite comprovar vazamento de conteúdo por leitura cruzada até haver um fixture autorizado.
- Testar reconciliação com backup, exclusão, recuperação e limpeza do cache PWA.
- Realizar smoke test em Safari/iPhone, Android/Chrome e desktop.
- Avaliar o aviso de proteção contra senhas vazadas desabilitada apresentado pelo auditor.

## Segurança
- O GitHub Pages publica HTML e JavaScript; a privacidade dos dados persistidos depende de RLS.
- Não adicionar credenciais privilegiadas ao código ou a arquivos públicos.
- Dados locais do navegador não são criptografados, mesmo depois do login.
- O webhook Telegram e os fluxos naturais em nuvem não são considerados ativos/homologados até implantação das credenciais privadas e testes reais do titular.
- As flags `ORBITA_NATURAL_ACTIONS_ENABLED` e `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` permanecem desligadas por padrão; um preflight de esquema aprovado NÃO autoriza publicação.

**Resultado:** infraestrutura preparada; publicação do login ainda não homologada.
