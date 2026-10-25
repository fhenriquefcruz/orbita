# ORBITA 3.11 — Exclusões locais resilientes e vínculo de titular

## Defeito anterior

A exclusão de registros locais dependia de duas gravações separadas no navegador: um registro de exclusão em `orbita_cloud_tombstones_v1` e a lista local em `orbita_v12_local`. Se uma gravação falhasse (por exemplo, armazenamento indisponível), o painel podia apresentar a tarefa removida da memória em execução, mas ainda mantida no disco — ou manter o marcador de exclusão sem a mudança correspondente.

Outro ponto: a autenticação consultava a presença de registros/chat legados para pedir autorização de vínculo a uma conta, mas desconsiderava um navegador contendo apenas tombstones.

## Correções implementadas

- A exclusão calcula o novo estado antes de tocar no armazenamento.
- Primeiro persiste a nova lista de registros e auditoria. Depois persiste o marcador de exclusão.
- Se o segundo passo falhar, tenta reverter a lista local ao valor anterior. A memória e a tela só são atualizadas quando ambos os passos terminam.
- Se até a reversão falhar, mostra aviso de risco, instruindo o usuário a não sincronizar e revisar o backup. **Não há garantia de transação atômica entre duas chaves de localStorage.**
- Em exclusão bem-sucedida, continua emitindo o aviso `orbita:local-change` para o painel mostrar alterações locais pendentes.
- Ao vincular um navegador ainda sem titular, presença de exclusões antigas passa a exigir confirmação explícita; a recusa mantém a interface bloqueada.
- Nenhuma operação de escrita no Supabase/Telegram é adicionada.

## Testes automatizados

1. Em navegador autenticado com tarefa existente, provocar `QuotaExceededError` somente ao gravar o tombstone e confirmar que a tarefa, a lista persistida e a marcação antiga permanecem intactas.
2. Retirar a falha simulada, concluir a exclusão e verificar que a tarefa sai da lista e seu tombstone é gerado.
3. Em segundo contexto, inserir apenas tombstones sem `account binding`, negar vínculo no login e verificar painel bloqueado. Depois aceitar e verificar o vínculo e a preservação dos tombstones.
4. Preservar os demais testes de autenticação, duas identidades simuladas, importação unidirecional, recuperação completa, responsividade, tratamento de XSS e revisão concorrente.

## Homologação

A versão principal permanece em PR de autenticação, com publicação bloqueada até testes reais em dois usuários, recuperação de senha e testes com Safari/iPhone. Esta alteração não modificou registros reais nem o backend Telegram.

**Limitação residual:** localStorage não fornece transações entre chaves. O rollback é de melhor esforço; para alta confiabilidade entre dispositivos, priorizar futuramente uma persistência transacional ou protocolo robusto em IndexedDB.