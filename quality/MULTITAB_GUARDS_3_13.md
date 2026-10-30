# ORBITA Aurora 3.13 — Proteção contra abas desatualizadas

## Problema
Duas abas do mesmo navegador compartilhavam `localStorage`, mas cada uma mantinha uma cópia própria de `records` e `audits` em memória. Depois de uma tarefa ser alterada na aba A, a aba B poderia usar a versão anterior para sobrescrever ou excluir o registro recém-editado. A 3.12 protegeu exclusões interrompidas, mas não essa concorrência entre abas.

## Mudanças
- `docs/local-integrity.js` oferece `createTabGuard(storage)`, que captura os valores das chaves locais de registros, exclusões e titular após a inicialização.
- Antes de criar, editar, concluir uma tarefa na conversa ou excluir, a aba compara o estado atual com o último snapshot confirmado, além de recusar operações enquanto existir um journal de exclusão.
- O evento `storage` sinaliza alterações em registros, exclusões, titular e journal originadas em outras abas. A aba avisa e exige recarregamento para gravar novamente.
- Ao concluir uma gravação válida da própria aba, o snapshot é atualizado.
- A conclusão de tarefas confirmada na conversa passou a preparar cópia de registros e trilha de auditoria e a atualizar a memória em execução somente após o salvamento local.
- O cache PWA muda para `orbita-pages-v3.13.0-multitab-guard.1`.

## Regressão
- Testes Node: abas com snapshots independentes, alteração externa mesmo após retorno ao valor antigo, mudança de titular, journal pendente e continuidade após escrita própria.
- Playwright: duas abas sob a mesma identidade mockada; a primeira altera uma tarefa e a segunda tenta editar/excluir com conteúdo antigo. O armazenamento deve manter a edição correta; após recarga, a segunda aba consulta o estado atual.
- Testes anteriores de RLS simulado, backups, recuperação, leitura do Telegram, responsividade, segurança HTML e concorrência com Supabase continuam ativos.

## Limites de segurança
O `storage` event e a comparação de snapshots reduzem perdas acidentais, mas não implementam bloqueio atômico entre abas ou dispositivos; gravações realmente simultâneas ainda exigem controle transacional. Futuramente migrar para IndexedDB com transação e/ou Web Locks com fallback testado para Safari, sem substituir backups existentes sem uma migração auditada.

Os testes de duas contas usam identidade **simulada**. Ainda faltam duas contas Auth reais, teste no iPhone Safari e recuperação de senha antes de tirar o PR #7 do modo rascunho. A produção do Telegram, os dados reais e a branch pública `main` não fazem parte desta entrega.
