# ORBITA Aurora 3.47 | Autenticacao SCRAM LOCAL, sem SQL e sem restore.
# Nao e Supabase Auth/JWT/RLS. Nao cria tabelas, banco, roles ou servicos.
# Em -ProbeAuth, operador fornece a senha somente no terminal do proprio Windows.
[CmdletBinding()]
param(
  [switch]$SelfTest,
  [switch]$ProbeAuth,
  [string]$ConfirmLocalCluster = ""
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$expected = "ORBITA-ISOLATED-55432"
$readinessScript = Join-Path $PSScriptRoot "private_restore_native_windows_readiness.ps1"
$psqlBin = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
function Fail([string]$message) { throw [InvalidOperationException]::new($message) }
function Test-Confirm([string]$value) { return ($value -ceq $expected) }
function Test-ReadyGate([string[]]$lines) {
  $identity = @($lines | Where-Object {
    ([string]$_) -ceq "IDENTIDADE: PG17, ACL, configuracao, PID e listener exclusivo aprovados."
  }).Count -eq 1
  $ready = @($lines | Where-Object {
    ([string]$_) -ceq "PG_ISREADY: ACEITANDO_CONEXOES"
  }).Count -eq 1
  $gate = @($lines | Where-Object {
    ([string]$_) -ceq "GATE: PRONTIDAO_TCP_APROVADA."
  }).Count -eq 1
  $blocked = @($lines | Where-Object {
    ([string]$_) -like "GATE: BLOQUEADO*" -or
    ([string]$_) -like "GATE: PRONTIDAO_TCP_NAO_APROVADA*"
  }).Count -gt 0
  return ($identity -and $ready -and $gate -and -not $blocked)
}
function Get-SafeAuthResult([bool]$exited,[int]$code) {
  if ($exited -and $code -eq 0) { return "AUTENTICACAO_LOCAL_APROVADA" }
  return "FALHA_OU_INCONCLUSIVO"
}
if ($SelfTest -and $ProbeAuth) { Fail "Escolha somente um modo." }
if ($SelfTest) {
  $readyLines = @(
    "IDENTIDADE: PG17, ACL, configuracao, PID e listener exclusivo aprovados.",
    "PG_ISREADY: ACEITANDO_CONEXOES",
    "GATE: PRONTIDAO_TCP_APROVADA."
  )
  if (-not (Test-ReadyGate $readyLines) -or
      (Test-ReadyGate @("PG_ISREADY: ACEITANDO_CONEXOES", "GATE: PRONTIDAO_TCP_APROVADA.")) -or
      (Test-ReadyGate (@($readyLines + "GATE: PRONTIDAO_TCP_NAO_APROVADA; nao repetir start."))) -or
      -not (Test-Confirm "ORBITA-ISOLATED-55432") -or
      (Test-Confirm "ORBITA-ISOLATED-5432") -or
      (Get-SafeAuthResult $true 0) -cne "AUTENTICACAO_LOCAL_APROVADA" -or
      (Get-SafeAuthResult $false 0) -cne "FALHA_OU_INCONCLUSIVO" -or
      (Get-SafeAuthResult $true 2) -cne "FALHA_OU_INCONCLUSIVO") {
    Fail "Autoteste de gates SCRAM e saidas sanitizadas falhou."
  }
  Write-Output "AUTOTESTE APROVADO: prontidao, confirmacao e autenticacao local sinteticas, nenhuma senha."
  exit 0
}
if (-not $ProbeAuth) { Fail "Use -SelfTest ou -ProbeAuth. Nenhuma conexao realizada." }
if (-not (Test-Confirm $ConfirmLocalCluster)) {
  Fail "Confirmacao literal ausente/invalida; nenhuma conexao realizada."
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Somente Windows."
}
if (-not (Test-Path -LiteralPath $readinessScript -PathType Leaf) -or
    -not (Test-Path -LiteralPath $psqlBin -PathType Leaf)) {
  Fail "Verificador ou psql PG17 ausente. Nenhuma conexao."
}
foreach ($path in @($readinessScript,$psqlBin)) {
  if (((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Junction/symlink de executavel ou verificador proibido."
  }
}
Write-Output "=== ORBITA 3.47 | AUTENTICACAO LOCAL SCRAM ==="
Write-Output "ALVO_FIXO: 127.0.0.1:55432; usuario local orbita_restore_admin; banco postgres."
Write-Output "LIMITACAO: login local nao demonstra Supabase Auth, JWT, RLS ou restore."
$before = @()
try { $before = @(& $readinessScript -Check) }
catch { Fail "Gate de prontidao falhou; nenhuma credencial solicitada." }
if (-not (Test-ReadyGate $before)) {
  Write-Output "GATE: PRONTIDAO_TCP_PENDENTE; nenhuma credencial solicitada."
  exit 0
}
Write-Output "PRONTIDAO_TCP: APROVADA."
Write-Output "SENHA: informe SOMENTE a senha local do sandbox no prompt oculto. Nunca envie ao chat."
Write-Output "ACAO: uma unica tentativa SCRAM sem SQL; nenhum retry automatico."

$securePassword = $null
$bstr = [IntPtr]::Zero
$plainPassword = $null
$psi = $null
$child = $null
$exited = $false
$code = -1
try {
  $securePassword = Read-Host -Prompt "Senha LOCAL do sandbox ORBITA" -AsSecureString
  if ($null -eq $securePassword -or $securePassword.Length -le 0) {
    Fail "Senha vazia: teste cancelado sem conexao."
  }
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
  $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  $psi = [Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $psqlBin
  # -X: sem psqlrc; -w: sem prompt oculto extra; \conninfo: meta-comando, nenhum SQL.
  $psi.Arguments = '-X -w -q -h "127.0.0.1" -p "55432" -U "orbita_restore_admin" -d "postgres" -c "\conninfo"'
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.EnvironmentVariables["PGPASSWORD"] = $plainPassword
  $psi.EnvironmentVariables["PGHOST"] = "127.0.0.1"
  $psi.EnvironmentVariables["PGPORT"] = "55432"
  $psi.EnvironmentVariables["PGUSER"] = "orbita_restore_admin"
  $psi.EnvironmentVariables["PGDATABASE"] = "postgres"
  $psi.EnvironmentVariables["PGCONNECT_TIMEOUT"] = "5"
  $psi.EnvironmentVariables.Remove("PGSERVICE")
  $psi.EnvironmentVariables.Remove("PGSERVICEFILE")
  $psi.EnvironmentVariables.Remove("PGPASSFILE")
  $child = [Diagnostics.Process]::new()
  $child.StartInfo = $psi
  if (-not $child.Start()) { Fail "Processo de autenticacao nao iniciado." }
  # Drenar ambos em paralelo sem publicar saida. Nenhum processo servidor e iniciado.
  $null = $child.StandardOutput.ReadToEndAsync()
  $null = $child.StandardError.ReadToEndAsync()
  $exited = [bool]$child.WaitForExit(15000)
  if ($exited) { $code = [int]$child.ExitCode }
} catch {
  # Erros internos, incluindo detalhes do servidor, jamais sao divulgados.
  Write-Output "AUTENTICACAO: FALHA_OU_INCONCLUSIVO."
} finally {
  if ($null -ne $psi) { $psi.EnvironmentVariables.Remove("PGPASSWORD") }
  $plainPassword = $null
  if ($bstr -ne [IntPtr]::Zero) {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
  $securePassword = $null
  if ($null -ne $child) { $child.Dispose() }
}
if ((Get-SafeAuthResult $exited $code) -ne "AUTENTICACAO_LOCAL_APROVADA") {
  Write-Output "GATE: AUTENTICACAO_LOCAL_NAO_APROVADA; nao repetir automaticamente."
  Write-Output "RESTAURACAO NAO EXECUTADA. Nao executar SQL 002/003 nem alterar 5432."
  exit 0
}
$after = @()
try { $after = @(& $readinessScript -Check) }
catch { Fail "Verificacao de isolamento apos login inconclusiva; nao prosseguir." }
if (-not (Test-ReadyGate $after)) {
  Write-Output "GATE: ISOLAMENTO_POS_LOGIN_NAO_APROVADO; nenhuma restauracao."
  exit 0
}
Write-Output "AUTENTICACAO: LOCAL_SCRAM_APROVADA."
Write-Output "GATE: IDENTIDADE_TCP_E_LOGIN_LOCAL_APROVADOS."
Write-Output "LIMITACAO: nenhuma consulta SQL; nao comprova restauracao, Supabase Auth, JWT ou RLS."
Write-Output "SEGURANCA: senha temporaria apenas no processo psql, sem arquivo ou stdout."
Write-Output "RESTAURACAO NAO EXECUTADA. SQL 002/003 e producao bloqueados."
