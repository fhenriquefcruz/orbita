# ORBITA Aurora 3.8 — Importação segura da memória em nuvem

## Finalidade
Oferecer um caminho unidirecional para trazer atividades criadas no Telegram para a memória local do Aurora, sem executar operações de escrita no Supabase. O comando **Trazer da nuvem** fica separado da conciliação bidirecional avançada.

## Comportamento
- Ação explícita no painel autenticado: Dados e histórico → Memória central → Trazer da nuvem.
- O aplicativo consulta os registros visíveis ao JWT da conta com RLS, compara IDs e adiciona apenas os IDs ausentes na memória local.
- Registros de mesmo ID com conteúdo idêntico ou divergente não são sobrescritos. A divergência aparece no resumo para conferência.
- Tombstones (exclusões locais pendentes) impedem que a importação ressuscite registros removidos no dispositivo.
- Duplicatas, payloads incoerentes e títulos vazios são ignorados e contabilizados.
- O usuário vê o resultado da comparação e precisa confirmar a importação e o salvamento efetivo de um backup antes de qualquer alteração.
- O backup agora guarda também tombstones, além de registros e trilha de auditoria, para não descartar o histórico de exclusões na recuperação manual.
- Antes de gravar a memória local, o navegador verifica se conta Auth, conjunto de registros, tombstones e associação do dispositivo continuam inalterados.
- Nenhum POST, PATCH ou DELETE é efetuado: a importação só faz GET remoto e grava o armazenamento local após consentimento explícito.

## Limitações
- O backup inclui tombstones para preservação e inspeção. A importação de backup legado pela interface não restaura automaticamente tombstones; uma restauração completa destes marcadores exigirá evolução específica.
- A importação não atualiza registros locais que já existam com o mesmo ID. Para decidir entre versões, permanece a conciliação bidirecional, que exige revisão, backup e confirmação.
- Uma leitura paginada não é snapshot transacional. A ação pode exigir nova importação se dados mudarem enquanto as páginas forem lidas.
- Os dados importados passam a existir no armazenamento local não criptografado deste navegador. Evitar dispositivos compartilhados e registros sensíveis até que o armazenamento seja protegido.

## Testes
- Funções puras validam: novos registros, colisões divergentes/iguais, tombstones, duplicatas, payloads inválidos e entradas inconsistentes.
- Smoke Playwright comprova que o botão cria registro apenas na memória local após confirmação do backup, que não altera tombstones e que a API Supabase recebe exclusivamente requisições GET.
- Gates prévios de Auth, RLS simulado, responsividade, XSS, concorrência e verificação de segredos continuam ativos.

## Critérios pendentes para publicação pública
- Homologação real com duas contas Auth independentes e recuperação de senha no Safari.
- Teste manual de arquivo de backup salvo e importação real no aparelho do usuário.
- A PR principal de autenticação permanece em modo rascunho; esta atualização não entra na branch pública main sem esses gates.
- Bot Telegram, tarefa de teste, chaves, variáveis Vercel e banco Supabase de produção permanecem intactos.