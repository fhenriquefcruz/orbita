# ORBITA 3.5 — Segurança de sessão e isolamento de contas

## Contexto real (24/10/2026)

- O webhook do bot Telegram está ativo; três atualizações previamente confirmadas como `processed` no Supabase e uma tarefa P1 persistida.
- Projeto Supabase ORBITA `tbqfymedgdsdrgkqmuni`: **1 conta Auth real**. A separação entre contas reais ainda NÃO foi homologada por HTTP com dois usuários independentes.
- Policies em `orbita_records` e `orbita_chat_messages`: leitura/gravação específicas do `auth.uid() = user_id`. `orbita_telegram_updates` está reservado ao backend, sem concessão de acesso ao cliente.
- Smoke read-only executado diretamente no Postgres, trocando `SET LOCAL ROLE authenticated` e `request.jwt.claim.sub` em transações: a conta proprietária enxerga o registro; identidade simulada independente recebe zero registros. **Não equivale ao login de um segundo usuário real.**
- Advisors de segurança: `orbita_telegram_updates` sem policy é intencional; aviso de **Leaked Password Protection Disabled** continua pendente, conforme https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Implementação

1. Antes de exibir contagem ou prévia de Telegram, o Aurora confirma que ainda há uma sessão autenticada da mesma conta que iniciou a consulta. Uma resposta antiga de outra conta é ignorada.
2. Durante conciliação manual, a conta de início é capturada e checada após a leitura, antes de cada criação/exclusão e antes de atualizar o armazenamento local; caso a sessão seja trocada, aborta a operação sem gravar localmente e informa possível parcialidade remota. Mantém download e confirmação explícitos do backup.
3. As gravações enviam `user_id` da conta capturada inicialmente, não de estado global que possa ser alterado.
4. `quality/browser_smoke.py` agora simula duas identidades coerentes em `/auth/v1/token` e `/auth/v1/user`. Um segundo navegador sem dados locais não pode visualizar registros do primeiro usuário (o mock retorna GET vazio); no mesmo navegador, a vinculação local bloqueia login com usuário distinto após logout.
5. Cache PWA atualizado para `orbita-pages-v3.5.0-isolation.1`.

## Limites e próximos critérios antes de publicar a branch de Auth

- O smoke browser prova **comportamento da interface e do mock**; não valida o RLS real do PostgREST com dois JWTs legítimos.
- Criar uma **segunda conta de teste autorizada** via Supabase Auth (sem compartilhar senha, sem inserções SQL em `auth.users`), validar GET/POST/PATCH/DELETE cruzados com ambas as sessões via API e remover a conta de teste quando não for mais necessária.
- Validar link de recuperação de senha no domínio homologado em iPhone Safari e Windows.
- Revisar configuração de proteção contra senhas vazadas no Supabase Auth e deixar inscrição pública desativada se o serviço continuar pessoal.
- Testar `/feito 1` no Telegram apenas após decidir concluir a tarefa de homologação. Sua tarefa real não é alterada por estes testes.
- Uma chave `OPENAI_API_KEY` é opcional e somente deve ser cadastrada em servidor privado se o usuário decidir ativar conversas livres. Não faz parte da entrega 3.5.

## Regressões evitadas

- Nenhum valor `sb_secret_`, chave de bot ou senha deve ser guardado no frontend, nos mocks ou no GitHub.
- Não realizar escrita silenciosa na memória, sincronização automática ou release na `main` sem os gates de homologação.
