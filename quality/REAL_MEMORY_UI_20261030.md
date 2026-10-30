# Consulta da memória central pela interface — 30/10/2026

## Escopo observado

- Painel local `http://127.0.0.1:8080/` no navegador integrado do VS Code, com sessão Supabase já autenticada pelo proprietário. Nenhuma credencial, sessão ou token foi copiado.
- Na visão geral, a interface exibiu **1 registro na nuvem e 0 neste dispositivo**. Em **Dados e histórico**, a seção de atividades do Telegram exibiu **1 de 1 registro consultado**, com **1 tarefa em aberto**.
- O botão **Simular sem alterar** retornou: **1 a receber, 0 atualizações da nuvem, 0 criações/atualizações a enviar, 0 exclusões e 0 conflitos**; total projetado de **1**. A interface indicou que nada havia sido gravado.
- Após recarregar a aba integrada, o painel permaneceu autenticado. A visão geral continuou com **1 registro remoto e 0 locais**, e a trilha local permaneceu sem alterações.

## Limites da evidência

O código da simulação em `docs/cloud-sync.js` usa requisições GET para consultar os registros. Nesta verificação pela interface, somente os controles de navegação e **Simular sem alterar** foram acionados. **Trazer da nuvem** e **Conciliar registros agora** não foram acionados. A observação não é teste de isolamento RLS entre duas contas, nem comprova ausência de alterações remotas por outros clientes concorrentes.

O piscar do formulário de login relatado pelo proprietário foi reproduzido pela leitura do fluxo: `auth.js` mostrava o formulário antes de concluir a verificação assíncrona da sessão. A correção apresenta **Verificando sua sessão** sem o formulário enquanto a validação está pendente. A regressão com resposta Auth atrasada passou em `quality/test_task_journey.cjs`; o F5 na aba real confirmou a permanência do login.
