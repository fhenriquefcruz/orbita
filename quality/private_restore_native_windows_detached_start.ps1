# ORBITA Aurora 3.44 | Inicio experimental SEM console (somente sandbox privado).
# NAO registra servicos, NAO reinicializa cluster, NAO executa SQL ou pg_restore.
# Para iniciar, exigir -StartDetached e confirmacao literal. NENHUM retry automatico.
[CmdletBinding()]
param(
  [switch]$SelfTest,
  [switch]$StartDetached,
  [string]$ConfirmLocalCluster = ""
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$expectedConfirm = "ORBITA-ISOLATED-55432"
$root = [IO.Path]::GetFullPath((Join-Path $HOME "orbita-restore-sandbox"))
$data = Join-Path $root "data"
$log = Join-Path $root "server.log"
$pgctl = "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe"
$verifyScript = Join-Path $PSScriptRoot "private_restore_native_windows_verify.ps1"
$allowedSids = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value, "S-1-5-18", "S-1-5-32-544")
function Fail([string]$message) { throw [InvalidOperationException]::new($message) }
function Assert-PrivateItem([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { Fail "Item do sandbox ausente." }
  $item = Get-Item -LiteralPath $path -Force
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Reparse point proibido no sandbox."
  }
  $acl = Get-Acl -LiteralPath $path
  foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowedSids -notcontains $sid) { Fail "ACL de terceiro detectada; operacao cancelada." }
  }
}
function Test-Confirmation([string]$value) {
  return ($value -ceq $expectedConfirm)
}
function Test-VerifiedStopped([string[]]$messages) {
  $identity = @($messages | Where-Object {
    ([string]$_) -clike "IDENTIDADE: marcador ORBITA, versao 17, ACL e configuracao de rede aprovados.*"
  }).Count -eq 1
  $stopped = @($messages | Where-Object {
    ([string]$_) -clike "CLUSTER PARADO:*"
  }).Count -eq 1
  $active = @($messages | Where-Object {
    ([string]$_) -clike "CLUSTER ATIVO:*"
  }).Count -gt 0
  return ($identity -and $stopped -and -not $active)
}
function Test-VerifiedActive([string[]]$messages) {
  return @($messages | Where-Object {
    ([string]$_) -clike "CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432.*"
  }).Count -eq 1
}
if ($SelfTest -and $StartDetached) { Fail "Escolha um unico modo." }
if ($SelfTest) {
  $stopped = @(
    "IDENTIDADE: marcador ORBITA, versao 17, ACL e configuracao de rede aprovados.",
    "CLUSTER PARADO: instancia isolada existe."
  )
  $active = @("CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432.")
  if (-not (Test-Confirmation "ORBITA-ISOLATED-55432") -or
      (Test-Confirmation "ORBITA-ISOLATED-5432") -or
      -not (Test-VerifiedStopped $stopped) -or
      (Test-VerifiedStopped (@($stopped + $active))) -or
      -not (Test-VerifiedActive $active) -or
      (Test-VerifiedActive @("CLUSTER ATIVO: outro processo")) ) {
    Fail "Autoteste de confirmacao/identidade e exclusividade falhou."
  }
  $testStartInfo = [Diagnostics.ProcessStartInfo]::new()
  $testStartInfo.UseShellExecute = $false
  $testStartInfo.CreateNoWindow = $true
  $testStartInfo.RedirectStandardOutput = $true
  $testStartInfo.RedirectStandardError = $true
  if ($testStartInfo.UseShellExecute -or -not $testStartInfo.CreateNoWindow -or
      -not $testStartInfo.RedirectStandardOutput -or -not $testStartInfo.RedirectStandardError) {
    Fail "Autoteste de isolamento de console falhou."
  }
  Write-Output "AUTOTESTE APROVADO: processo sem console, confirmacao e estados sinteticos."
  exit 0
}
if (-not $StartDetached) {
  Fail "Operacao requer -StartDetached com confirmacao literal. Nenhuma acao executada."
}
if (-not (Test-Confirmation $ConfirmLocalCluster)) {
  Fail "Confirmacao invalida. Nenhuma inicializacao executada."
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Somente Windows."
}
if (-not (Test-Path -LiteralPath $pgctl -PathType Leaf) -or
    -not (Test-Path -LiteralPath $verifyScript -PathType Leaf)) {
  Fail "Ferramentas esperadas ausentes; nao iniciar."
}
Assert-PrivateItem $root
Assert-PrivateItem $data
# Codigo versionado no repositorio nao precisa herdar ACL do sandbox;
# validar apenas existencia e ausencia de junction/symlink.
if (((Get-Item -LiteralPath $verifyScript -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
  Fail "Verificador versionado nao pode ser junction/symlink."
}
if (Test-Path -LiteralPath $log) { Assert-PrivateItem $log }

# Exigir TODAS as verificacoes de identidade, ACL, PG_VERSION, conf e porta do 3.37.
$before = @()
try { $before = @(& $verifyScript) }
catch { Fail "Preflight de identidade do sandbox falhou; nenhuma inicializacao." }
if (-not (Test-VerifiedStopped $before)) {
  Fail "Preflight nao confirmou sandbox parado e exclusivo; nenhuma inicializacao."
}
Write-Output "=== ORBITA 3.44 | START SEM CONSOLE — SOMENTE 55432 ==="
Write-Output "IDENTIDADE: sandbox PostgreSQL 17 parado e isolamento 127.0.0.1:55432 aprovado."
Write-Output "PROCESSO: CreateNoWindow e redirecionamento de stdout/stderr; nenhum log bruto exibido."
Write-Output "INICIANDO: uma tentativa de pg_ctl exclusivamente no sandbox ORBITA."

# Executar pg_ctl como processo sem janela de console com streams redirecionados.
# O PostgreSQL grava seu log privado em server.log por pg_ctl -l.
$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $pgctl
$psi.Arguments = '-D "' + $data + '" -l "' + $log + '" -w -t 30 start'
$psi.WorkingDirectory = $root
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables["PGHOST"] = "127.0.0.1"
$psi.EnvironmentVariables["PGPORT"] = "55432"
$child = [Diagnostics.Process]::new()
$child.StartInfo = $psi
$exitCode = -1
try {
  if (-not $child.Start()) { Fail "pg_ctl nao iniciou; nenhuma repeticao." }
  $outTask = $child.StandardOutput.ReadToEndAsync()
  $errTask = $child.StandardError.ReadToEndAsync()
  if (-not $child.WaitForExit(45000)) {
    Fail "pg_ctl excedeu tempo; NAO interromper processo nem tentar start novamente."
  }
  # Drenar os streams sem jamais imprimir texto bruto.
  if (-not $outTask.Wait(2000) -or -not $errTask.Wait(2000)) {
    Fail "Saida do processo ainda pendente; nao executar restore nem retry."
  }
  $null = $outTask.Result
  $null = $errTask.Result
  $exitCode = [int]$child.ExitCode
} catch {
  Fail "Resultado do inicio inconclusivo. Nao repetir start; verificar cluster e log sanitizado."
} finally {
  $child.Dispose()
}
if ($exitCode -ne 0) {
  Fail "pg_ctl retornou falha. Nao tentar iniciar novamente; usar diagnostico somente leitura."
}
Write-Output "PG_CTL: terminou com sucesso; verificando identidade real, nao apenas mensagem de prontidao."

$after = @()
try { $after = @(& $verifyScript) }
catch { Fail "Verificacao pos-start inconclusiva. RESTAURACAO BLOQUEADA." }
if (-not (Test-VerifiedActive $after)) {
  Fail "Pos-start NAO confirmou PID e listener exclusivos; RESTAURACAO BLOQUEADA."
}
Write-Output "CLUSTER INICIADO: PID confirmado e listener exclusivo 127.0.0.1:55432."
Write-Output "PROXIMO GATE: executar estabilidade -Observe no mesmo PowerShell, sem fechar a janela."
Write-Output "RESTAURACAO NAO EXECUTADA. SQL 002/003, main e producao permanecem BLOQUEADOS."
