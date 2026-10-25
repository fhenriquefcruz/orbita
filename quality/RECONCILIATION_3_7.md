# ORBITA 3.7 — Conciliação segura: prévia e revisões condicionais

## Objetivo
Conciliação manual, verificável e conservadora entre navegador, Supabase e Telegram. Sem automação de escrita, alteração em bot, migração SQL ou chave nova.

## Funcionalidades
- Em Dados → Memória central, Simular sem alterar consulta registros (GET com sessão Auth e RLS), exibe totais a receber, substituir, criar, atualizar, excluir e conflitos. Simular não importa nem modifica.
- Comparação JSON canônica, para evitar falsos conflitos decorrentes da ordem das chaves JSONB.
- Horários de revisão ausentes, iguais ou inválidos com conteúdos distintos geram conflito e bloqueiam a gravação.
- Exclusões com tombstones inválidos ou datas não comparáveis são bloqueadas.
- Atualizações são PATCH condicionado a ID e updated_at vistos na leitura; revisão remota diferente causa resposta vazia e aborta a sequência.
- Exclusões são DELETE condicionado à mesma revisão e abortam se mudou.
- Criações são INSERT simples (sem merge-duplicates): colisão de ID falha sem sobrescrever.
- Validação da identidade atual, backup obrigatório, consentimento duplo e preservação local se houver erro continuam.

## Limitações relevantes
- A simulação é um retrato pontual; o plano é recalculado ao conciliar.
- Múltiplas requisições não formam uma transação. Após falha, operações remotas anteriores podem ter sido aplicadas e devem ser auditadas antes de repetir.
- Controle otimista atual usa timestamp updated_at, não contador monotônico transacional. Duas gravações que reutilizem a mesma revisão não são integralmente detectáveis. Futuramente planejar RPC transacional, versão monotônica e soft-delete.
- A tarefa P1 do Telegram não foi alterada por esta implementação.

## Testes previstos
- Node: empate de revisão com payload divergente, JSON com ordem de chave distinta, tombstones inválidos e totais do plano.
- Navegador: prévia somente GET; alteração remota simulada entre leitura e PATCH interrompe a conciliação e conserva o registro local; Auth com duas identidades simuladas, segurança HTML e responsividade.
- Branch Auth permanece em PR draft; falta homologação real de duas contas, recuperação de senha e Safari antes de lançar em main.