# Robustez no envio de mensagens — Vânia / Telegram

## Defeito corrigido
Anteriormente, o webhook marcava `processed` antes de `sendMessage`. Falha de envio resultava em perda definitiva da resposta.

## Protocolo
- `received`: atualização recebida, processamento em andamento; não reexecutar comando em duplicatas.
- `replied`: resposta persistida em `response`, pronta para envio ou reenvio. Nenhuma ação de memória precisa ser repetida.
- `processed`: `sendMessage` retornou sucesso e o banco registrou a confirmação.

No novo fluxo: claim → processar uma única vez → **persistir resposta** → enviar Telegram → marcar `processed`. Se a transmissão falhar, retorno HTTP 503 permite ao Telegram tentar novamente, recuperando a resposta persistida.

## Limites honestos
- Telegram não oferece chave de idempotência para `sendMessage`. Se o envio tiver sucesso mas a gravação final falhar, um retry pode **duplicar a mensagem de resposta**. A criação da tarefa/ideia não deve repetir nesse caminho.
- Queda durante `received` sem resposta exige inspeção e recuperação manual, para evitar duplicação de ações.
- Não é uma fila durável com reprocessador, supervisão ou garantias de entrega exatamente uma vez.
- Só ativar webhook com token revogado/substituído, segredo privado, proprietário autorizado e banco Auth validado.

## Homologação
- Testar envio normal, falha de envio seguida de retry, duplicata depois de `processed` e credencial inválida.
- Em produção, medir updates presos em `received`/`replied` e implantar rotina segura de recuperação antes de prometer confiabilidade operacional.
