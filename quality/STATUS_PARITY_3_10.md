# ORBITA Aurora 3.10 — Coerência de situações Telegram e painel

## Defeito reproduzido

O bot compartilha com o Supabase tarefas em estados como `a_fazer`, `em_andamento` e `concluida`. O Aurora 3.9 aceitava `em_andamento` na recuperação de backups e na visualização remota, mas não o incluía no conjunto de situações ativas, no seletor de edição ou no filtro da lista local. Após `Trazer da nuvem`, uma tarefa nesse estado podia ficar ausente dos indicadores de pendências e prioridades.

## Correção

- Adicionada `em_andamento` à lista de estados aceitos no painel, com rótulo **Em andamento**.
- Adicionada às atividades ativas usadas pelo dashboard, cartões de prioridade, resumos e mecanismos consultivos.
- O filtro **Situação** e o modal de edição passam a preservar o estado original, sem traduzir silenciosamente o JSON para `em_execucao`.
- Compatibilidade com o estado local anterior `em_execucao` é mantida.
- Atualizado o cache PWA para `orbita-pages-v3.10.0-telegram-status.1`.

## Regressão automatizada

O teste Playwright simula uma tarefa originada no Telegram com `em_andamento` e prioridade P1. Em seguida valida a importação **somente leitura** no Supabase, um registro ativo e prioritário no dashboard, rótulo correto na lista, filtro e valor preservado no modal de edição.

## Segurança e limites

A alteração não toca no Telegram de produção, na conta Auth, em segredos, nas políticas RLS nem em registros reais. A importação continua manual e condicionada a backup. A PR de autenticação deve continuar em rascunho até verificação real com duas contas e Safari/recuperação de senha.