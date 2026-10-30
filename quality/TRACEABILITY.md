# ORBITA 3.0 — Linha de base e matriz de rastreabilidade

> **Registro histórico de 24/10/2026.** A matriz abaixo descreve a linha de base daquela data. O estado atualizado da branch está no [handoff](../product/ORBITA_CODEX_HANDOFF.md) e no adendo ao final deste arquivo; não interpretar pendências históricas como estado atual.

**Referência:** `product/PROMPT_MESTRE_ORBITA_3_0.md` | **Versão base:** 2.2 | **Incremento:** 3.0-alpha.1 | **Data:** 24/10/2026

## Linha de base técnica confirmada

- `docs/index.html`: HTML/CSS/JS monolítico, navegação local e `localStorage` `orbita_v12_local`.
- `telegram/bot.py`: polling Telegram, SQLite privado e uso opcional da OpenAI API.
- `docs/sw.js`: cache de recursos estáticos, sem API privada.
- `GitHub Pages`: workflow do repositório no `main`, sem backend embutido.
- Na linha de base 3.0-alpha.1 não havia memória compartilhada ativa nem proteção global do painel; a conexão à nuvem usava login isolado no módulo Dados.
- Não havia comprovação de notificações realmente programadas.

## Decisão de arquitetura

Preservar frontend existente e SQLite de desenvolvimento. Acrescentar projeto Supabase próprio com RLS, adaptador Telegram e conciliação **opt-in** autenticada. Não reescrever framework só por estética. Não alterar bancos de projetos existentes.

## Requisito → implementação → teste → resultado

| ID | Requisito | Implementação | Teste / evidência | Estado |
|---|---|---|---|---|
| ORB-SEC-001 | Sem segredos no repositório público | Config pública separada, chaves secret server-side | Inspeção e CI `tests.yml` | Em validação |
| ORB-DATA-001 | Preservação de registros existentes | `docs/cloud-core.js`, backups e tombstones | `quality/test_cloud_core.cjs` (7 cenários) | Em validação |
| ORB-DATA-002 | Memória PostgreSQL com RLS por usuário | `infra/supabase/001_core.sql` | Schema escrito; execução/RLS real pendentes | Bloqueado |
| ORB-DATA-003 | Login com projeto isolado | `docs/auth.js`, sessão validada e recuperável, `docs/cloud-sync.js` sem login paralelo | Sintaxe JS verificada; E2E real pendente | Implementado, não homologado |
| ORB-SEC-002 | Views protegidas `#/home`…`#/data` | UI bloqueada por padrão, guarda de sessão e logout | Smoke com Auth simulado no CI; Supabase real pendente | Implementado, não homologado |
| ORB-SEC-003 | Recuperação de senha | Auth REST com link de recuperação e troca de senha | Teste com SMTP/e-mail real pendente | Implementado, não homologado |
| ORB-DATA-004 | Conciliação explícita local↔nuvem | `cloud-core.js`, `cloud-sync.js` | 7 testes de regra aprovados; E2E pendente | Em validação |
| ORB-INT-001 | Telegram consultar a memória central | `telegram/cloud_memory.py`, seleção em `bot.py` | 6 testes do adaptador; integração real pendente | Em validação |
| ORB-INT-002 | Webhook HTTPS autenticado Telegram | `api/index.py` | 3 testes de bloqueio/autorização; deploy pendente | Em validação |
| ORB-INT-003 | Resposta generativa de Vânia | `telegram/bot.py` OpenAI já disponível e preservado | Mock/sem chave real nesta execução | Bloqueado |
| ORB-UX-001 | Identidade visual alinhada ao mestre | Tokens de cores no `docs/index.html` | Validação visual física pendente | Implementado, não testado |
| ORB-UX-002 | Interface de conexão honesta | Card no módulo Dados e histórico | Teste browser indisponível | Implementado, não testado |
| ORB-DATA-005 | Não confirmar gravação local falha | `saveLocal` passa a lançar erro | Inspeção de código; browser pendente | Em validação |
| ORB-FUN-001 | Contagem de concluídos no dia | `completed_at` e filtro por data local | Browser pendente | Implementado, não testado |
| ORB-UX-003 | Mobile 320 a 1920 px | CSS responsivo existente preservado | Browser bloqueado neste ambiente | Bloqueado |
| ORB-ACC-001 | WCAG 2.2 AA | A desenvolver e verificar | Axe/teclado não executados | Não iniciado |
| ORB-FUN-002 | Resumos agendados às 07:30 e 18:00 | Apenas configuração de referência, envio desativado | Sem agendador real | Não iniciado |
| ORB-PWA-001 | Cache versionado | `docs/sw.js` cache `3.0.0-alpha.1` | Sintaxe JS, browser pendente | Em validação |
| ORB-DEP-001 | GitHub Pages publicado | Workflow preexistente | Novo deploy necessário após merge | Em validação |
| ORB-INT-004 | Servidor Telegram em produção | Fonte webhook/polling, env privada pendente | Deploy e teste real pendentes | Bloqueado |
| ORB-FUN-003 | Busca, filtros, CRUD completos | Preservados da versão 2.2 | Regressão navegador pendente | Em validação |

## Testes executados neste incremento

