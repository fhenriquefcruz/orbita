# ORBITA 3.0 — Infraestrutura: guia de ativação segura

> **Estado atualizado em 26/10/2026:** o Supabase exclusivo ORBITA tem duas contas Auth reais e o isolamento HTTP de registros/chat passou. As migrações históricas `002_least_privilege` e `003_telegram_reply_delivery` já estão aplicadas; as **outras** SQLs `002_action_proposals` e `003_telegram_delivery` estão BLOQUEADAS até backup restaurável e autorização. Webhook real, recuperação de senha/Safari e liberação da `main` ainda pendentes. Não usar bancos de outros projetos.

## Arquitetura

- `docs/`: GitHub Pages. Bloqueia todas as telas até Supabase Auth validar a sessão; guarda dados locais no navegador e concilia **sob demanda**; jamais contém chaves privilegiadas.
- `infra/supabase/001_core.sql`: tabelas `orbita_records`, `orbita_chat_messages`, `orbita_telegram_updates`, RLS por usuário, índices.
- `telegram/bot.py`: polling para uso local ou servidor contínuo. Banco SQLite quando as 3 opções Supabase estão vazias; caso contrário usa a memória central.
- `api/index.py`: webhook FastAPI para execução em hospedagem HTTPS compatível (por exemplo Vercel), com token secreto do webhook e proprietário restrito. **Polling e webhook não devem operar simultaneamente**.
- `requirements.txt` e `vercel.json`: dependência e roteamento preliminar para Vercel; deploy remoto ainda requer validação de rota e duração de execução.

## Passos para conectar sem publicar segredos

1. **Projeto dedicado:** o Supabase exclusivo `orbita` já foi confirmado na organização ORBITA (região `sa-east-1`). Não recriar ou reutilizar bancos alheios; conferir sempre a identidade do projeto antes de operar.
2. **Base:** `infra/supabase/001_core.sql` está refletido nas três tabelas e no RLS existentes. Antes de qualquer novo rollout, executar SOMENTE a consulta `infra/supabase/preflight_readonly.sql` e conferir `quality/SUPABASE_RELEASE_PREFLIGHT_3_21.md`. As migrações **002 (propostas)** e **003 (entrega Telegram)** não foram aplicadas e não devem ser executadas sem revisão, backup e homologação. Verificar isolamento RLS com duas contas reais.
3. Em **Authentication → Users**, criar/convidar somente os usuários autorizados. Em **Authentication → URL Configuration**, definir **Site URL** e **Redirect URLs** como `https://fhenriquefcruz.github.io/orbita/` (com barra final). Validar entrega de e-mails de recuperação (SMTP próprio em produção). Em **Authentication → Providers → Email**, evitar inscrição pública se o ORBITA for restrito ao proprietário. A interface não oferece auto-cadastro.
4. Copiar **somente a URL pública e a chave `sb_publishable_...`** para `docs/cloud-config.js`. Esta chave é publicável e fica limitada pelo RLS. Nunca colocar `sb_secret_...` ou token de Telegram no navegador.
5. Publicar o frontend pelo GitHub Pages. O endereço `https://fhenriquefcruz.github.io/orbita/` deve exibir o **login antes de qualquer tela do painel**. Após entrar, abrir `#/data` ou **Dados e histórico → Memória central**. Primeiro revisar e exportar um backup; depois escolher **Conciliar registros agora**. Conflitos usam `updated_at` mais recente; exclusões recebem tombstones. Não apagar o backup original antes de confirmar ambos os lados.
6. Revogar o token Telegram que foi exposto no chat anterior. Gerar um token NOVO no BotFather, guardar somente em env privados. Com o bot local em execução, enviar `/id` e preencher `ORBITA_OWNER_ID`.
7. Configurar **somente no servidor**: `TELEGRAM_BOT_TOKEN`, `ORBITA_OWNER_ID`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (`sb_secret_...`), `ORBITA_USER_UUID` (UUID da mesma conta Supabase Auth do passo 3), `OPENAI_API_KEY` (opcional) e `OPENAI_MODEL`. Essas variáveis **não** podem ir para o GitHub Pages nem para o frontend.
8. Para o webhook, adicionar `TELEGRAM_WEBHOOK_SECRET` privado (segredo aleatório de 1 a 256 caracteres `A-Z a-z 0-9 _ -`). Hospedar `api/index.py` por HTTPS e verificar `/api/health`. Cadastrar webhook no BotFather/Telegram `setWebhook` com a **URL completa** da rota `/api/telegram` e o parâmetro `secret_token` idêntico. Nunca usar URL com token no repositório, Issue, logs ou conversa. O `getUpdates` não funciona enquanto webhook estiver ativado.
9. Testar mensagem de usuário autorizado e bloqueio de terceiro, criação `/tarefa`, consulta `/tarefas`, atualização `/feito`, conversa com Vânia. Confirmar que registros aparecem no Supabase e, após conciliação manual, no painel.
10. **Não ativar resumos automáticos** até existirem rotinas agendadas, deduplicação, verificação de timezone, limites e opção de desligar. Apenas os horários desejados estão registrados.

