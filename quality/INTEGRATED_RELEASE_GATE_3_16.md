# ORBITA Aurora 3.16 — Consolidação segura dos incrementos

## Contexto
A branch de homologação `feat/supabase-auth-protected-panel` recebeu:
- Aurora 3.14 (PR #24): guarda otimista de concorrência no comando Telegram `/feito`;
- Aurora 3.15 (PR #25): journal write-ahead para a finalização de conciliação local;
- Aurora 3.13 (PR #22): proteção contra alterações oriundas de abas obsoletas.

A PR #23 de cache offline não podia ser integrada diretamente sem reconciliar a
versão do service worker com as alterações posteriores. Esta entrega preserva o
journal 3.15 e reaplica a estratégia de cache restrito, como versão 3.16.

## Integração aplicada
- Escopo estrito do service worker para a aplicação ORBITA publicada no Pages;
  APIs, métodos não GET, requisições de outras origens e URLs desconhecidas não
  são interceptados.
- Lista branca explícita dos arquivos de aplicação; `index.html` só é fallback
  para navegações offline, nunca para JS ou CSS.
- Em arquivo público ausente offline, HTTP 503 em texto para não produzir erro
  MIME enganoso.
- Cache `orbita-pages-v3.16.0-integrated-offline.1`: invalida versões anteriores
  exclusivamente do ORBITA, sem afetar caches de outras aplicações.
- Nova suite `quality/test_service_worker.cjs` com seis cenários Node,
  incorporada ao workflow existente, juntamente com as suítes de integridade,
  chat, backend e navegador simulado.

## Critérios de homologação
| Gate | Evidência | Condição |
| --- | --- | --- |
| Testes unitários de cache | 6 casos Node | Passar na CI |
| Journal de conciliação | Casos Node e Playwright da 3.15 | Não regredir |
| Telegram `/feito` | Python da 3.14 | Não regredir |
| Auth e painel | Playwright mockado | Não regredir |
| Autenticação HTTP real | Duas contas em projeto Supabase dedicado | Pendente |
| Login e recovery no iPhone Safari | Dispositivo real | Pendente |
| RLS real via JWT com duas contas | Requisições HTTP separadas | Pendente |
| PWA offline/atualização no Safari | Dispositivo real | Pendente |
| Segurança de senhas vazadas | Supabase Auth | Requer ativação |
| Deploy web/backend e acesso externo | Hospedagem operante | Pendente |

## Garantias e limitações
A memória local não deve desaparecer nem sincronizar automaticamente. Todas as
alterações da nuvem continuam por confirmação explícita e backup. A proteção
`commitSync` cobre o estado local, não faz rollback de escritas remotas.

Nenhuma alteração direta em `main`, credenciais, banco real, serviços em produção
ou políticas de notificação. A PR #7 continua bloqueada para publicação até passar
pelos gates reais. A PR #23 original pode ser encerrada como substituída apenas
após CI bem-sucedida da versão integrada.

**Próxima fase:** testes de jornadas autenticadas reais em dois dispositivos e
avaliação da política de integração bidirecional antes de ativar automações.
