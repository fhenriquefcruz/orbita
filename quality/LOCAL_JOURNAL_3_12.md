# ORBITA Aurora 3.12 — Journal de recuperação e gravações locais consistentes

## Diagnóstico
O painel Aurora usa `localStorage` com duas chaves separadas: registros e tombstones. O rollback adicionado na 3.11 protege exceções durante a execução, mas **não consegue executar caso a aba ou dispositivo feche entre as duas gravações**. Além disso, edições/criações alteravam a coleção em memória antes de confirmar a escrita, permitindo uma divergência temporária entre UI e disco após `QuotaExceededError`.

## Entrega
- Novo módulo `docs/local-integrity.js`, carregado **antes** de `auth.js`, com journal write-ahead em `orbita_local_txn_v1`.
- Antes de exclusões, grava snapshot anterior e posterior das duas chaves, vinculado à conta Auth do navegador; em seguida aplica as duas alterações e limpa o journal.
- Se houver falha de armazenamento, tenta reverter as duas chaves. Se a aba encerrar durante a operação, a próxima abertura **detecta e reverte a exclusão incompleta** antes de liberar o painel autenticado.
- A recuperação valida titular, limites de tamanho e se as chaves ainda correspondem ao estado esperado. Em divergência, **bloqueia a abertura** em vez de sobrescrever uma alteração de outra aba.
- Criações e edições preparam cópias imutáveis de registros/auditoria, gravam o `localStorage` e **somente depois** alteram os dados da UI.
- O service worker inclui o novo módulo no cache 3.12; sintaxe e testes de unidade entram no GitHub Actions.

## Cenários cobertos
- Exclusão normal sem journal residual.
- Falha no segundo `setItem` com rollback e recuperação se até o rollback falhar.
- Queda simulada após gravar a lista e antes de atualizar tombstones, validada em navegador com recarga completa.
- Journal associado a outra conta é recusado.
- Journal inválido/alteração não prevista por outra aba não provoca sobrescrita silenciosa.
- Permanecem os testes anteriores de backup, RLS simulado, segurança HTML, responsividade e integração Telegram read-only.

## Limitações e próximos gates
O journal é uma **estratégia de recuperação**, não uma transação atômica multi-chave. Ele exige espaço adicional no `localStorage`, e outras abas ainda podem modificar dados fora do journal. Uma migração para IndexedDB com transação multi-store exige versão de esquema, migração idempotente, rollback e testes Safari/iOS; não foi improvisada aqui.

A versão pública `main` e o backend Telegram não mudam. O PR #7 permanece rascunho até teste com duas contas Supabase reais, validação em iPhone Safari, recuperação de senha e política de senhas comprometidas.
