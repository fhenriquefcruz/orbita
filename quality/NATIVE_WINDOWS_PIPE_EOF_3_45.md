# ORBITA Aurora 3.45 — Cluster ativo; falso erro na coleta de stdout/stderr

## Evidencia real, 28/10/2026

Execucao única da Aurora 3.44 com `-StartDetached -ConfirmLocalCluster ORBITA-ISOLATED-55432`:
- Preflight confirmou identidade do sandbox PostgreSQL 17, isolamento em `127.0.0.1:55432` e cluster inicialmente parado.
- O novo processo `pg_ctl` foi iniciado com `CreateNoWindow=true` e stdout/stderr redirecionados.
- O wrapper exibiu `Resultado do inicio inconclusivo` antes de exibir `PG_CTL: terminou...`.
- **Imediatamente depois**, o monitor passivo Aurora 3.43 reportou:
  `AMOSTRA_1: ATIVO_ISOLADO`,
  `AMOSTRA_2: ATIVO_ISOLADO`,
  `AMOSTRA_3: ATIVO_ISOLADO`,
  `RESULTADO: ATIVO_E_ISOLADO_NA_JANELA_DE_60_SEGUNDOS`.
- Nenhuma restauracao executada; nenhuma operacao na porta principal 5432.

**Conclusao comprovada:** o banco real estava ativo e validado pelo verificador de PID/porta por 60 s, apesar do wrapper dizer "inconclusivo". A persistencia apos fechar o console original ainda NAO foi demonstrada.

## Causa provavel do falso-negativo

Na Aurora 3.44, apos `pg_ctl.WaitForExit(45000)`, o wrapper exigia que ambas as tarefas `StandardOutput.ReadToEndAsync()` e `StandardError.ReadToEndAsync()` finalizassem em apenas 2 segundos; caso contrario, devolvia a mesma mensagem generica de erro.

Um postmaster iniciado por `pg_ctl` pode herdar handles de escrita dos pipes. O `ReadToEndAsync` depende de EOF do **ultimo** processo com esse handle, não necessariamente do encerramento do `pg_ctl` original. Isso **pode** explicar a discrepancia; a excecao interna foi propositalmente suprimida, portanto nao ha prova definitiva do ponto exato em que ocorreu a falha.

Referencia: [Microsoft .NET Blog — Process API Improvements / Handle inheritance](https://devblogs.microsoft.com/dotnet/process-api-improvements-in-dotnet-11/); [Microsoft Learn — Process.StandardOutput](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process.standardoutput).

## Correcao no repositorio (sem atuar no banco)

A Aurora 3.45 remove a obrigacao de concluir `ReadToEndAsync` (EOF) como gate. Ela:
1. Ainda espera `pg_ctl` terminar dentro do prazo e obtem seu `ExitCode`.
2. Verifica apenas indicadores booleanos dos streams sem imprimir o conteudo.
3. Se o exit code nao for zero ou se o processo nao encerrar, conserva o bloqueio.
4. Exige a mesma verificacao posterior Aurora 3.37 de PID e listener exclusivo do sandbox **antes de informar sucesso**.
5. Mantem confirmacao literal, isolamento, processo sem janela, log privado, nenhuma tentativa automatica, e bloqueios contra SQL/restore.
6. Inclui `-SelfTest` com exit code zero e streams ainda abertos para impedir regressao no Windows CI.

**Importante:** esta mudanca nao reinicia nem modifica o cluster ativo. Os testes CI nao iniciam PostgreSQL real, apenas validam o codigo com dados sinteticos.

## Proximo gate — somente leitura, SEM start

Apos CI aprovada e merge na homologacao, manter a janela original aberta. Em outro processo PowerShell (se possivel, em outra janela), executar:

```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Alteracoes locais; nao executar pull." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "Falha no pull." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_detached_start.ps1" -SelfTest
if ($LASTEXITCODE -ne 0) { throw "Autoteste falhou." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_verify.ps1"
```

**NAO** executar `-StartDetached` ou `-Start` se `CLUSTER ATIVO`. A verificação em novo processo mostra independencia do monitor e confirmar status em outro processo, mas **nao testa** persistencia apos fechar a janela original. Nao fechar a janela original ainda. Se parar, interromper; nao repetir start.

Para comprovar independencia **entre janelas**, depois de passar o primeiro gate, abrir outra janela do Windows PowerShell e executar somente o verificador 3.37 via `powershell.exe ... -File`; manter a janela de origem aberta. Nao executar scripts a partir de locais nao versionados.

## Estado dos gates de entrega

- **Aprovado:** estrutura e ACL do sandbox; port 55432; SHA e inventario do arquivo `.dump`; estabilidade de 60 s em sessao ativa.
- **Pendente:** persistencia apos encerrar console; recuperacao real em banco privado; smoke tests funcionais; Auth/JWT/RLS.
- **Bloqueado:** `pg_restore`, migracoes SQL 002/003, `main`, produção e alteracoes no servico `postgresql-x64-17` porta 5432.

A Issue #58 acompanha a ocorrência. Nada neste PR autoriza restauracao.
