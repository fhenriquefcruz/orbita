# ORBITA 🪐 — Assistente pessoal inteligente

Projeto independente de assessoria pessoal com **sete personagens**: **Vânia** (coordenação), **Zezé** (agenda e tarefas), **Gusttavo Lima** (ideias), **Bastião** (memória profissional), **Obina** (alertas), **Chicão** (execução) e **Fátima** (pesquisa).

> **Estado: 3.0-alpha.1 em validação.** A camada de login, recuperação de senha, restauração de sessão e navegação protegida foi preparada em branch de desenvolvimento; **a ativação real exige o projeto Supabase exclusivo ORBITA**. O painel ainda usa armazenamento local; a conciliação com a nuvem continua exigindo confirmação manual. O bot só responde quando executado ou com webhook hospedado e configurado. Não há notificações agendadas ativas.

## Estrutura

| Pasta | Conteúdo | Estado |
| --- | --- | --- |
| `docs/` | Painel web responsivo PWA para GitHub Pages | Funcional **localmente no navegador** |
| `telegram/` | Bot Telegram com comandos, SQLite, OpenAI opcional e memória Supabase | Executável após configuração privada |
| `infra/supabase/` | DDL com RLS para memória compartilhada | Implementado, implantação pendente |
| `api/index.py` | Webhook FastAPI para hospedagem HTTPS | Implementado, deploy pendente |
| `quality/` | Testes e matriz de requisitos do prompt mestre | 24 testes locais aprovados, E2E pendente |
| `.github/workflows/pages.yml` | Publicação estática do painel | Executa após habilitar Pages no GitHub |
| `.github/workflows/tests.yml` | Testes e verificação preventiva de token | Automatizado |

## Como publicar no GitHub Pages

1. Crie um repositório público `orbita` no GitHub, sem adicioná-lo a repositórios privados de trabalho.
2. Faça upload destes arquivos preservando as pastas, no branch `main`.
3. Em **Settings → Pages → Build and deployment → Source**, selecione **GitHub Actions**.
4. Acompanhe a execução do workflow `Publicar painel ORBITA no GitHub Pages` em **Actions**.
5. Site esperado: `https://SEU_USUARIO.github.io/orbita/` (depois que o GitHub confirmar a publicação).

A pasta `docs/` é a **única publicada** pelo Pages. O código do bot fica no GitHub como fonte; GitHub Pages **não executa Python nem mantém um bot online**.

## Uso do painel

- Cadastre compromissos, tarefas, ideias e pendências.
- Consulte a central da Vânia (interpretação **local baseada em regras**, não IA generativa).
- Veja prévias de resumos e avaliação de prioridades.
- Exporte backups periódicos do painel.

**Privacidade:** os registros continuam em `localStorage` do navegador, não no GitHub. Há controle de entrada por Supabase Auth na nova versão, porém o armazenamento local **não é criptografado**; evite informações sigilosas até a homologação. Abrir o site em outro dispositivo **não sincroniza** registros. Apagar dados do navegador pode apagar registros.

## Como testar o Telegram localmente

Consulte [telegram/README.md](telegram/README.md). Nunca envie token de bot ou chave de API pelo chat nem os publique no GitHub. Se um token tiver sido divulgado, **revogue-o em @BotFather antes de usar**.

## Horários e política já definidos, mas ainda desativados

- Resumos da Vânia: **07h30** e **18h00**.
- Silêncio das **20h00 às 07h30** (fuso `America/Campo_Grande`), com exceções críticas justificadas.
- Prioridades P0 crítica, P1 alta, P2 normal e P3 baixa.
- **Nenhuma notificação automática está ativada.**

## Evolução ORBITA 3.0

Consulte [Prompt Mestre](product/PROMPT_MESTRE_ORBITA_3_0.md), [Rastreabilidade](quality/TRACEABILITY.md) e [Configuração da memória central](infra/SETUP.md).

O login passa a proteger o acesso a toda interface. Sem projeto Supabase exclusivo e chave publicável configurada em `docs/cloud-config.js`, o painel **permanece bloqueado por segurança**. A seção **Dados e histórico → Memória central** utiliza a sessão já validada; não existe um segundo formulário de login. Não envie chaves privadas para o GitHub.

O bot e a aplicação web **não compartilham dados automaticamente neste instante**. Depois da configuração privada, o Telegram pode salvar no Supabase e o painel pode conciliar registros por ação explícita. **Não há atualização em tempo real** nesta versão.

## Homologação real do Auth

Consulte o [roteiro operacional](quality/HOMOLOGACAO_REAL_PASSO_A_PASSO.md).
O script `python3 quality/run_auth_homologation.py` solicita duas contas distintas
em um Terminal privado e valida o isolamento RLS pela API HTTP do Supabase,
sem copiar tokens manualmente nem modificar dados do negócio. Há seis testes
unitários em `telegram/tests/test_run_auth_homologation.py`.
**Não representa liberação de produção**: exige duas contas reais, backup,
validação de senha/recuperação e testes em dispositivos.

## Próximas etapas

1. Ativar e testar bot no Telegram com token rotacionado e `ORBITA_OWNER_ID` restrito.
2. Backend autenticado e memória em banco central com controles de acesso.
3. Conversa por IA com permissões e observabilidade; conexão segura Telegram ⇄ painel.
4. Google Calendar, confirmação de ações, fila de notificações e teste dos horários/silêncio.
5. Testes de ponta a ponta, limites de custo, backup/restauração e deploy do backend.

## Decisões de segurança

- **Nenhuma chave privilegiada** na aplicação web, GitHub Pages ou repositório. Somente URL e chave publicável são permitidas no cliente.
- Chaves ficam em variáveis de ambiente privadas no servidor local/hospedagem futura.
- A assinatura ChatGPT não cobre chamadas à API OpenAI utilizadas pelo bot.
- Não inserir memória pessoal ou profissional no repositório público.
- O login web está preparado, mas **não foi homologado com Supabase real**; o backend compartilhado ainda não foi implantado e os dados não estão sincronizados.
