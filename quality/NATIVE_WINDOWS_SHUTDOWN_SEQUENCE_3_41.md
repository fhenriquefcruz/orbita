# ORBITA Aurora 3.41 — Sequencia sanitizada de prontidao e desligamento

## Evidencia real recebida (28/10/2026)

A Aurora 3.40, executada em Windows no sandbox dedicado da porta 55432, informou:

- `SERVER_LOG: PRESENTE; TAMANHO=ATE_4KB` e ultima atualizacao `ATE_24H`;
- `LINHAS_INSPECIONADAS: 29`; `LINHAS_NAO_VAZIAS: 29`;
- `EVENTOS_CLASSIFICADOS: 26`;
- `CATEGORIA: PRONTIDAO`, `DESLIGAMENTO` e `REGISTRO_GERAL`;
- `CURRENT_LOGFILES: AUSENTE` e `POSTMASTER_PID: ARQUIVO_AUSENTE`;
- `logging_collector` e `log_destination` nao declarados no arquivo consultado.

Interpretacao: ha mensagens de prontidao e parada, mas as categorias anteriores nao demonstram se sao da mesma tentativa, em que ordem ocorreram ou **quem provocou** a parada. A inexistencia de uma categoria de pedido explicito nao prova que nao houve solicitacao; outro idioma, outro destino ou outra mensagem podem ter sido utilizados.

## Mudanca cirurgica

O script **existente** `quality/private_restore_native_windows_log_evidence.ps1` agora:

1. Preserva validacoes de marcador ORBITA, ACL, PG_VERSION e protecao contra symlink.
2. Continua lendo no maximo as ultimas 300 linhas do `server.log` privado.
3. Produz apenas os ultimos 12 marcos reconhecidos, em ordem e com posicao relativa na janela de leitura: `PRONTIDAO`, `PEDIDO_DESLIGAMENTO`, `ENCERRANDO`, `CHECKPOINT_DESLIGAMENTO`, `DESLIGAMENTO`, `PANIC`, `FATAL`, `ERROR`.
4. Compara a ultima prontidao e ultimo desligamento classificados e informa se um pedido reconhecido aparece **entre esses marcos**.
5. Nunca imprime dados da linha, usuario, SQL, caminho privado, valor de configuracao, timestamp, PID nem detalhes de diagnostico confidencial.
6. Executa `-SelfTest` com mensagens inteiramente sinteticas. CI Windows valida parser, teste e guardas de saida.

`MARCO: POS_N CATEGORIA` significa apenas posicao na janela inspecionada. **Nao corresponde a linha absoluta do log e nao estabelece relacao causal nem identifica qual processo sinalizou o encerramento.** A janela tambem pode abranger mais de uma inicializacao.

## Comando seguro, apos CI aprovada e merge somente em homologacao

```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Alteracoes locais; pull abortado." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "Falha no git pull." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_log_evidence.ps1" -SelfTest
if ($LASTEXITCODE -ne 0) { throw "Autoteste falhou." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_log_evidence.ps1"
```

Compartilhar apenas a saida do script. Nao compartilhar linhas brutas de `server.log`, `postgresql.conf`, `postmaster.pid`, dump ou credenciais.

## Interpretacao do proximo resultado

- `ORDEM: PRONTIDAO_ANTES_DO_ULTIMO_DESLIGAMENTO`: confirma ordem observada no trecho, **nao o mecanismo da parada**.
- `PEDIDO_RECONHECIDO_ENTRE_MARCOS: SIM`: houve log de solicitacao dentro da janela analisada; investigar localmente qual mecanismo solicitou.
- `PEDIDO_RECONHECIDO_ENTRE_MARCOS: NAO`: o parser nao identificou solicitacao com as expressoes conhecidas; **nao** presume encerramento forcado nem sinal externo.
- `ORDEM: ULTIMA_PRONTIDAO_APOS_ULTIMO_DESLIGAMENTO`: o arquivo contem ao menos uma prontidao posterior ao ultimo desligamento reconhecido, sem demonstrar estado atual.
- `ORDEM: INSUFICIENTE_PARA_COMPARACAO`: nao inferir nada; planejar outra coleta segura.

## Gates que permanecem bloqueados

Cluster isolado com status anterior `PARADO`; nenhuma repeticao de `-Initialize`, `-Start`, SQL, `pg_restore` ou operacao no servidor principal da porta 5432. Arquivo dump possui integridade anteriormente aprovada, **restauracao real ainda nao executada**. SQL 002/003, deploy em `main`, Vercel e Telegram permanecem bloqueados.
