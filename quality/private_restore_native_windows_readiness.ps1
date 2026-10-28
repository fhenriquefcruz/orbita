# ORBITA Aurora 3.46 | Verificacao de prontidao TCP do cluster isolado.
# Somente pg_isready no loopback: nao autentica, nao executa SQL ou pg_restore,
# nao executa initdb/start/stop e nao altera configuracao de cluster ou servicos.
[CmdletBinding()]
param([switch]$SelfTest, [switch]$Check)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$verifyScript = Join-Path $PSScriptRoot "private_restore_native_windows_verify.ps1"
$readyBin = "C:\Program Files\PostgreSQL\17\bin\pg_isready.exe"

function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Get-SafeReadiness([int]$exitCode) {
  switch ($exitCode) {
    0 { return "ACEITANDO_CONEXOES" }
    1 { return "RECUSANDO_CONEXOES" }
    2 { return "SEM_RESPOSTA" }
    3 { return "PARAMETROS_INVALIDOS" }
    default { return "INCONCLUSIVO" }
  }
}
function Test-IsolatedActive([string[]]$messages) {
  $identity = @($messages | Where-Object {
    ([string]$_) -ceq "IDENTIDADE: marcador ORBITA, versao 17, ACL e configuracao de rede aprovados."
  }).Count -eq 1
  $active = @($messages | Where-Object {
    ([string]$_) -ceq "CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432."
  }).Count -eq 1
  $stopped = @($messages | Where-Object {
    ([string]$_) -clike "CLUSTER PARADO:*"
  }).Count -gt 0
  return ($identity -and $active -and -not $stopped)
}
if ($SelfTest -and $Check) { Fail "Escolha apenas um modo." }
if ($SelfTest) {
  $good = @(
    "IDENTIDADE: marcador ORBITA, versao 17, ACL e configuracao de rede aprovados.",
    "CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432."
  )
  if (-not (Test-IsolatedActive $good) -or
      (Test-IsolatedActive @("CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432.")) -or
      (Test-IsolatedActive (@($good + "CLUSTER PARADO: instancia existe."))) -or
      (Get-SafeReadiness 0) -cne "ACEITANDO_CONEXOES" -or
      (Get-SafeReadiness 1) -cne "RECUSANDO_CONEXOES" -or
      (Get-SafeReadiness 2) -cne "SEM_RESPOSTA" -or
      (Get-SafeReadiness 3) -cne "PARAMETROS_INVALIDOS" -or
      (Get-SafeReadiness 77) -cne "INCONCLUSIVO") {
    Fail "Autoteste de identidade ou classificacao de retorno falhou."
  }
  Write-Output "AUTOTESTE APROVADO: quatro codigos de prontidao, isolamento e nenhum servidor acessado."
  exit 0
}
if (-not $Check) { Fail "Execute -SelfTest ou -Check; nenhuma conexao executada." }
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Diagnostico de prontidao requer Windows."
}
if (-not (Test-Path -LiteralPath $verifyScript -PathType Leaf) -or
    -not (Test-Path -LiteralPath $readyBin -PathType Leaf)) {
  Fail "Verificador ou binario PG17 pg_isready ausente. Nao prosseguir."
}
foreach ($itemPath in @($verifyScript,$readyBin)) {
  if (((Get-Item -LiteralPath $itemPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Verificador ou binario via junction/symlink proibido."
  }
}
Write-Output "=== ORBITA 3.46 | PRONTIDAO TCP DO SANDBOX ==="
Write-Output "ALVO_FIXO: IPv4 127.0.0.1:55432, PostgreSQL 17."
$lines = @()
try { $lines = @(& $verifyScript) } catch {
  Fail "Isolamento do cluster nao aprovado. Sem tentativa de conexao."
}
if (-not (Test-IsolatedActive $lines)) {
  Write-Output "IDENTIDADE: NAO_APROVADA_PARA_TESTE_TCP."
  Write-Output "GATE: BLOQUEADO; nenhum teste TCP realizado."
  exit 0
}
Write-Output "IDENTIDADE: PG17, ACL, configuracao, PID e listener exclusivo aprovados."
$code = -1
try {
  # pg_isready verifica apenas o estado do servidor; nao faz autenticacao nem SQL.
  # Argumentos fixos impedem fallback para o servico principal em 5432.
  & $readyBin -h "127.0.0.1" -p "55432" -U "orbita_restore_admin" -d "postgres" -q -t "3" 1>$null 2>$null
  $code = [int]$LASTEXITCODE
} catch {
  $code = -1
}
$status = Get-SafeReadiness $code
Write-Output ("PG_ISREADY: " + $status)
if ($status -eq "ACEITANDO_CONEXOES") {
  Write-Output "GATE: PRONTIDAO_TCP_APROVADA."
} else {
  Write-Output "GATE: PRONTIDAO_TCP_NAO_APROVADA; nao repetir start."
}
Write-Output "LIMITACAO: este teste nao valida senha, SQL, integridade restaurada nem Auth/JWT/RLS."
Write-Output "SEGURANCA: nenhuma senha divulgada, nenhuma consulta SQL, start, stop ou restore."
Write-Output "RESTAURACAO NAO EXECUTADA. SQL 002/003 e producao bloqueados."
