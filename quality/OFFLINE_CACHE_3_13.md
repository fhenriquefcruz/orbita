# ORBITA Aurora 3.13 — Cache PWA controlado e fallback offline seguro

## Problema corrigido
O service worker Aurora 3.12 interceptava toda solicitação GET do mesmo domínio e,
na falta de conexão, podia responder com o `index.html` quando o navegador solicitava
um arquivo `.js`, CSS ou outro recurso. Além de erro de MIME, isso dificultava
diagnosticar falhas de carregamento e permitia armazenar URLs imprevistas em cache.

## Implementação
- Restrição de interceptação ao próprio escopo do aplicativo (por exemplo, `/orbita/`).
- Lista explícita de recursos estáticos públicos, preservando os scripts de Auth,
  a folha de estilos Aurora, o módulo de integridade e o manifesto.
- Requisições externas, APIs, métodos diferentes de GET e URLs de recurso desconhecidas
  deixam de ser interceptadas ou armazenadas.
- Navegações offline continuam usando somente o `index.html` já instalado.
- Recursos JS/CSS sem cópia offline retornam HTTP 503 texto, **nunca HTML**.
- Cache versionado `orbita-pages-v3.13.0-offline-scope.1`: remove apenas
  versões antigas com prefixo `orbita-pages-`; caches de outras aplicações permanecem.
- Nenhum dado pessoal, segredo, token, resposta autenticada ou conteúdo do Supabase
  é colocado deliberadamente no Cache Storage.

## Evidências e testes
Teste novo: `node --test quality/test_service_worker.cjs`. Cenários:
1. JS offline existente mantém conteúdo e tipo original.
2. JS ausente retorna 503 e não recebe o documento HTML.
3. Navegação offline recebe o documento da aplicação.
4. APIs, outros domínios, caminhos fora do escopo, arquivos desconhecidos e POST não são interceptados.
5. Rede disponível atualiza apenas um recurso estático permitido.
6. Ativação descarta cache antigo do ORBITA sem afetar outros caches.

Validação inicial: seis casos unitários aprovados no Node 22 (ambiente local de desenvolvimento),
e `node --check docs/sw.js` sem erro. O workflow `.github/workflows/tests.yml`
passa a executar esses casos com os demais testes.

## Limites de homologação
Testes em VM de Service Worker não substituem um teste real no Safari/iPhone:
validar instalação, primeira atualização, recarga offline, troca de versão do cache
e experiência ao abrir uma página sem sessão Auth ativa. Sem serviço Supabase disponível,
a tela protegida deve continuar bloqueada; offline não significa burlar autenticação.

Branch de homologação: `feat/supabase-auth-protected-panel` (PR #7 em draft).
Não modificar `main`, backend Telegram, Supabase real, credenciais ou notificações
antes dos gates previstos no Plano Mestre.
