# ORBITA — Ativação segura do Telegram

**Situação verificada em 24/10/2026:** o banco Supabase `orbita` e suas 3 migrações estão operacionais. O projeto Vercel `orbita-api` possui implantação `READY` ligada ao GitHub, porém o webhook **não está ativo**. O projeto ainda exige credenciais privadas e configuração de acesso público restrito ao endpoint do Telegram. A memória do painel sincroniza manualmente.

## A arquitetura

`Seu Telegram` → `@orbita_assistente_bot` → `POST https://orbita-api-olive.vercel.app/api/telegram` → `FastAPI (segredo + ID proprietário)` → `Supabase ORBITA`. Opcionalmente, respostas livres usam OpenAI API (cobrança à parte). A chave Supabase `sb_secret_` não deve ir ao navegador.

## Ações do proprietário

1. Em [@BotFather](https://t.me/BotFather), selecione `/mybots` → bot `@orbita_assistente_bot` → API Token. Como uma credencial anterior já foi compartilhada em uma conversa, **revogue/substitua-a antes de ativar** (a interface pode oferecer `/revoke` ou gerar novo token). **Não copie para chats, issues, commits ou GitHub Pages.**
2. Abra uma conversa privada com o bot e envie `/start`; bots só podem responder depois de iniciados pelo usuário.
3. Descubra o **seu Telegram numeric user ID** (não é o identificador do bot). Pode obtê-lo por `getUpdates` do seu próprio bot **antes** de ligar webhook, com um script local protegido, ou por um serviço informativo de sua escolha (este último exige fornecer dados básicos a um terceiro). Anote-o para `ORBITA_OWNER_ID`.
4. No [Supabase Authentication Users](https://supabase.com/dashboard/project/tbqfymedgdsdrgkqmuni/auth/users), confirme sua conta e copie seu **User UID** UUID. O UUID deve identificar exatamente a conta que será usada no painel: `ORBITA_USER_UUID`.
5. Em [Supabase API Keys](https://supabase.com/dashboard/project/tbqfymedgdsdrgkqmuni/settings/api-keys), crie/obtenha uma **secret key** `sb_secret_...` exclusivamente para o backend Vercel. Não reutilize a chave publicável.
6. Em [Vercel Environment Variables](https://vercel.com/rtm11/orbita-api/settings/environment-variables), configure as variáveis abaixo **para Production**. Use o tipo encrypted/sensitive para tokens, senhas e chaves; nunca coloque segredos como variáveis públicas. Depois, faça redeploy de produção para aplicar os valores.

| Variável | Valor / origem |
| --- | --- |
| `SUPABASE_URL` | **Já criada** na Vercel: `https://tbqfymedgdsdrgkqmuni.supabase.co` |
| `SUPABASE_SECRET_KEY` | Secret API Key do projeto Supabase `orbita` (privada) |
| `ORBITA_USER_UUID` | Auth → Users → User UID da conta autorizada |
| `ORBITA_OWNER_ID` | ID numérico do proprietário no Telegram |
| `TELEGRAM_BOT_TOKEN` | Novo token privado gerado por BotFather após revogação |
| `TELEGRAM_WEBHOOK_SECRET` | Segredo aleatório separado do token do bot, com 32+ caracteres `A-Z a-z 0-9 _ -` |
| `OPENAI_API_KEY` | **Opcional** — habilita conversação com IA; não é necessária para os comandos básicos |
| `OPENAI_MODEL` | **Opcional**; usar modelo suportado pelo servidor e sua conta OpenAI |

## Preparação segura do webhook

- Verificar HTTPS e `GET /api/health` no domínio público **de produção** da Vercel, que deve retornar JSON e `webhook_configured:true` somente quando o ambiente estiver corretamente configurado.
- As implantações Vercel individuais e previews podem estar sob Vercel Authentication; o Telegram **não consegue autenticar-se na Vercel**. Manter previews protegidos, mas tornar alcançável a **URL de produção** do webhook via configurações de Deployment Protection, sem eliminar o cabeçalho secreto exigido pelo FastAPI. Não abrir outros endpoints sensíveis.
- **Somente após essa verificação**, cadastrar no Telegram o webhook com `setWebhook` (Bot API) usando a URL HTTPS `https://orbita-api-olive.vercel.app/api/telegram` e `secret_token` **idêntico** a `TELEGRAM_WEBHOOK_SECRET` salvo na Vercel. Preferir cliente/script local que leia segredos do ambiente, sem imprimir token na tela, colar em URL de navegador ou deixar em histórico de terminal.
- Conferir `getWebhookInfo`, `pending_update_count` e `last_error_message` (não copiar respostas que exponham credenciais para locais públicos).
- O Telegram reenvia atualizações com falha de HTTP; o webhook salva a resposta como `replied` antes de enviá-la e marca `processed` depois. Há possibilidade limitada de **resposta duplicada** se o ACK do banco falhar após o envio — não prometer exatamente uma vez.

## Homologação

1. Enviar `/ajuda`, `/tarefa P1 | Testar ORBITA`, `/tarefas`, `/feito <numero>`, `/ideia Teste` e `/resumo`. O ID numérico usado em `/feito` vem da resposta do bot.
2. Confirmar que um remetente não autorizado é **ignorado** e uma requisição sem cabeçalho secreto é **rejeitada**.
3. Confirmar `orbita_records` e `orbita_chat_messages` no Supabase da conta correta, sem mostrar dados de outro titular.
4. Fazer login no painel Aurora 3.3 e, após **backup**, usar `Dados e histórico → Memória central → Conciliar registros agora`. A sincronização **não é em tempo real**.
5. Testar recuperação, reinício de implantação, timeout e duplicata antes de uso contínuo. Não habilitar resumos proativos enquanto não existir agendador real e monitorado.

## Se algo falhar / desligamento

- Mensagem não chega: conferir `getWebhookInfo`, proteção Vercel, deploy Production, logs do webhook sem imprimir tokens e `/api/health`.
- Erro HTTP 403 no endpoint: conferir apenas `secret_token` e origem; **não remova** a validação de assinatura/ID proprietário.
- HTTP 503: alguma variável essencial ausente, Supabase inacessível ou erro no envio.
- Para interromper totalmente, usar `deleteWebhook` e remover token/segredos da implantação Vercel. Não ativar polling paralelo ao webhook.
- A camada de IA é opcional; sem `OPENAI_API_KEY`, comandos estruturados continuam previstos no bot.

**Fontes:** https://core.telegram.org/bots/api · https://core.telegram.org/bots/features · https://vercel.com/docs/deployment-protection · https://supabase.com/docs/guides/getting-started/api-keys

**Não incluir credenciais neste documento ou no ChatGPT.**
