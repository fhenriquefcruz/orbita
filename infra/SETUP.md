# ORBITA 3.0 — Infraestrutura: guia de ativação segura

> **Situação em 24/10/2026:** projeto Supabase exclusivo ORBITA (`tbqfymedgdsdrgkqmuni`) já criado em São Paulo; migrações 001–003 aplicadas. Backend Vercel `orbita-api` compilado, porém Telegram **não ativado**. A autenticação real do painel e os testes de isolamento continuam em homologação (PR #7). Consulte `infra/TELEGRAM_ACTIVATION.md` para o procedimento atualizado.

## Arquitetura

- `docs/`: GitHub Pages. Guarda dados locais no navegador e pode conciliá-los **sob demanda** com Supabase depois de login; jamais contém chaves privilegiadas.
- `infra/supabase/001_core.sql`: tabelas `orbita_records`, `orbita_chat_messages`, `orbita_telegram_updates`, RLS por usuário, índices.
- `telegram/bot.py`: polling para uso local ou servidor contínuo. Banco SQLite quando as 3 opções Supabase estão vazias; caso contrário usa a memória central.
- `api/index.py`: webhook FastAPI para execução em hospedagem HTTPS compatível (por exemplo Vercel), com token secreto do webhook e proprietário restrito. **Polling e webhook não devem operar simultaneamente**.
- `requirements.txt` e `vercel.json`: dependência e roteamento preliminar para Vercel; deploy remoto ainda requer validação de rota e duração de execução.

## Passos para conectar sem publicar segredos

1. **Concluído:** projeto `orbita` na organização `ORBITA`, região `sa-east-1`, plano Free (cotação de criação US$ 0/mês). Outros bancos não foram reutilizados.
2. Executar `infra/supabase/001_core.sql` no SQL Editor desse projeto. Executar advisors de segurança e verificar RLS com duas contas independentes.
3. Em Supabase Auth, criar/autorizar sua conta de acesso ao painel. Copiar **somente a URL pública e a chave `sb_publishable_...`** para `docs/cloud-config.js`. Esta chave é publicável e fica limitada pelo RLS. Não habilitar inscrição irrestrita sem necessidade.
4. Publicar o frontend pelo GitHub Pages. Em **Dados e histórico → Memória central**, autenticar com sua conta. Primeiro revisar e baixar backup; depois escolher **Conciliar registros agora**. Conflitos usam `updated_at` mais recente; exclusões recebem tombstones. Não apagar o backup original antes de confirmar ambos os lados.
5. Revogar o token Telegram que foi exposto no chat anterior. Gerar um token NOVO no BotFather, guardar somente em env privados. Com o bot local em execução, enviar `/id` e preencher `ORBITA_OWNER_ID`.
6. Configurar **somente no servidor**: `TELEGRAM_BOT_TOKEN`, `ORBITA_OWNER_ID`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (`sb_secret_...`), `ORBITA_USER_UUID` (UUID da mesma conta Supabase Auth do passo 3), `OPENAI_API_KEY` (opcional) e `OPENAI_MODEL`. Essas variáveis **não** podem ir para o GitHub Pages nem para o frontend.
7. Para o webhook, adicionar `TELEGRAM_WEBHOOK_SECRET` privado (segredo aleatório de 1 a 256 caracteres `A-Z a-z 0-9 _ -`). Hospedar `api/index.py` por HTTPS e verificar `/api/health`. Cadastrar webhook no BotFather/Telegram `setWebhook` com a **URL completa** da rota `/api/telegram` e o parâmetro `secret_token` idêntico. Nunca usar URL com token no repositório, Issue, logs ou conversa. O `getUpdates` não funciona enquanto webhook estiver ativado.
8. Testar mensagem de usuário autorizado e bloqueio de terceiro, criação `/tarefa`, consulta `/tarefas`, atualização `/feito`, conversa com Vânia. Confirmar que registros aparecem no Supabase e, após conciliação manual, no painel.
9. **Não ativar resumos automáticos** até existirem rotinas agendadas, deduplicação, verificação de timezone, limites e opção de desligar. Apenas os horários desejados estão registrados.

## Segurança

- `sb_secret_...` é uma chave privilegiada, bypass RLS; não entra em código de cliente, nem em commits, nem em testes de browser.
- Token de sessão da interface fica **somente em memória da página**: ao recarregar, é necessário entrar novamente. Não usar dados confidenciais antes do teste de políticas RLS.
- A memória do ChatGPT **não é transferida automaticamente**. O bot só consulta o conteúdo efetivamente salvo na base ORBITA.
- No primeiro login, um navegador pode estar vinculado a uma única conta Supabase para impedir envio acidental de dados locais a outro usuário. Usar perfis separados para outras contas.
- A sincronização é **manual, não em tempo real** nesta entrega. Não afirmar que alterações feitas no Telegram aparecem instantaneamente no painel.
- Uma falha de rede durante a sincronização pode deixar operações parciais, mas o backup local prévio permite recuperação. Repetir a conciliação quando o serviço estiver disponível, sem apagar dados.

## Testes

```bash
python -m unittest discover -s telegram/tests -v
node --test quality/test_cloud_core.cjs
node --check docs/cloud-sync.js
```

A execução acima não equivale a teste E2E com Supabase/Telegram reais. Validar também o backend publicado, Safari iPhone, Android, acessibilidade e fluxo de login antes da homologação.
