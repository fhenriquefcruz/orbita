# ORBITA Aurora 3.43 — Start no shell interativo + observador passivo

## Evidencia real Windows de 28/10/2026

A Aurora 3.42 mostrou 29 linhas de log, seis marcos:
`POS_3 DESLIGAMENTO`, `POS_4 PRONTIDAO`, `POS_14 DESLIGAMENTO`,
`POS_20 PRONTIDAO`, `POS_27 CHECKPOINT_DESLIGAMENTO`,
`POS_29 DESLIGAMENTO`.

Nao houve `PEDIDO_RECONHECIDO_ENTRE_MARCOS` nem `EXCECAO_CONSOLE_RECONHECIDA_ENTRE_MARCOS`. Estes NAO significam que nao houve pedido nem interferencia externa. `checkpoint starting: shutdown immediate` nao comprova shutdown forcado ou crash.

## Hipotese de trabalho, nao diagnostico

A primeira tentativa usou um processo-filho **`powershell.exe -File ... -Start`**, e o postmaster pode ter recebido um evento associado ao console/processo Windows ao encerrar esse invocador. A sequencia mostra encerramento registrado, mas nao identifica o emissor nem demonstra esse comportamento. O controle correto e testar **uma unica inicializacao explicitamente autorizada no PowerShell interativo que permanece aberto**, distinta do experimento anterior.

Documentacao oficial: [PostgreSQL 17 / pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html), [Relato PostgreSQL bug #18958](https://www.postgresql.org/message-id/18958-e398048dd0cdad11%40postgresql.org). Relato externo e apenas contexto.

## Implementacao

Novo arquivo `quality/private_restore_native_windows_stability.ps1`:
- `-SelfTest`: verifica apenas estados sinteticos; NAO le arquivos privados.
- `-Observe`: SOMENTE LEITURA. Reutiliza o verificador da Aurora 3.37, incluindo identidade do sandbox, ACL, `PG_VERSION=17`, `postgresql.conf`, `pg_hba.conf`, PID do postmaster, listener unico `127.0.0.1:55432`.
- Coleta tres amostras ao longo de ~60 segundos, sem start/stop, SQL, conexao, login ou restauracao.
- Imprime apenas `AMOSTRA_1/2/3`: `ATIVO_ISOLADO`, `PARADO` ou `INCONCLUSIVO` e resultado final.
- Se qualquer verificacao nao confirmar `ATIVO_ISOLADO`, interrompe e NAO reinicia automaticamente.
- Na CI Windows, `-SelfTest` usa apenas texto sintetico. A CI nunca executa `-Observe` e jamais faz start em sandbox.

## Pre-gate Windows: politica de execucao na sessao interativa

**Incidente real (28/10/2026):** apos atualizar o codigo ate `8526715`, o Windows recusou TODAS as chamadas diretas com `& ".\\quality\\...ps1"`, incluindo `-SelfTest`, `-Check`, `verify`, `-Start` e `-Observe`, com `PSSecurityException: UnauthorizedAccess` / "execucao de scripts foi desabilitada neste sistema". **Nenhum desses scripts chegou a executar; a tentativa de start foi bloqueada pela politica antes de invocar o gerenciador.** O Git pull nao altera a politica de execucao.

No **mesmo PowerShell interativo** que permanecera aberto, consultar politica e, somente se as politicas `MachinePolicy` e `UserPolicy` nao estiverem impostas, usar `RemoteSigned` restrito ao processo atual:

```powershell
Get-ExecutionPolicy -List
$enforced = @(Get-ExecutionPolicy -List | Where-Object {
  $_.Scope -in @("MachinePolicy", "UserPolicy") -and $_.ExecutionPolicy -ne "Undefined"
})
if ($enforced.Count -gt 0) { throw "Politica de grupo imposta: nao contornar." }
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
if ((Get-ExecutionPolicy) -ne "RemoteSigned") {
  throw "Politica efetiva nao e RemoteSigned; interromper Gate A e Gate B."
}
```

`-Scope Process` vale somente para essa sessao, sem alterar politica permanente no Registro; ao encerrar o PowerShell, o ajuste deixa de valer. `RemoteSigned` nao equivale a `Bypass`. Nao usar `Unrestricted`, `Bypass`, `LocalMachine`, `CurrentUser` ou `Unblock-File` para contornar controles corporativos. Em maquinas gerenciadas, solicitar revisao ao administrador se a politica de grupo bloquear os scripts.

**Atencao:** na falha do Gate A, NAO executar Gate B. O fato de o `git pull` funcionar nao comprova execucao de nenhum script. Se `-Check` ou `verify` falhar, parar sem tentar `-Start`. O Gate B exige aprovacao explícita do operador, ate quando a politica foi corrigida.

Referencia: [Microsoft Learn — about_Execution_Policies, Windows PowerShell 5.1](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1).

## Executar no Windows — dois gates distintos

**Gate A: somente leitura** (antes de qualquer partida). No PowerShell interativo ja aberto, **nao** invocar um novo `powershell.exe -File` para iniciar o servidor:

```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Alteracoes locais: nao executar git pull." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "Falha no pull." }
& ".\quality\private_restore_native_windows_stability.ps1" -SelfTest
& ".\quality\private_restore_native_windows_cluster.ps1" -Check
& ".\quality\private_restore_native_windows_verify.ps1"
```

Confirmar manualmente `SANDBOX: existente e identidade/configuracao verificadas`, `IDENTIDADE: ... aprovados`, `CLUSTER PARADO` e porta 55432 livre. Se ja estiver ativo, NAO usar `-Start`: usar apenas o observador passivo.

**Gate B: inicio supervisionado** (muda SOMENTE o cluster isolado, requer confirmacao literal do titular). Executar `-Start` **uma unica vez**, apos Gate A aprovado, **no mesmo PowerShell interativo que ficara aberto ate finalizar a observacao**:

```powershell
& ".\quality\private_restore_native_windows_cluster.ps1" -Start -ConfirmLocalCluster ORBITA-ISOLATED-55432
```

Somente se a saida terminar em `CLUSTER INICIADO: escutando exclusivamente 127.0.0.1:55432` e `RESTAURACAO NAO EXECUTADA`, executar **sem fechar o console**:

```powershell
& ".\quality\private_restore_native_windows_stability.ps1" -Observe
```

**Nao usar `powershell.exe -File ... -Start`**, `Start-Process`, `pg_ctl` direto ou reiniciar o servico `postgresql-x64-17`. Compartilhar apenas as linhas sanitizadas de `AMOSTRA_`/`RESULTADO`, sem log ou arquivos brutos.

## Interpretacao

- `ATIVO_E_ISOLADO_NA_JANELA_DE_60_SEGUNDOS`: persistiu durante a sessao interativa por ao menos o periodo observado, sem demonstrar persistencia ao encerrar o terminal, restauracao ou RLS.
- `ESTABILIDADE_NAO_COMPROVADA`: alguma amostra nao confirmou o estado; parar a investigacao sem novos starts.
- Proximo gate, se estável: avaliar persistencia entre processos/consoles por um protocolo independente, **antes de restauracao**.

Apenas `-Start` do gerenciador existente altera o cluster privado e requer `-ConfirmLocalCluster ORBITA-ISOLATED-55432`. Os scripts `-Check`, `-SelfTest`, `-Observe` e `verify` sao somente leitura.

**Bloqueios mantidos:** `pg_restore`, SQL 002/003, `main`, Vercel, Telegram e quaisquer operacoes na porta 5432/servico principal. SHA/TOC aprovados do backup nao provam recuperacao funcional.
