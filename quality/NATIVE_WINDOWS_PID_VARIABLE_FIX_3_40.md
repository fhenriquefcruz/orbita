# ORBITA Aurora 3.40 — correcao do conflito com a variavel automatica $PID

## Evidencia observada (28/10/2026)

O titular atualizou o staging ate `29adc9d` e executou o diagnostico `private_restore_native_windows_log_evidence.ps1`:

- `-SelfTest`: **AUTOTESTE APROVADO**;
- `CONFIG: logging_collector=NAO_DECLARADO; log_destination=NAO_DECLARADO`;
- `CURRENT_LOGFILES: AUSENTE`;
- excecao PowerShell: `VariableNotWritable`, tentativa de sobrescrever `PID`.

**Causa demonstrada do erro do script**: a variavel `$PID` e automatica, somente leitura e nao diferenciada por maiusculas/minusculas. A linha `$pid = Join-Path $data "postmaster.pid"` interrompia o script antes de classificar `postmaster.pid` e o `server.log`. **Isso nao explica, por si, o motivo de o PostgreSQL isolado estar parado.**

## Correcao

- Substituida a variavel `$pid` pelo nome `$postmasterPidFile` em suas tres ocorrencias, sem mudar o comportamento planejado.
- Incluido gate CI Windows que inspeciona a AST do script e rejeita atribuicoes diretas a variaveis automaticas protegidas (`$PID`, `$Host`, `$PSHOME`).
- Mantidos os controles de identidade/ACL, classificacao sanitizada e ausencia de escrita.

## Executar somente depois de CI e merge no staging

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

Envie somente a saida **sanitizada**, jamais linhas originais de `server.log`, senhas, arquivos `.dump` ou configuracoes completas.

## Interpretacao e proximos gates

A ausencia de `logging_collector` ou `log_destination` declarados no arquivo nao prova que nenhum log existe. `CURRENT_LOGFILES: AUSENTE` tambem nao prova que a inicializacao nao gerou mensagens.

Aguardar evidencia de `SERVER_LOG`, `LINHAS_NAO_VAZIAS`, `EVENTOS_CLASSIFICADOS`, tamanho aproximado e idade antes de formular hipotese de encerramento.

Nao executar `-Initialize`, `-Start`, `pg_restore`, SQL, operacoes na porta 5432, Supabase, migracoes SQL 002/003 ou publicar `main`. Restauração funcional permanece nao testada.
