# ORBITA Aurora 3.19 — Botões de confirmação no Telegram

Esta etapa remove a fricção de copiar o código após criar proposta de tarefa
ou ideia em linguagem natural. A resposta da Vânia inclui dois botões nativos
Telegram InlineKeyboard: **✅ Confirmar** e **✕ Cancelar**, além dos comandos de
texto (alternativa acessível).

## Protocolo
- Botões aparecem somente em mensagens que correspondem ao modelo local da
  prévia de proposta emitida pelo ORBITA; propostas existem e expiram no banco,
  não apenas na mensagem visual.
- `callback_data` está limitada a `orbita:confirm:XXXXXXXXXXXX` ou
  `orbita:cancel:XXXXXXXXXXXX`, com 12 caracteres hexadecimais em caixa alta,
  abaixo de 64 bytes.
- Polling e webhook aceitam `callback_query`. Em ambos os modos, verificam
  chat privado, identidade Telegram autorizada e código antes de chamar
  `reply_text`. Callback inválido não chama armazenamento.
- A confirmação passa pelo mesmo `confirm_proposal` idempotente da Aurora
  3.18, não por uma rota paralela sem validações. O botão **não** significa
  autorização por si só.
- Em sucesso, o bot envia uma mensagem de confirmação ou resposta de
  idempotência; `answerCallbackQuery` encerra a animação de espera.
- Na nuvem, se `ORBITA_NATURAL_ACTIONS_ENABLED` não estiver em `1`,
  nenhum botão pode gravar, mesmo que um usuário acione uma mensagem antiga.
- `getUpdates` do polling é configurado para `message` e
  `callback_query`. Não rodar simultaneamente com o webhook.

## Testes
- `telegram/tests/test_proposal_transport.py` valida teclado, tamanho,
  payload malformado e respostas sem proposta.
- `telegram/tests/test_webhook.py` testa dono autorizado, outro usuário e
  callback malformado, incluindo caminho de envio e reconhecimento de botão.
- Regressão de `test_action_proposals.py`, `test_cloud_proposals.py`,
  `test_natural_chat.py` e testes preexistentes deve continuar aprovada.

## Limitações
- A existência dos botões na versão publicada requer deploy homologado; não
  foram feitos testes no aplicativo Telegram real.
- Botões em mensagens expiradas continuam visualmente presentes: tocar neles
  retornará uma mensagem indicando proposta inválida/expirada, nunca criará a
  tarefa. Remoção automática dos botões antigos é melhoria posterior.
- Enviar resposta e reconhecer callback são chamadas HTTP separadas à API do
  Telegram; falha de rede pode impedir a mensagem de confirmação de chegar,
  embora a operação no banco tenha concluído. O usuário pode consultar
  `/tarefas` e repetir o botão para recuperar o mesmo identificador.
- A fila `orbita_telegram_updates` protege contra retransmissão do mesmo
  update; recuperação de entrega pós-crash precisa de um protocolo de outbox
  transacional próprio antes de produção crítica.

**Gate:** manter em homologação e a migração da Aurora 3.18 sem aplicação
automática; a versão pública e as configurações privadas não foram alteradas.
