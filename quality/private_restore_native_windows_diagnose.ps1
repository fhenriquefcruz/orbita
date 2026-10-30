# ORBITA Aurora 3.38 | Diagnostico PRIVADO do cluster Windows 127.0.0.1:55432.
# Somente leitura: sem start, stop, SQL, login, rede externa ou pg_restore.
# Nunca exibe linhas completas de server.log; apenas categorias predefinidas.
[CmdletBinding()]
param([switch]$SelfTest)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = [IO.Path]::GetFullPath((Join-Path $HOME "orbita-restore-sandbox"))
$data = Join-Path $root "data"
$log = Join-Path $root "server.log"
$marker = Join-Path $root "orbita-local-only.marker"
$port = 55432
$expectedMarker = "ORBITA_NATIVE_RESTORE_SANDBOX_V1"
$allowed = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value,"S-1-5-18","S-1-5-32-544")
function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Get-EventCategory([string]$line) {
  # Matching somente por frases, sem divulgar timestamp, SQL, usuario ou nomes.
  if ($line -match 'database system is ready to accept connections') { return "PRONTO_PARA_CONEXOES" }
  if ($line -match 'database system is shut down') { return "BANCO_ENCERRADO" }
  if ($line -match 'received (fast|smart|immediate) shutdown request') { return "SOLICITACAO_DE_DESLIGAMENTO" }
  if ($line -match '(?i)background worker.*terminated by exception') { return "PROCESSO_ENCERRADO_POR_EXCECAO" }
  if ($line -match '(?i)database system was not properly shut down') { return "RECUPERACAO_APOS_QUEDA" }
  if ($line -match '(?i)\bPANIC\b') { return "PANIC_NO_LOG" }
  if ($line -match '(?i)\bFATAL\b') { return "FATAL_NO_LOG" }
  if ($line -match '(?i)could not bind (IPv4|IPv6|TCP)') { return "FALHA_AO_ABRIR_PORTA" }
  if ($line -match '(?i)permission denied|access is denied') { return "ACESSO_NEGADO" }
  if ($line -match '(?i)invalid configuration|configuration file contains errors') { return "CONFIGURACAO_INVALIDA" }
  return ""
}
function Assert-Private([string]$path,[bool]$protected) {
  if (-not (Test-Path -LiteralPath $path)) { Fail "Item de sandbox obrigatorio ausente." }
  $item = Get-Item -LiteralPath $path -Force
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Junction/symlink nao permitido no sandbox."
  }
  $acl = Get-Acl -LiteralPath $path
  if ($protected -and -not $acl.AreAccessRulesProtected) {
    Fail "Permissoes da pasta privada sem protecao."
  }
  foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowed -notcontains $sid) { Fail "ACL de terceiros detectada." }
  }
}

if ($SelfTest) {
  if ((Get-EventCategory "2026 LOG: database system is ready to accept connections") -cne "PRONTO_PARA_CONEXOES" -or
      (Get-EventCategory "2026 LOG: received fast shutdown request") -cne "SOLICITACAO_DE_DESLIGAMENTO" -or
      (Get-EventCategory "2026 LOG: database system is shut down") -cne "BANCO_ENCERRADO" -or
      (Get-EventCategory "LOG: user@email.example query private") -cne "" -or
      (Get-EventCategory "2026 FATAL: could not read config") -cne "FATAL_NO_LOG") {
    Fail "Autoteste de categorizacao falhou."
  }
  Write-Output "AUTOTESTE APROVADO: logs sinteticos classificados sem revelar conteudo."
  exit 0
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Diagnostico requer Windows."
}
Write-Output "=== ORBITA 3.38 | CLUSTER PARADO APOS START ==="
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
  Write-Output "CLUSTER: AUSENTE. Nada alterado."
  exit 0
}
Assert-Private $root $true
Assert-Private $data $false
Assert-Private $marker $false
if (([IO.File]::ReadAllText($marker)).Trim() -cne $expectedMarker) {
  Fail "Identidade do sandbox ORBITA nao corresponde."
}
$version = Join-Path $data "PG_VERSION"
Assert-Private $version $false
if (([IO.File]::ReadAllText($version)).Trim() -ne "17") {
  Fail "Cluster nao e PostgreSQL 17."
}

