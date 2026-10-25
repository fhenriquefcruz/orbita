# ORBITA Aurora 3.17 — Conversa natural com Vânia

## Resposta sobre a experiência
Vânia **já possui rota conversacional livre** por texto no Telegram:
`telegram/bot.py` faz chamadas para `POST /v1/responses` quando a variável
privada `OPENAI_API_KEY` está presente. Sem chave, informa a limitação e
permite os comandos tradicionais. A API tem cobrança independente do ChatGPT.

No modo cloud, o histórico de conversa é armazenado em
`public.orbita_chat_messages` no Supabase do titular; no modo local usa SQLite.
As tarefas e ideias entram no contexto da IA como dados, sem autorizar
execução por texto livre.

## Melhoria desta etapa
- Instruções de personalidade profissional, diálogo direto e continuidade em
  português, sem saudações/listas redundantes.
- Referências como "isso", "aquela tarefa" e "continue" usam o histórico
  anterior, nunca inventando contexto indisponível.
- Janela recuperada de 10 para 16 mensagens (até oito turnos completos),
  podendo elevar o consumo de tokens na API.
- Resposta máxima do modelo de 850 para 1100 tokens; respostas concisas
  continuam sendo preferência por padrão.
- Delimitação explícita entre sugestão e ação: linguagem livre **não grava**
  registros; para executar uma tarefa, mostrar o comando necessário.
- Preserva `/tarefa`, `/feito`, `/ideia`, recuperação de status e resumos
  manuais sem alterar o contrato do banco e do webhook.

## Testes executados por CI (sem uso de chave real)
`telegram/tests/test_natural_chat.py` verifica:
1. Duas mensagens em sequência com contexto transmitido à API e histórico salvo.
2. Pedido de tarefa em linguagem livre não cria registro silenciosamente.
3. Ausência da API retorna instrução clara sem gravar a conversa.
4. HTTP 429 não confirma sucesso nem salva mensagem parcial.
5. Comandos continuam independentes do modelo, mesmo com API habilitada.
6. Limite de 16 mensagens anteriores e preservação da ordem.
7. Títulos maliciosos permanecem dados do contexto, não comandos executados.

## Situação operacional
A inspeção do código **não** verifica se `OPENAI_API_KEY` está configurada
na hospedagem. Não gravar segredos em PR, repositório, logs ou no navegador.
Verificar a existência (não o valor) da variável no ambiente privado e testar
mensagem real antes de afirmar conversação ativada. O código não possui
entrada de áudio nem interpretação de mensagens de voz.

## Próximo marco: ações naturais com confirmação segura
Contrato de produto proposto:
- "Vânia, anote que preciso enviar o documento amanhã" gera prévia de tarefa.
- Vânia devolve título, prioridade e eventual data, sem afirmar que salvou.
- Usuário revisa e confirma por botão ou texto explícito.
- O servidor verifica identidade do Telegram, titular do Supabase, prazo de
  expiração da proposta, revisão, limites e idempotência antes de gravar.
- Bot comunica sucesso **somente** após confirmação persistida no banco.
- Cancelamento, resposta ambígua e expiração não escrevem nada.
- Manter comandos como alternativa avançada. Não iniciar notificações
  automáticas sem autorização.
- Proposta deve sobreviver a reinicializações serverless e não depender de
  memória de processo ou interpretação de conversa antiga para confirmação.

**Atenção:** esta etapa futura requer modelo de propostas pendentes persistente,
regras de confirmação e testes de concorrência. Não foi introduzida de maneira
improvisada na Aurora 3.17.

## Gates de publicação
A PR #7 (Auth) continua rascunho: falta login real com duas contas, RLS HTTP,
recuperação de senha e Safari/iPhone. O novo incremento é isolado da `main`
e não modifica ambiente produtivo nem ativa IA automaticamente.
