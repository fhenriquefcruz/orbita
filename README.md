# ORBITA 🪐 — Assistente pessoal inteligente

Projeto independente de assessoria pessoal com **sete personagens**: **Vânia** (coordenação), **Zezé** (agenda e tarefas), **Gusttavo Lima** (ideias), **Bastião** (memória profissional), **Obina** (alertas), **Chicão** (execução) e **Fátima** (pesquisa).

> **Estado: protótipo técnico.** O painel e o bot são módulos **independentes**; não compartilham automaticamente memória, credenciais ou agenda. O bot só responde enquanto executado no computador ou servidor. Não há notificações agendadas ativas.

## Estrutura

| Pasta | Conteúdo | Estado |
| --- | --- | --- |
| `docs/` | Painel web responsivo PWA para GitHub Pages | Funcional **localmente no navegador** |
| `telegram/` | Bot Telegram com comandos, SQLite e OpenAI opcional | Executável após configuração privada |
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

**Privacidade:** os dados são gravados no `localStorage` do navegador, não no GitHub. Não há login nem criptografia do banco do navegador; **evite informações sigilosas** nesta versão. Abrir o site em outro dispositivo **não sincroniza** registros. Apagar dados do navegador pode apagar registros.

## Como testar o Telegram localmente

Consulte [telegram/README.md](telegram/README.md). Nunca envie token de bot ou chave de API pelo chat nem os publique no GitHub. Se um token tiver sido divulgado, **revogue-o em @BotFather antes de usar**.

## Horários e política já definidos, mas ainda desativados

- Resumos da Vânia: **07h30** e **18h00**.
- Silêncio das **20h00 às 07h30** (fuso `America/Campo_Grande`), com exceções críticas justificadas.
- Prioridades P0 crítica, P1 alta, P2 normal e P3 baixa.
- **Nenhuma notificação automática está ativada.**

## Próximas etapas

1. Ativar e testar bot no Telegram com token rotacionado e `ORBITA_OWNER_ID` restrito.
2. Backend autenticado e memória em banco central com controles de acesso.
3. Conversa por IA com permissões e observabilidade; conexão segura Telegram ⇄ painel.
4. Google Calendar, confirmação de ações, fila de notificações e teste dos horários/silêncio.
5. Testes de ponta a ponta, limites de custo, backup/restauração e deploy do backend.

## Decisões de segurança

- **Nenhuma credencial** na aplicação web, GitHub Pages ou repositório.
- Chaves ficam em variáveis de ambiente privadas no servidor local/hospedagem futura.
- A assinatura ChatGPT não cobre chamadas à API OpenAI utilizadas pelo bot.
- Não inserir memória pessoal ou profissional no repositório público.
- O projeto ainda **não possui backend compartilhado**, autenticação web ou dados sincronizados.