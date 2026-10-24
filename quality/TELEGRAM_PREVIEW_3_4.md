# ORBITA 3.4 — Prévia autenticada Telegram → Aurora

## Contexto validado em 24/10/2026

- Telegram `@orbita_assistente_bot`: webhook registrado e comandos `/ajuda`, `/tarefa` e `/tarefas` respondendo.
- Supabase exclusivo ORBITA: uma tarefa de teste `P1` efetivamente persistida, com usuário Auth existente; três updates de Telegram com estado `processed`.
- A consulta à memória no painel continua protegida por Supabase Auth e RLS; os testes automatizados com provedor simulado não equivalem à validação entre dois usuários reais.

## Entrega desta etapa

Em **Dados e histórico → Memória central**, o painel mostra **Recebidos do Telegram**, até cinco itens mais recentes da própria conta, seus títulos, tipos, prioridades e situação (em aberto/concluída). O botão **Atualizar** repete a consulta autenticada.

O filtro no PostgREST busca `payload->>source=eq.Telegram ORBITA` na tabela `orbita_records`. A requisição usa a chave pública do cliente, o token da sessão e as políticas RLS existentes. Nenhuma chave `sb_secret_` é enviada pelo navegador. Os títulos remotos usam `textContent` (não são interpretados como HTML).

**Importante:** o painel não altera dados locais nem envia alterações durante a prévia. A listagem principal, os indicadores e o dashboard local somente refletem dados remotos **depois de um backup confirmado e conciliação manual**. O botão da prévia não altera `localStorage` e a exclusão/conclusão de tarefas não é executada a partir dessa visualização.

## Gates de qualidade

1. Sem sessão Auth, a aplicação continua bloqueada.
2. Após login, a prévia faz GET autenticado e lista somente itens cuja origem é Telegram ORBITA.
3. Sem dados de Telegram na conta autenticada, informa ausência e convida a conferir o vínculo da conta.
4. Em erro de rede, não toca no estado local.
5. Strings maliciosas em títulos são exibidas como texto, sem executar HTML.
6. Layout responsivo nos 8 viewports e modo noturno preservados.
7. Cache PWA versionado `orbita-pages-v3.4.0-telegram-preview.1`.

## Homologação manual pendente

- Na prévia Vercel do ramo de Auth, entrar com a **mesma** conta que está configurada em `ORBITA_USER_UUID`; a tarefa criada no Telegram deve aparecer em **Recebidos do Telegram**.
- Enviar `/feito 1` no bot **apenas depois que o proprietário decidir concluir a tarefa de teste** e pressionar Atualizar para conferir o status.
- Exportar o backup do navegador e conciliar dados **somente após confirmar que o arquivo foi salvo**. Confirmar que o registro aparece também na visão geral de registros.
- Validar RLS com duas contas reais independentes; testar recuperação de senha e dispositivos móveis. Ainda não liberar a PR de Auth para a branch pública `main`.
- A conversa livre da Vânia requer configuração independente de `OPENAI_API_KEY` no backend. Esta etapa não habilita IA nem notificações automáticas.
