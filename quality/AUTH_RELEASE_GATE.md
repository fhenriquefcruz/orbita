# ORBITA 3.0 — Homologação do Supabase Auth

## Confirmado em 24/10/2026
- Projeto `orbita` ativo na organização ORBITA, região São Paulo.
- Três migrações executadas e RLS habilitada nas três tabelas da memória.
- Site URL e URL de redirecionamento confirmadas visualmente: https://fhenriquefcruz.github.io/orbita/.
- Frontend de autenticação e chave publicável já preparados no PR 7; testes simulados aprovados.

## Bloqueadores antes de mesclar o PR 7
- Verificar login real de proprietário e e-mail confirmado (a consulta automatizada de usuários foi bloqueada pela ferramenta).
- Testar restauração de sessão, logout, redefinição de senha e links de recuperação reais.
- Testar RLS entre duas contas autenticadas distintas com dados de teste e limpeza posterior.
- Testar reconciliação com backup, exclusão, recuperação e limpeza do cache PWA.
- Realizar smoke test em Safari/iPhone, Android/Chrome e desktop.
- Avaliar o aviso de proteção contra senhas vazadas desabilitada apresentado pelo auditor.

## Segurança
- O GitHub Pages publica HTML e JavaScript; a privacidade dos dados persistidos depende de RLS.
- Não adicionar credenciais privilegiadas ao código ou a arquivos públicos.
- Dados locais do navegador não são criptografados, mesmo depois do login.
- O webhook Telegram permanece inativo até implantação das credenciais privadas e autorização do titular.

**Resultado:** infraestrutura preparada; publicação do login ainda não homologada.