## Segurança

- `sb_secret_...` é uma chave privilegiada, bypass RLS; não entra em código de cliente, nem em commits, nem em testes de browser.
- O token da sessão do painel fica em **`sessionStorage`**, exclusivamente no navegador; sobrevive à recarga na mesma aba e é removido ao sair/fechar a aba. A interface só abre após `GET /auth/v1/user` verificar a conta. Um refresh token permite renovar a sessão. Não usar dados confidenciais antes do teste real do RLS.
- A memória do ChatGPT **não é transferida automaticamente**. O bot só consulta o conteúdo efetivamente salvo na base ORBITA.
- Na primeira entrada, o navegador é vinculado à conta Supabase. Se já houver registros legados, a associação exige consentimento explícito. Contas distintas devem usar perfis separados; armazenamento local **não é criptografado** e autenticação visual não substitui proteção no dispositivo.
- Rotas `#/home`, `#/chat`, `#/records`, `#/summaries`, `#/team`, `#/rules`, `#/data` têm **guarda de sessão na interface**, mas a autorização de dados depende do RLS em toda API e de verificação de JWT no backend. **O GitHub Pages não é um servidor privado**: HTML, CSS e JS continuam públicos.
- A sincronização é **manual, não em tempo real** nesta entrega. Não afirmar que alterações feitas no Telegram aparecem instantaneamente no painel.
- Uma falha de rede durante a sincronização pode deixar operações parciais, mas o backup local prévio permite recuperação. Repetir a conciliação quando o serviço estiver disponível, sem apagar dados.

## Testes

```bash
python -m unittest discover -s telegram/tests -v
node --test quality/test_cloud_core.cjs
node --check docs/auth.js
node --check docs/cloud-sync.js
```

A execução acima não equivale a teste E2E com Supabase/Telegram reais. Validar também o backend publicado, Safari iPhone, Android, acessibilidade e fluxo de login antes da homologação.

## Homologação da autenticação e rotas protegidas

- Sem URL/chave ou sem sessão válida, **nenhuma view** do painel deve abrir; endereço direto `#/records` também exige login.
- Fazer login com uma conta, criar registro, recarregar a página e comprovar permanência da sessão na mesma aba.
- Trocar para `#/chat` e `#/data`, voltar, encerrar sessão e confirmar que o painel volta a ficar oculto.
- Abrir link de recuperação recebido por e-mail, atualizar senha, entrar com a nova senha e verificar que o link não dá acesso automático ao painel.
- Com duas contas independentes e RLS, garantir que leituras, gravações e exclusões cruzadas são negadas no Supabase, independentemente da proteção visual.
- Executar `python quality/browser_smoke.py` com Playwright e Chromium instalados. O mock só testa interface/fluxos; **não** substitui autenticação e isolamento RLS reais.

**Ativação bloqueada:** Auth/RLS **HTTP real aprovado** com duas contas; ainda faltam backup restaurado isoladamente, SQL opcional `002_action_proposals`/`003_telegram_delivery`, recuperação Auth em dispositivos e Telegram em produção. As flags `ORBITA_NATURAL_ACTIONS_ENABLED` e `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` seguem OFF por padrão. A branch `main` permanece preservada.
