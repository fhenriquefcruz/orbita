# ORBITA — Handoff de continuidade

**Atualizado em:** 30/10/2026

**Branch de trabalho:** `feat/supabase-auth-protected-panel`

**Especificação principal:** [`PROMPT_MESTRE_ORBITA_3_0.md`](PROMPT_MESTRE_ORBITA_3_0.md)

> Este handoff foi reconstruído a partir do código, dos relatórios versionados em `quality/` e do trabalho desta conversa. O arquivo original mencionado pelo proprietário não estava no workspace nem no histórico Git consultado. Não tratar esta reconstrução como transcrição de um documento anterior.

## 1. Objetivo e estado real

ORBITA é uma assessoria pessoal inteligente com painel web, memória local do navegador, memória central Supabase e bot Telegram. A direção de produto, UX e qualidade está no Prompt Mestre 3.0. Evoluir a implementação existente; preservar dados e funcionalidades úteis. Não recomeçar o projeto.

O proprietário relatou ter executado o painel pelo VS Code, feito login real, acessado o dashboard e verificado que a sessão permaneceu após F5. Em 30/10, o agente observou a mesma aba autenticada no navegador integrado do VS Code, consultou a memória central e executou a prévia sem escrita; o painel permaneceu autenticado após recarga. A [evidência de interface](../quality/REAL_MEMORY_UI_20261030.md) registra os números e os limites. A homologação completa de dispositivos, recuperação de senha, publicação e sincronização permanece distinta dessa verificação.

O [`README.md`](../README.md), o [`ROADMAP.md`](../ROADMAP.md) e partes de [`quality/TRACEABILITY.md`](../quality/TRACEABILITY.md) contêm descrições anteriores à ativação do projeto Supabase e não devem substituir as evidências datadas mais recentes. Atualizá-los em incremento próprio, após conferir cada afirmação.

## 2. Arquitetura a preservar

| Área | Implementação atual | Limite importante |
| --- | --- | --- |
| Painel | `docs/index.html`, `docs/design-aurora.css`, `docs/theme.js` | HTML/CSS/JS existente; sem reconstrução de framework |
| Login | `docs/auth.js`, `docs/cloud-config.js` | Sessão Supabase validada; somente chave publicável no navegador |
| Dados locais | `orbita_v12_local` no `localStorage`, `docs/local-integrity.js` | Dados do navegador não criptografados; vínculo com a conta, guardas de abas e journal |
| Memória central | `docs/cloud-core.js`, `docs/cloud-sync.js` | Consultar/simular por GET; conciliação com escrita exige confirmação e backup |
| Telegram | `telegram/bot.py`, `telegram/cloud_memory.py`, `api/index.py` | Não alterar bot ativo, webhook ou flags sem autorização específica |
| Banco | `infra/supabase/` | RLS e grants existentes; `002_action_proposals.sql` e `003_telegram_delivery.sql` bloqueados |
| Qualidade | `quality/`, `telegram/tests/`, `.github/workflows/tests.yml` | Distinguir testes simulados, consultas reais e homologação em dispositivo |

O projeto Supabase dedicado é `orbita` (`tbqfymedgdsdrgkqmuni`, `sa-east-1`). [`quality/SUPABASE_ACTIVATION_20261024.md`](../quality/SUPABASE_ACTIVATION_20261024.md) registra a implantação do núcleo e os grants mínimos. [`quality/AUTH_RELEASE_GATE.md`](../quality/AUTH_RELEASE_GATE.md) registra, em 26/10, teste HTTP com **duas sessões Auth/JWT reais**, isolamento de registros e chat e limpeza das fixtures; o teste não libera por si só `main` ou produção. Em 29/10, uma consulta **somente leitura** pelo conector Supabase confirmou `ACTIVE_HEALTHY` e `count(*) = 1` em `public.orbita_records`. A consulta administrativa não comprova a jornada da interface sob RLS.

## 3. Entrega funcional desta conversa

Arquivos da entrega funcional, sujeitos ao estado Git indicado por `git status`:

- `docs/index.html`: conclusão contextual de tarefas abertas na lista e no dashboard; busca e filtros com limpeza em um clique, contagem de resultados e rótulos acessíveis; atualização coerente dos indicadores e resumos; conclusão da conversa com Vânia pelo mesmo caminho de gravação. O modal agora prende o foco durante Tab e devolve o foco ao fechar.
- `docs/design-aurora.css`: estados visuais da ação Concluir, botão Limpar filtros e alvos de toque em tela pequena.
- `quality/test_task_journey.cjs`: jornada isolada em Chrome com Auth e Data API simulados, sem conexão ao Supabase real.
- `quality/browser_smoke.py`: usa Chrome instalado quando disponível no Windows e seleciona a ação Editar/Excluir na lista, evitando ambiguidade após a inclusão das ações no dashboard. O Chromium do Playwright continua sendo usado na CI Linux.
- `docs/cloud-sync.js`: a prévia de conciliação é invalidada quando a memória local muda; uma edição durante a consulta impede a exibição de um plano calculado com dados antigos. O botão de conciliação continua refazendo a comparação antes de qualquer escrita.
- `docs/auth.js`: durante a restauração assíncrona, exibe verificação sem formulário de login. Uma falha temporária oferece **Tentar novamente** sem descartar a sessão; uma sessão recusada volta ao login. Falha temporária ao renovar o token em um painel aberto também não provoca logout.
- `.github/workflows/tests.yml`: nova jornada adicionada à CI de PR com Playwright Node 1.55.0, alinhado à versão Python já usada no workflow. A CI remota ainda não foi observada para estas alterações.
- `README.md`, `ROADMAP.md`, `quality/TRACEABILITY.md`: descrições antigas atualizadas; a linha de base histórica da rastreabilidade foi preservada em adendo. `.gitignore` passou a ignorar `node_modules/`.

