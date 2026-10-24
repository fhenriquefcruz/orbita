# ORBITA 3.3 — Visibilidade e segurança da memória central

## O que muda
- Na visão geral, após autenticação Supabase real, o painel mostra uma faixa enxuta de situação da memória, com leitura do total de registros da nuvem (via `Prefer: count=exact` e cabeçalho `Content-Range`) e contagem local. O usuário pode conferir novamente ou navegar até "Dados e histórico".
- Essa inspeção só faz requisição HTTP **GET** com JWT de usuário; não escreve nem faz conciliação por conta própria.
- O usuário continua decidindo quando conciliar. Antes de qualquer escrita é iniciado um download do backup e exigido um segundo aceite confirmando que o arquivo foi de fato salvo.
- Antes e depois de operações remotas, o painel verifica se os registros e tombstones locais mudaram desde o planejamento. Se mudaram, interrompe a atualização local e pede nova comparação.
- Paginação remota agora ordena por `updated_at.desc,id.asc`, evitando instabilidade em timestamps iguais.
- Cache estático PWA versionado para evitar cliente com JavaScript antigo.

## Homologação automatizada
- Smoke Playwright mantém gate de Auth simulado e rotas protegidas.
- Mock de PostgREST comprova chamada somente leitura com Bearer e `count=exact`.
- Valida aviso de 2 registros na nuvem e atualização explícita; teste de telas de 320 a 1920px já existe.
- Testes não comprovam contas reais nem isolamento RLS ponta a ponta.

## Limites operacionais
- Memória central ainda exige login Supabase real e conciliação **manual** com backup.
- Sem garantia transacional distribuída. Se a falha ocorrer após uma escrita remota, o servidor pode ficar parcialmente atualizado; a recuperação é reler e conciliar novamente.
- Um clique no download **não assegura** que o navegador salvou o arquivo; o usuário confirma manualmente.
- A inspeção retorna a contagem de registros do titular autenticado; não expõe segredo de servidor.
- O JavaScript do GitHub Pages e arquivos locais não são armazenamento criptografado. Evitar dados sensíveis até migração e homologação.
- Os endpoints Telegram continuam separados e sem webhook ativo. Não afirmar que Vânia responde online.
- O PR #7 do Supabase Auth permanece em rascunho até validação real de login e isolamento entre duas contas.

## Revisão necessária antes de release
1. Testar login real no ambiente de prévia e os redirecionamentos de recuperação para o domínio de prévia.
2. Conferir que o novo indicador mostra o total esperado e falha sem perder dados ao ficar offline.
3. Exportar backup, conciliar registro de teste, alterar em outra aba, verificar interrupção sem sobrescrita.
4. Confirmar que registros excluídos são respeitados e que não há dados do usuário A no usuário B.
5. Revisar iOS Safari/PWA, Android e teclados móveis em tema claro e noturno.

**Estado:** código implementado em prévia; dados reais e RLS E2E ainda não homologados.
