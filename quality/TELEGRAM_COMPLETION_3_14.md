# ORBITA Aurora 3.14 — Conclusão segura de tarefas entre Telegram e painel

## Problema reproduzido na revisão de código

O adaptador `telegram/cloud_memory.py` executava `GET` seguido de `PATCH`
incondicional para o comando `/feito N`. Entre as duas operações, o painel ou
outro dispositivo podia editar ou concluir a tarefa. Mesmo que o `PATCH`
atingisse zero linhas, `complete()` retornava `True` sem verificar a resposta.

## Comportamento implementado

1. Ler `id,payload,updated_at` da tarefa, filtrando `telegram_seq` e
   `user_id` do titular autenticado no backend.
2. Validar que há exatamente uma tarefa elegível e que `updated_at`
   está presente e inclui fuso horário. Registros ambíguos não são atualizados.
3. Gerar cópia do payload e carimbo de conclusão com microssegundos,
   obrigatoriamente posterior à revisão observada.
4. Executar `PATCH` com predicados `id`, `user_id` e
   `updated_at = revisão lida`; exigir `Prefer: return=representation`.
5. Retornar sucesso **somente** se exatamente uma linha com o ID esperado
   for devolvida. `[]` significa conflito ou ausência de alteração e retorna
   `False`, mantendo a mensagem do bot transparente.
6. Informar ao usuário que a tarefa pode ter mudado e orientar consulta
   por `/tarefas` em vez de anunciar uma conclusão não confirmada.

Não altera RLS, esquema Supabase, autenticação, banco local, notificações nem
a estrutura dos registros existentes.

## Matriz de qualidade

- Tarefa em andamento concluída com revisão remota ainda válida.
- Cópia do payload original preservada (sem mutação indireta).
- `PATCH` que retorna lista vazia após edição concorrente: sem sucesso falso.
- Resposta com ID errado: não confirmar conclusão.
- Revisão ausente, inválida ou sem fuso: nenhuma escrita.
- Ideias e estados terminais: nenhuma escrita.
- Carimbo de atualização posterior à revisão, inclusive revisão futura.
- Codificação correta de timestamp com offset na URL PostgREST.
- Mensagem `/feito` exibe sucesso apenas com confirmação.

Os testes automáticos estão em
`telegram/tests/test_cloud_memory.py` e `telegram/tests/test_bot.py`,
incorporados ao workflow Python preexistente.

## Limites e próximos gates

Esta melhoria usa `updated_at` como revisão de concorrência. Ela depende de
todos os escritores atualizarem esse campo ao modificar um registro; timestamp
com resolução insuficiente em um cliente legado pode permitir colisões. A
evolução futura recomendada é um campo `revision` inteiro com incremento
atômico no servidor e migração verificada entre clientes, antes da escrita
conversacional por múltiplos canais.

Validar com dois clientes reais no projeto Supabase exclusivo do ORBITA:
alterar a mesma tarefa entre o `GET` e `PATCH`, verificar zero linhas na
resposta, confirmar a ausência de conclusão falsa e repetir a operação após
recarregar. Manter a PR #7 em draft até a homologação de Auth, RLS real, Safari
e políticas de segurança já pendentes.

**Segurança:** sem credenciais ou alteração em `main` ou bot hospedado.
