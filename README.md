# ORBITA 🪐 — Assistente pessoal inteligente

Projeto independente de assessoria pessoal com **sete personagens**: **Vânia** (coordenação), **Zezé** (agenda e tarefas), **Gusttavo Lima** (ideias), **Bastião** (memória profissional), **Obina** (alertas), **Chicão** (execução) e **Fátima** (pesquisa).

> **Estado em 30/10/2026: versão 3.0-alpha em homologação na branch `feat/supabase-auth-protected-panel`.** O projeto Supabase exclusivo ORBITA está ativo, e a autenticação/RLS teve teste HTTP com duas contas reais em 26/10. A interface autenticada foi consultada em 30/10: a prévia somente leitura mostrou 1 registro remoto e 0 locais, com sessão preservada após recarga. Os registros do painel continuam locais até uma conciliação manual confirmada; a branch `main` não recebeu esta entrega. Não há notificações agendadas ativas.

## Estrutura

| Pasta | Conteúdo | Estado |
| --- | --- | --- |
| `docs/` | Painel web responsivo PWA para GitHub Pages | Auth real; registros locais e consulta à memória central |
| `telegram/` | Bot Telegram com comandos, SQLite, OpenAI opcional e memória Supabase | Código existente; estado operacional externo exige verificação separada |
| `infra/supabase/` | Núcleo SQL, RLS e grants; migrações opcionais | Núcleo implantado; propostas/entrega V2 bloqueadas |
| `api/index.py` | Webhook FastAPI para hospedagem HTTPS | Código existente; não presumir deploy operacional |
| `quality/` | Testes, evidências e matriz de requisitos | 51 testes JS locais e jornada de navegador simulada aprovados nesta entrega |
| `.github/workflows/pages.yml` | Publicação estática do painel | Publica a versão de `main`; esta branch ainda não foi integrada |
| `.github/workflows/tests.yml` | Testes e verificação preventiva de token | Automatizado |

## Repositório e publicação