- Python `unittest`: 17 testes aprovados (SQLite original + adaptador Supabase mockado + endpoint webhook).
- Node `node:test`: 7 testes aprovados (versões, exclusões, conflitos, mesclagem, entradas inválidas).
- `node --check`: sintaxe dos scripts JavaScript verificada.
- `compileall`: sintaxe Python verificada.
- **Bloqueio de teste visual:** o Chromium disponível retornou `ERR_BLOCKED_BY_ADMINISTRATOR` para abrir site local; isso não valida layout, Safari nem experiência em dispositivo real.
- **Integração de produção:** não executada por ausência de projeto Supabase do ORBITA, credenciais privadas e hospedeiro configurado.

## Riscos e contenções

| Risco | Impacto | Mitigação |
|---|---|---|
| Token Telegram antes divulgado | Controle indevido do bot | Revogar no BotFather antes de ativar |
| Conciliação interrompida | Estado parcialmente aplicado na nuvem | Backup automático antes de sincronizar; repetir com auditoria |
| Serviço offline | Ausência de respostas e nuvem | Modo local preservado; erros explícitos |
| Service worker antigo | Interface desatualizada | Versionar cache e excluir versões anteriores |
| Compartilhamento indevido entre contas | Vazamento de dados locais | Bloqueio de troca de conta vinculada e políticas RLS |
| Alteração estética com regressão | Perda de funções | Branch/PR e smoke pós-publicação obrigatório |

## Situação do incremento

**Em validação.** A autenticação e o guard das views foram adicionados na branch `feat/supabase-auth-protected-panel`. Ainda requerem confirmação do CI, testes com Supabase Auth/RLS real e conexão da organização exclusiva ORBITA. Não há liberação para dados sensíveis. O ORBITA 3.0 **não está integralmente concluído**.

## Adendo de 29/10/2026 — evidência posterior à linha de base

| ID | Situação atual | Evidência e limite |
| --- | --- | --- |
| ORB-DATA-002 / ORB-DATA-003 / ORB-SEC-002 | Núcleo Supabase implantado; login/RLS real parcialmente homologados | [`SUPABASE_ACTIVATION_20261024.md`](SUPABASE_ACTIVATION_20261024.md) e [`AUTH_RELEASE_GATE.md`](AUTH_RELEASE_GATE.md): duas sessões Auth/JWT reais, isolamento de registros/chat e limpeza de fixtures em 26/10. O proprietário relatou login e F5 no painel; recuperação e dispositivos ainda pendentes. |
| ORB-DATA-004 | Prévia de conciliação validada em navegador simulado | `quality/test_task_journey.cjs` verifica GET, ausência de alteração local e invalidação da prévia após edição ou edição durante o GET; leitura UI sob sessão real ainda pendente. A conciliação com escrita não foi acionada nesta entrega. |
| ORB-FUN-001 / ORB-FUN-003 | Jornada local aprovada no navegador simulado | Criar, editar, concluir, buscar, filtrar, limpar, atualizar indicadores/resumo, F5 e falha de armazenamento verificados em `quality/test_task_journey.cjs`. |
| ORB-UX-003 / ORB-ACC-001 | Verificação parcial | Sem overflow em 320/390/1280 px, rótulos de busca/filtros e ciclo de foco do modal testados. Isso não equivale a auditoria WCAG 2.2 AA ou teste Safari/Android reais. |
| ORB-PWA-001 | Regressão local aprovada | `quality/test_service_worker.cjs` passou nesta sessão; atualização real em dispositivo ainda pendente. |

Nesta sessão, `node --test quality/test_cloud_core.cjs quality/test_local_integrity.cjs quality/test_service_worker.cjs` passou com **51/51**. A jornada `node quality/test_task_journey.cjs` e o smoke `python quality/browser_smoke.py` também passaram com Playwright e Chrome locais. A suíte Python do aplicativo, excluindo dois módulos de backup que exigem permissões POSIX, executou **167 testes sem falhas**; a descoberta completa no Windows executou 192 testes, com 18 ignorados, 1 falha e 5 erros nesses módulos. O [workflow Linux/Windows do PR #7](https://github.com/fhenriquefcruz/orbita/actions/runs/41055169169) terminou com sucesso em 30/10/2026, incluindo a descoberta Python completa, o smoke e a nova jornada. Em consulta administrativa somente leitura em 29/10, o projeto Supabase estava `ACTIVE_HEALTHY` e `public.orbita_records` tinha uma linha; essa consulta não prova RLS pela interface.

## Adendo de 30/10/2026 — interface com sessão real

| ID | Resultado observado | Limite |
| --- | --- | --- |
| ORB-SEC-002 | A aba integrada do VS Code estava autenticada e continuou autenticada após recarga. `docs/auth.js` apresenta “Verificando sua sessão” enquanto valida o token. Em navegador simulado, atraso Auth, falha 503 com nova tentativa, resposta 401 e falha temporária na renovação passaram. | As falhas foram simuladas; não testa sessão expirada nem recuperação de senha com conta real. |
| ORB-DATA-004 | Em **Dados e histórico**, consulta real exibiu 1 registro remoto e 0 locais; a prévia exibiu 1 a receber, 0 a enviar/excluir, 0 conflitos. Após recarga, o dashboard ainda mostrou 1/0. Ver [`REAL_MEMORY_UI_20261030.md`](REAL_MEMORY_UI_20261030.md). | Uma sessão real; não testa isolamento entre contas pela UI nem conciliação com escrita. |
