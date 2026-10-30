# ORBITA Aurora 3.9 — Backup completo com restauração segura

## Problema verificado
Até a 3.8, os backups pré-conciliação passaram a incluir tombstones (marcadores de exclusão), mas o botão Importar backup restaurava apenas registros/auditoria; na ausência de chat no arquivo podia apagar a conversa local e não verificava a conta original.

## Comportamento desta atualização
- **Exportar dados** anexa `account_id`, `tombstones`, registros, auditoria e chat ao JSON local.
- Backups automáticos antes de **Trazer da nuvem** ou **Conciliar registros agora** incluem `account_id` e `tombstones` — não incluem chat; a recuperação conserva a conversa atual quando o campo falta.
- **Restaurar backup** verifica autenticação, esquema, limite de 5.000 registros, IDs únicos, tipos, prioridades, estados e título. Até 1.000 caracteres são aceitos para tarefas Telegram.
- Um backup com `account_id` diferente do usuário autenticado é **recusado**, sem modificar registros.
- Backups legados sem identificação de conta são tratados como não vinculados e exibem aviso antes da restauração.
- Os tombstones existentes e os do backup são combinados por revisão mais recente. Se o backup contém um registro que está marcado como excluído, bloqueia a restauração para não ressuscitar a exclusão.
- Se o arquivo omitir chat, o histórico atual é preservado; se trouxer chat, esse histórico é restaurado após confirmação.
- Antes de qualquer substituição, é gerado um **backup de segurança do estado atual** com conta e exclusões. O usuário precisa confirmar que o arquivo foi efetivamente salvo.
- Antes das gravações locais, verificam-se conta autenticada, vínculo do aparelho e ausência de mudança em registros/chat/tombstones. Em erro de escrita, o app tenta recuperar os valores anteriores; o backup de segurança permite recuperação manual.
- Tudo ocorre no armazenamento local. Não há escrita no Supabase e não foi executada modificação no bot Telegram, banco ou variáveis Vercel.

## Limites operacionais
- A recuperação substitui a coleção local depois de dois consentimentos; ela não reconcilia estados com a nuvem e não altera registros remotos.
- Backups antigos sem `account_id` não comprovam titularidade. Devem ser usados somente pelo titular que confia na origem.
- Backups com tombstones e registros contraditórios são recusados: revisão humana é necessária.
- Armazenamento local não é transacional. Em falhas de armazenamento, recuperar manualmente a partir do backup de segurança.
- Arquivos acima de 8 MB são recusados.

## Gates
- Testes Node para backup completo, legado, tombstones, registros divergentes, usuário incorreto, tipos inválidos e conversa ausente.
- Playwright com provedor mock: tenta arquivo de outra conta (recusa), restaura backup válido com download prévio, preserva exclusões antigas + novas e conversa local, confirma login e operação sem gravação na nuvem.
- PR principal de Auth continua como rascunho até homologação com duas contas reais, Safari iPhone e recuperação de senha.

## Aceitação manual
1. Entrar com a conta do ORBITA na prévia.
2. Dados e histórico → Exportar dados (JSON), conferir que o arquivo foi salvo.
3. Em ambiente de homologação e após exportação, clicar Restaurar backup e selecionar o arquivo.
4. Conferir mensagens de confirmação, backup pré-restauração, dados e marcadores de exclusão (pelo acompanhamento técnico).
5. Verificar que o Telegram não perdeu ou duplicou a tarefa registrada.