O repositório local acompanha [fhenriquefcruz/orbita](https://github.com/fhenriquefcruz/orbita), na branch `feat/supabase-auth-protected-panel`. A publicação de `main` em [GitHub Pages](https://fhenriquefcruz.github.io/orbita/) é independente do código ainda não integrado nesta branch. Não usar a URL publicada como prova de que estas alterações já foram liberadas.

A pasta `docs/` é a **única publicada** pelo Pages. O código do bot fica no GitHub como fonte; GitHub Pages **não executa Python nem mantém um bot online**.

## Uso do painel

- Cadastre compromissos, tarefas, ideias e pendências.
- Consulte a central da Vânia (interpretação **local baseada em regras**, não IA generativa).
- Veja prévias de resumos e avaliação de prioridades.
- Exporte backups periódicos do painel.

**Privacidade:** os registros do painel continuam em `localStorage`, não no GitHub. O login Supabase protege a abertura da interface, mas o armazenamento local **não é criptografado**. Abrir outro dispositivo **não sincroniza** registros automaticamente; apagar dados do navegador pode apagá-los. Use exportação de backup e evite dados altamente sensíveis até concluir a homologação.

## Como testar o Telegram localmente

Consulte [telegram/README.md](telegram/README.md). Nunca envie token de bot ou chave de API pelo chat nem os publique no GitHub. Se um token tiver sido divulgado, **revogue-o em @BotFather antes de usar**.

## Horários e política já definidos, mas ainda desativados

- Resumos da Vânia: **07h30** e **18h00**.
- Silêncio das **20h00 às 07h30** (fuso `America/Campo_Grande`), com exceções críticas justificadas.
- Prioridades P0 crítica, P1 alta, P2 normal e P3 baixa.
- **Nenhuma notificação automática está ativada.**

## Evolução ORBITA 3.0

Consulte [Prompt Mestre](product/PROMPT_MESTRE_ORBITA_3_0.md), [Rastreabilidade](quality/TRACEABILITY.md) e [Configuração da memória central](infra/SETUP.md).

Para repetir a regressão local da memória e cache:

```bash
node --test quality/test_cloud_core.cjs quality/test_local_integrity.cjs quality/test_service_worker.cjs
```

A jornada de tarefas está em `quality/test_task_journey.cjs`. Ela exige Playwright Node 1.55.0 e Chromium (ou Chrome no Windows). Para executá-la localmente, instale a dependência de teste com `npm install --prefix quality --no-save --no-package-lock --ignore-scripts playwright@1.55.0` (no PowerShell, use `npm.cmd`) e rode `node quality/test_task_journey.cjs`. A [CI](.github/workflows/tests.yml) executa os mesmos passos. Auth e Data API são simulados nessa jornada; ela não modifica o Supabase real.

O smoke existente `python quality/browser_smoke.py` requer Playwright Python e usa Chrome instalado no Windows ou o Chromium do Playwright na CI Linux. Para indicar outro executável, defina `ORBITA_TEST_CHROME`. Esse smoke também simula Auth e a API; não altera o Supabase real. Os testes de permissões dos backups privados requerem POSIX; a [CI Linux do PR #7](https://github.com/fhenriquefcruz/orbita/actions/runs/41055169169) passou com eles em 30/10/2026.

O login protege o acesso à interface. `docs/cloud-config.js` contém apenas a URL e a chave **publicável** do projeto exclusivo. A sessão fica em `sessionStorage`: permanece após F5 na mesma aba, mas outra aba ou o navegador integrado do VS Code pode exigir login próprio. Durante a verificação da sessão, a tela mostra “Verificando sua sessão”, sem exibir o formulário de login. Se a verificação falhar por indisponibilidade, **Tentar novamente** mantém a sessão salva; uma sessão recusada exige novo login. A seção **Dados e histórico → Memória central** utiliza a sessão já validada; não existe segundo login. A simulação consulta a nuvem sem gravar e informa quando uma edição local torna a prévia desatualizada. Não envie chaves privadas para o GitHub.

O bot e a aplicação web **não compartilham dados automaticamente neste instante**. Depois da configuração privada, o Telegram pode salvar no Supabase e o painel pode conciliar registros por ação explícita. **Não há atualização em tempo real** nesta versão.

## Homologação real do Auth

Consulte o [relatório Auth/RLS de 26/10](quality/AUTH_RELEASE_GATE.md), o [handoff atual](product/ORBITA_CODEX_HANDOFF.md) e o [roteiro operacional](quality/HOMOLOGACAO_REAL_PASSO_A_PASSO.md). O isolamento HTTP com duas contas reais foi aprovado e as fixtures foram removidas; isso não substitui recuperação de senha, backup restaurável, testes em dispositivos e revisão de publicação.

## Próximas etapas

1. Ampliar a homologação da memória central para falhas de rede e duas contas pela interface; a [consulta e prévia com uma sessão real](quality/REAL_MEMORY_UI_20261030.md) já foram verificadas sem escrita.
2. Validar teclado, responsividade, recuperação de senha e backup em dispositivos reais.
3. Revisar a integração Telegram e as migrações opcionais somente após autorização específica e gates de segurança.
4. Evoluir conversa, calendário e notificações com permissões, observabilidade e testes verificáveis.

## Decisões de segurança

- **Nenhuma chave privilegiada** na aplicação web, GitHub Pages ou repositório. Somente URL e chave publicável são permitidas no cliente.
- Chaves ficam em variáveis de ambiente privadas no servidor local/hospedagem futura.
- A assinatura ChatGPT não cobre chamadas à API OpenAI utilizadas pelo bot.
- Não inserir memória pessoal ou profissional no repositório público.
- Auth/RLS já têm evidência HTTP com duas contas reais; a jornada de tarefas foi testada com Auth/Data API simulados. A consulta e a simulação da memória central foram observadas na interface com uma sessão real, sem testar escrita ou isolamento de duas contas pela UI.
