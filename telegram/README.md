# ORBITA 2.2 — Telegram, Vânia e memória local

**Estado:** primeira ponte local de testes. **Não está hospedada, não envia resumos automáticos, não recebe áudios e não está sincronizada com a PWA.**

## 0. Antes de tudo: segurança

O token antigo do BotFather foi compartilhado numa conversa e precisa ser **revogado**. Abra `https://t.me/BotFather`, envie `/revoke`, escolha `@orbita_assistente_bot` e gere um token novo. **Não use o anterior e não compartilhe o novo.** Também é possível obter novo token em `/token` após revogar o antigo.

## 1. O que esta versão faz

- Recebe e responde mensagens **diretamente no Telegram**, mas somente enquanto o script estiver executando.
- Restringe o acesso a **um usuário** (`ORBITA_OWNER_ID`). Antes de definir esse ID, o bot responde somente `/id` e `/start`.
- Registra tarefas e ideias em `orbita.sqlite3` (arquivo local persistente).
- Lista tarefas, conclui registros e gera uma **prévia manual** do resumo.
- Se houver uma chave API OpenAI, conversa em linguagem natural com Vânia e consulta os registros da memória, sem alterá-los automaticamente.
- Em consultas, Vânia pode mencionar outros personagens, mas ainda não existem sete agentes independentes.
- **Não possui disparos automáticos, cron nem permissões de acesso à agenda.**

## 2. Iniciar no Windows (PowerShell ou Prompt)

1. Instale Python 3.11 ou superior de `https://www.python.org/downloads/` (caso ainda não tenha).
2. Descompacte este projeto numa pasta apenas sua.
3. Dentro da pasta, copie `.env.example` para `.env` (no Windows, ative "Mostrar extensões de arquivo").
4. Abra `.env` num editor de texto e substitua o campo `TELEGRAM_BOT_TOKEN` **somente pelo token NOVO**, após a revogação.
5. Deixe `ORBITA_OWNER_ID=0` por enquanto.
6. Abra o terminal nessa pasta e execute:

```powershell
py bot.py
```

Se `py` não for reconhecido, tente `python bot.py`.

7. Abra `https://t.me/orbita_assistente_bot` e envie `/start` ou `/id`. O bot mostrará seu **Telegram ID**.
8. Altere `ORBITA_OWNER_ID=0` para esse número no `.env`, salve e reinicie o script (`Ctrl+C`, depois `py bot.py`).
9. Teste no Telegram:

```
/tarefa P1 | Validar conversa com a Vânia
/tarefas
/ideia Criar painel integrado ao Telegram
/ideias
/resumo
```

**Importante:** não publique o `.env` e nem o arquivo `orbita.sqlite3`. Eles podem conter dados privados.

## 3. Habilitar IA OpenAI (opcional, separado da assinatura ChatGPT)

1. No painel da API em `https://platform.openai.com/`, crie um projeto para ORBITA.
2. Configure orçamento e, se disponível, limite rígido de gastos; verifique a cobrança.
3. Gere uma chave de API restrita a esse projeto, guardando-a **somente no `.env` local** como `OPENAI_API_KEY`.
4. Confira se `OPENAI_MODEL` está disponível na sua conta (sugestão inicial: `gpt-5-mini`; pode ser substituído).
5. Reinicie o `bot.py` e envie texto normal: `Vânia, organize minhas prioridades`.

A IA recebe apenas o contexto local recente (até 10 mensagens) e até 45 registros da base. Ela **não recupera automaticamente** memórias do ChatGPT, arquivos do Google Drive ou outros projetos.

## 4. Configurar o perfil do bot

Use o conteúdo de `BOTFATHER.txt` para configurar descrição, texto curto e comandos pelo @BotFather.

## 5. Regras preservadas (não ativadas)

- Vânia: resumos às **07:30** e **18:00**.
- Silêncio **20:00–07:30** em `America/Campo_Grande`.
- Apenas exceções importantes durante silêncio.
- Prioridades P0, P1, P2 e P3.

Essas regras são **requisitos de projeto**. Não existe motor de notificações automático nesta versão, portanto nada será enviado por horário.

## 6. Limitações e próximos passos

- **Teste local:** PC desligado = bot indisponível. Para 24h, configurar infraestrutura.
- **SQLite não criptografado:** não cadastre segredos, prontuários ou dados confidenciais. Proteger a pasta, disco e backups.
- Não há processamento de áudio/fotos, calendar sync, exclusão de tarefas, autenticação web, notificações ou API de memória compartilhada com a PWA.
- Próxima versão: API backend autenticada, PostgreSQL, webhooks com segredo, filas, integrações agenda + dashboard, camada de agendamento e classificação de exceções.
- Para desativar imediatamente o bot local, pressione `Ctrl+C`. Para invalidar a credencial, utilize o BotFather.

## 7. Desenvolvimento e testes

Requer somente a biblioteca padrão do Python; sem `pip install`.

```powershell
py -m unittest discover -s tests -v
```