**Verificação executada nesta conversa:**

1. `node --test quality/test_cloud_core.cjs quality/test_local_integrity.cjs quality/test_service_worker.cjs`: **51 passaram, 0 falharam**.
2. `node quality/test_task_journey.cjs` com Playwright disponível no ambiente local: **passou**. Cobriu criação, edição, busca sem acentos, filtros, limpeza, cancelamento de conclusão, falha de `localStorage` sem falso sucesso, conclusão, dashboard e resumo, F5, consulta/simulação por GET sem mutação local, invalidação da prévia após edição e durante GET, conclusão pela conversa e ausência de overflow em 320/390/1280 px. Cobriu ciclo de foco do modal e Auth simulado com resposta atrasada, falha 503 recuperável, sessão recusada 401 e falha temporária ao renovar token em painel aberto.
3. `git diff --check` e `node --check quality/test_task_journey.cjs`: **passaram**.
4. `python quality/browser_smoke.py`: **passou** no Chrome local com Auth simulado, isolamento, importação unidirecional e proteção contra PATCH concorrente.
5. Suíte Python do aplicativo, excluindo somente `test_private_database_backup.py` e `test_verify_backup_archive.py`: **167 testes executados, sem falhas**. A descoberta completa executou **192 testes**, com 18 ignorados, 1 falha e 5 erros concentrados nesses dois módulos de backup por exigirem permissões POSIX `0600/0700`, indisponíveis neste Windows. A CI Linux permanece como verificação desses módulos.
6. Em 30/10, na aba autenticada do VS Code, consulta UI real mostrou **1 remoto e 0 locais**; a simulação retornou **1 a receber, 0 a enviar/excluir e 0 conflitos**. Após recarga, a sessão permaneceu e os indicadores continuaram 1/0. A regressão com resposta Auth atrasada passou, sem exibir o formulário durante a verificação. Ver [`REAL_MEMORY_UI_20261030.md`](../quality/REAL_MEMORY_UI_20261030.md).

Para executar o teste de navegador em outra máquina, instalar `playwright` para Node e um Chromium compatível. A CI instala `playwright@1.55.0` antes da jornada. O teste usa o Chromium do Playwright quando disponível; neste Windows usou Chrome instalado. Nesta sessão, Playwright 1.55.0 foi instalado somente em `quality/node_modules/` (ignorado pelo Git) e a jornada passou novamente sem `NODE_PATH`. O smoke Python usou dependências temporárias fora do repositório; nenhuma dependência foi adicionada ao aplicativo.

## 4. Limites e riscos

- Os testes automatizados de navegador usam **Auth/Data API simulados**, inclusive falhas 503/401. A consulta e a prévia foram também observadas pela interface com **uma sessão real**, mas isso não homologa comportamento sob falha de rede real, isolamento RLS entre contas pela UI, escrita remota, recuperação de senha ou dispositivos diferentes.
- O painel mantém registros locais no navegador. Login não significa sincronização automática nem criptografia local. A consulta da memória central e a simulação não devem importar ou alterar dados.
- `docs/cloud-sync.js` permite conciliação explícita com POST/PATCH/DELETE após confirmação; não acionar esse fluxo sem autorização específica, backup conferido e entendimento do plano de conflitos.
- O bot, notificações externas e integração com calendário não devem ser descritos como ativos só porque o código existe.
- A recuperação de banco é uma trilha independente. [`quality/RECOVERY_SCOPE_DECISION_2026_10_29.md`](../quality/RECOVERY_SCOPE_DECISION_2026_10_29.md) demonstra dependências de `auth.users`/`auth.uid()` e **não autoriza** restaurar apenas tabelas `orbita_*` em PostgreSQL nativo. Não instalar Docker nem retomar essa trilha como pré-requisito para melhorar o painel.
- O arquivo de backup privado, senhas, JWTs, chaves secretas e dados pessoais não devem entrar no repositório nem na conversa.

## 5. Restrições de execução

Não alterar `main`, produção, bancos remotos, migrações bloqueadas, Telegram ativo, backups privados ou serviços PostgreSQL sem autorização específica. Trabalho local reversível na branch atual está autorizado. Preservar todas as alterações locais; conferir `git status --short --branch` antes de editar. Não usar `git reset`, `clean`, `pull` ou merge para descartar trabalho. Não fazer deploy nem publicar por inferência.

## 6. Próxima ordem de execução

1. Ler este handoff, o Prompt Mestre e `git status`; preservar todas as alterações locais da entrega acima, inclusive as alterações já adicionadas ao índice Git.
2. Preservar a evidência de consulta e prévia somente leitura de 30/10. Para aprofundar a homologação, verificar isolamento e falhas com sessões reais separadas sem expor senhas/JWTs; a conciliação com escrita continua fora do escopo autorizado.
3. Continuar o ciclo de tarefas e UX com teste em navegador real para teclado, foco, mobile e estados de erro; ampliar regressão apenas onde houver risco concreto.
4. Observar a execução da CI quando houver PR/commit autorizado; corrigir falhas concretas. Manter README, roadmap e rastreabilidade alinhados às evidências posteriores.
5. Manter `002_action_proposals.sql`, `003_telegram_delivery.sql`, restauração, deploy, flags Telegram e `main` fora do escopo até autorização específica.

**Princípio de prestação de contas:** registrar arquivos alterados, comandos e resultados realmente observados. Teste mockado não equivale a homologação remota. Nenhuma tarefa pendente deve ser marcada como concluída por ausência de erro visível.
