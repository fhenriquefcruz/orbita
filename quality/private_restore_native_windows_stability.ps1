# ORBITA Aurora 3.43 | Monitoramento SOMENTE LEITURA do cluster nativo Windows.
# NAO inicia/para o PostgreSQL. NAO abre conexoes de rede nem executa SQL/restore.
# Usar na MESMA sessao PowerShell interativa da inicializacao explicitamente autorizada.
[CmdletBinding()]
param(
  [switch]$SelfTest,
  [switch]$Observe
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Get-SafeState([string[]]$messages,[int]$exitCode) {
  if ($exitCode -ne 0) { return "INCONCLUSIVO" }
  $active = @($messages | Where-Object {
    ([string]$_) -clike "CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432.*"
  }).Count -gt 0
  $stopped = @($messages | Where-Object {
    ([string]$_) -like "CLUSTER PARADO:*"
  }).Count -gt 0
  if ($active -and -not $stopped) { return "ATIVO_ISOLADO" }
  if ($stopped -and -not $active) { return "PARADO" }
  return "INCONCLUSIVO"
}

if ($SelfTest -and $Observe) { Fail "Escolha apenas um modo." }
if ($SelfTest) {
  $good = @(
    "IDENTIDADE: marcador ORBITA, versao 17, ACL e configuracao de rede aprovados.",
    "CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432.",
    "RESTAURACAO: NAO EXECUTADA."
  )
  $off = @("CLUSTER PARADO: instancia isolada existe.")
  if ((Get-SafeState $good 0) -cne "ATIVO_ISOLADO" -or
      (Get-SafeState $off 0) -cne "PARADO" -or
      (Get-SafeState $good 1) -cne "INCONCLUSIVO" -or
      (Get-SafeState (@($good + $off)) 0) -cne "INCONCLUSIVO" -or
      (Get-SafeState @("login user@example.test SQL privado") 0) -cne "INCONCLUSIVO") {
    Fail "Autoteste de estados ou sanitizacao falhou."
  }
  Write-Output "AUTOTESTE APROVADO: estados sinteticos, nenhuma conexao ou cluster acessado."
  exit 0
}
if (-not $Observe) { Fail "Escolha -SelfTest ou -Observe. Nenhuma acao executada." }
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Observacao requer Windows."
}
$verifyScript = Join-Path $PSScriptRoot "private_restore_native_windows_verify.ps1"
if (-not (Test-Path -LiteralPath $verifyScript -PathType Leaf)) {
  Fail "Verificador privado da Aurora 3.37 nao encontrado."
}
if (((Get-Item -LiteralPath $verifyScript -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
  Fail "Verificador nao pode ser junction/symlink."
}

Write-Output "=== ORBITA 3.43 | OBSERVACAO PASSIVA DO CLUSTER ISOLADO ==="
Write-Output "AMOSTRAS: inicio, mais 15 segundos e mais 45 segundos (total 60)."
Write-Output "SEM START: o monitor usa apenas o verificador de identidade/porta da Aurora 3.37."
$index = 0
foreach ($delay in @(0,15,45)) {
  if ($delay -gt 0) { Start-Sleep -Seconds $delay }
  $index++
  $output = @()
  $exitCode = 1
  try {
    # Chamada de script no mesmo processo PowerShell, SEM criar powershell.exe filho.
    $output = @(& $verifyScript)
    $exitCode = if ($LASTEXITCODE -is [int]) { [int]$LASTEXITCODE } else { 0 }
  } catch {
    # Erros e caminhos brutos nunca sao transmitidos.
    $output = @()
    $exitCode = 1
  }
  $state = Get-SafeState $output $exitCode
  Write-Output ("AMOSTRA_" + $index + ": " + $state)
  if ($state -ne "ATIVO_ISOLADO") {
    Write-Output "RESULTADO: ESTABILIDADE_NAO_COMPROVADA."
    Write-Output "RESTAURACAO BLOQUEADA. Nao repetir -Start automaticamente."
    exit 0
  }
}
Write-Output "RESULTADO: ATIVO_E_ISOLADO_NA_JANELA_DE_60_SEGUNDOS."
Write-Output "ATENCAO: nao prova persistencia apos fechar o console; precisa de teste separado."
Write-Output "RESTAURACAO NAO EXECUTADA. SQL 002/003, main e producao continuam bloqueados."
