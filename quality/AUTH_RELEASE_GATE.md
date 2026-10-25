# ORBITA 3.0 — Homologação do Supabase Auth

## Confirmado em 24/10/2026
- Projeto `orbita` ativo na organização ORBITA, região São Paulo.
- As **três tabelas base** da memória estão presentes e têm RLS habilitado; a contagem de tabelas não significa que as migrações opcionais recentes foram aplicadas.
- Auditoria SQL de leitura de 24/10/2026 confirmou ausência de `orbita_action_proposals` e da RPC de confirmação (SQL 002 pendente) e ausência de `delivered` no constraint do webhook (SQL 003 pendente), preservando o estado legado `replied`.
- Site URL e URL de redirecionamento confirmadas visualmente: https://fhenriquefcruz.github.io/orbita/.
- Frontend de autenticação e chave publicável já preparados no PR 7; testes simulados aprovados.

## Bloqueadores antes de mesclar o PR 7
- **Confirmar backup recuperável** (automático ou dump lógico privado com plano de restauração) antes de aplicar permanentemente SQL 002/003. A ferramenta conectada não oferece verificação/execução de backups oficiais. Ver `quality/SECURE_ROLLOUT_3_23.md`.
- Revisar, aplicar somente após autorização e testar as migrações SQL 002/003 no projeto dedicado, repetindo `infra/supabase/preflight_readonly.sql` e o relatório `quality/SUPABASE_RELEASE_PREFLIGHT_3_21.md`.
- Verificar login real de proprietário e e-mail confirmado (a consulta automatizada de usuários foi bloqueada pela ferramenta).
- Testar restauração de sessão, logout, redefinição de senha e links de recuperação reais.
- Ensaio PostgreSQL com `SET LOCAL ROLE` aprovado (Aurora 3.23: proprietário vê seu registro, identidade não proprietária vê zero, `anon` e atualizações privadas protegidos). **Ainda falta testar RLS por HTTP entre duas contas autenticadas distintas com tokens JWT reais**, dados de teste e limpeza posterior.
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