$pgctlPath = "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe"
if (-not (Test-Path -LiteralPath $pgctlPath -PathType Leaf)) {
  $cmd = Get-Command pg_ctl.exe -ErrorAction SilentlyContinue
  if (-not $cmd -or -not $cmd.Source) { Fail "pg_ctl.exe 17 nao encontrado." }
  $pgctlPath = [string]$cmd.Source
}
$oldPreference = $ErrorActionPreference
$statusExit = -1
try {
  $ErrorActionPreference = "Continue"
  $null = @(& $pgctlPath -D $data status 2>$null)
  $statusExit = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $oldPreference
}
switch ($statusExit) {
  0 { Write-Output "PG_CTL: servidor declara estar ATIVO." }
  3 { Write-Output "PG_CTL: servidor declara estar PARADO." }
  default { Write-Output "PG_CTL: status INCONCLUSIVO (nao prosseguir com restore)." }
}
try {
  $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
} catch {
  Write-Output "PORTA 55432: nao foi possivel consultar listener."
  $listeners = @()
}
if ($listeners.Count -eq 0) {
  Write-Output "PORTA 55432: SEM LISTENER."
} elseif ($listeners.Count -eq 1 -and $listeners[0].LocalAddress -eq "127.0.0.1") {
  Write-Output "PORTA 55432: listener SOMENTE em 127.0.0.1 (identidade precisa ser confirmada no verificador 3.37)."
} else {
  Write-Output "PORTA 55432: OCUPACAO OU EXPOSICAO INESPERADA. RESTAURACAO PROIBIDA."
}

if (-not (Test-Path -LiteralPath $log -PathType Leaf)) {
  Write-Output "LOG PRIVADO: ausente. Consultar falha de log localmente, sem compartilhar arquivos."
} else {
  Assert-Private $log $false
  # Acesso local a ate 300 linhas recentes; nenhuma linha original sai do script.
  $recentLines = @(Get-Content -LiteralPath $log -Tail 300 -ErrorAction Stop)
  $events = @(
    foreach ($line in $recentLines) {
      $category = Get-EventCategory ([string]$line)
      if ($category) { $category }
    }
  )
  Write-Output ("EVENTOS RECONHECIDOS NO LOG: " + $events.Count)
  if ($events.Count -gt 0) {
    $lastEvents = @($events | Select-Object -Last 8)
    foreach ($category in $lastEvents) { Write-Output ("EVENTO: " + $category) }
    $latest = $events[$events.Count - 1]
    if ($statusExit -eq 3 -and $latest -eq "BANCO_ENCERRADO") {
      Write-Output "HIPOTESE: houve desligamento registrado; apurar sua causa antes de reiniciar."
    } elseif ($statusExit -eq 3 -and $latest -eq "PRONTO_PARA_CONEXOES") {
      Write-Output "HIPOTESE: processo parou apos declarar pronto sem evento final capturado neste trecho."
    } elseif ($statusExit -eq 3 -and $latest -match 'FATAL|PANIC|CONFIGURACAO_INVALIDA|ACESSO_NEGADO') {
      Write-Output "HIPOTESE: falha operacional registrada; revisar log privado localmente."
    }
  } else {
    Write-Output "EVENTOS: nenhum padrao de inicializacao/encerramento nos ultimos registros."
  }
}
Write-Output "PROXIMO GATE: comparar causas sem repetir -Start ou alterar o cluster."
Write-Output "SEGURANCA: somente leitura; log bruto nao exibido; nenhuma senha, SQL ou conexao."
Write-Output "RESTAURACAO NAO TESTADA; novas SQL 002/003 e producao continuam bloqueadas."
