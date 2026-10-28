# ORBITA Aurora 3.37 | Verifica identidade e isolamento do cluster LOCAL.
# Somente leitura: nao executa SQL, nao pede senha, nao altera arquivos nem servicos.
[CmdletBinding()]
param([switch]$SelfTest)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$port = 55432
$loopback = "127.0.0.1"
$root = [IO.Path]::GetFullPath((Join-Path $HOME "orbita-restore-sandbox"))
$data = Join-Path $root "data"
$marker = Join-Path $root "orbita-local-only.marker"
$expectedMarker = "ORBITA_NATIVE_RESTORE_SANDBOX_V1"
$allowed = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value,"S-1-5-18","S-1-5-32-544")
function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Assert-NotLink([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { Fail "Arquivo ou pasta esperado ausente." }
  if (((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Junction/symlink nao permitido."
  }
}
function Assert-Private([string]$path,[bool]$requireProtected) {
  Assert-NotLink $path
  $acl = Get-Acl -LiteralPath $path
  if ($requireProtected -and -not $acl.AreAccessRulesProtected) {
    Fail "ACL privada nao protegida."
  }
  foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowed -notcontains $sid) { Fail "ACL de terceiros detectada." }
  }
}
function Get-ActiveSetting([string]$text,[string]$key) {
  $pattern = '(?m)^\s*' + [regex]::Escape($key) + '\s*=\s*([^\r\n#]+)'
  $matches = [regex]::Matches($text,$pattern)
  if ($matches.Count -lt 1) { return "" }
  return $matches[$matches.Count-1].Groups[1].Value.Trim().Trim("'").Trim('"')
}
function Assert-Configuration([string]$conf,[string]$hba) {
  if ($conf -match '(?m)^\s*include(?:_dir|_if_exists)?\s*=') {
    Fail "Configuracao inclui arquivos externos nao auditados."
  }
  if ((Get-ActiveSetting $conf "port") -ne "55432" -or
      (Get-ActiveSetting $conf "listen_addresses") -ne "127.0.0.1" -or
      (Get-ActiveSetting $conf "password_encryption") -ne "scram-sha-256") {
    Fail "Configuracao de rede/porta/SCRAM nao esta isolada."
  }
  $active = @($hba -split '\r?\n' | Where-Object { $_.Trim() -and $_.Trim() -notmatch '^#' } | ForEach-Object { ($_.Trim() -replace '\s+',' ') })
  $expected = @(
    "host all all 127.0.0.1/32 scram-sha-256",
    "host all all 0.0.0.0/0 reject",
    "host all all ::/0 reject"
  )
  if ($active.Count -ne $expected.Count) { Fail "pg_hba.conf possui regras inesperadas." }
  foreach ($line in $expected) {
    if ($active -cnotcontains $line) { Fail "pg_hba.conf diverge da lista restrita." }
  }
}
if ($SelfTest) {
  $sample = @"
# comment
port = 55432
listen_addresses = '127.0.0.1'
password_encryption = 'scram-sha-256'
"@
  $hbaSample = @"
host all all 127.0.0.1/32 scram-sha-256
host all all 0.0.0.0/0 reject
host all all ::/0 reject
"@
  Assert-Configuration $sample $hbaSample
  $rejected = $false
  try {
    Assert-Configuration ($sample + "include_dir = 'conf.d'") $hbaSample
  } catch { $rejected = $true }
  if (-not $rejected) { Fail "Autoteste nao rejeitou inclusao externa." }
  $rejected = $false
  try {
    Assert-Configuration $sample ($hbaSample + "host all all 0.0.0.0/0 trust")
  } catch { $rejected = $true }
  if (-not $rejected) { Fail "Autoteste nao rejeitou regra HBA insegura." }
  Write-Output "AUTOTESTE APROVADO: isolamento de configuracao em memoria, sem tocar no sistema."
  exit 0
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Verificador exige Windows."
}
Write-Output "=== ORBITA 3.37 | IDENTIDADE DO CLUSTER ISOLADO ==="
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
  Write-Output "CLUSTER AUSENTE: primeiro executar -Check da Aurora 3.36."
  Write-Output "RESTAURACAO: NAO AUTORIZADA (cluster nao encontrado)."
  Write-Output "SEGURANCA: somente leitura, nenhuma conexao ou SQL."
  exit 0
}
Assert-Private $root $true
Assert-Private $data $false
Assert-Private $marker $false
if (([IO.File]::ReadAllText($marker)).Trim() -cne $expectedMarker) {
  Fail "Identificador de sandbox nao corresponde ao ORBITA."
}
$versionFile = Join-Path $data "PG_VERSION"
Assert-NotLink $versionFile
if (([IO.File]::ReadAllText($versionFile)).Trim() -ne "17") { Fail "Versao nao corresponde a PostgreSQL 17." }
$conf = Join-Path $data "postgresql.conf"
$hba = Join-Path $data "pg_hba.conf"
Assert-Private $conf $false
Assert-Private $hba $false
Assert-Configuration ([IO.File]::ReadAllText($conf)) ([IO.File]::ReadAllText($hba))
$autoConf = Join-Path $data "postgresql.auto.conf"
if (Test-Path -LiteralPath $autoConf -PathType Leaf) {
  Assert-Private $autoConf $false
  $override = [IO.File]::ReadAllText($autoConf)
  if ($override -match '(?m)^\s*(listen_addresses|port|password_encryption|hba_file|config_file)\s*=') {
    Fail "Configuracao automatica pode substituir as protecoes do sandbox."
  }
}
Write-Output "IDENTIDADE: marcador ORBITA, versao 17, ACL e configuracao de rede aprovados."

$pgctl = Get-Command pg_ctl.exe -ErrorAction SilentlyContinue
$pgctlBin = if ($pgctl -and $pgctl.Source) {
  [string]$pgctl.Source
} else {
  "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe"
}
if (-not (Test-Path -LiteralPath $pgctlBin -PathType Leaf)) { Fail "pg_ctl.exe indisponivel." }
$oldPreference = $ErrorActionPreference
try {
  $ErrorActionPreference = "Continue"
  $statusOutput = @(& $pgctlBin -D $data status 2>$null)
  $statusCode = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $oldPreference
}
try {
  $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
} catch {
  Fail "Nao foi possivel validar a porta do cluster."
}
if ($statusCode -eq 3) {
  if ($listeners.Count -ne 0) { Fail "Porta 55432 ocupada por outro processo; restauracao proibida." }
  Write-Output "CLUSTER PARADO: instância isolada existe; executar -Start da Aurora 3.36 se desejado."
  Write-Output "RESTAURACAO: NAO EXECUTADA."
  Write-Output "SEGURANCA: somente leitura, nenhum SQL ou autenticação."
  exit 0
}
if ($statusCode -ne 0) { Fail "pg_ctl status inconclusivo; nao prosseguir." }
$pidFile = Join-Path $data "postmaster.pid"
Assert-NotLink $pidFile
$pidLine = Get-Content -LiteralPath $pidFile -TotalCount 1 -Encoding ASCII
$serverPid = 0
if (-not [int]::TryParse(($pidLine -join "").Trim(),[ref]$serverPid) -or $serverPid -le 0) {
  Fail "PID do postmaster invalido."
}
if ($listeners.Count -ne 1) {
  Fail "Numero inesperado de listeners na porta 55432."
}
$listener = $listeners[0]
if ($listener.LocalAddress -ne $loopback -or [int]$listener.OwningProcess -ne $serverPid) {
  Fail "Listener nao pertence ao postmaster do sandbox em 127.0.0.1; NAO restaurar."
}
Write-Output "CLUSTER ATIVO: PID do postmaster confere e listener exclusivo 127.0.0.1:55432."
Write-Output "RESTAURACAO: NAO EXECUTADA. Auth/RLS Supabase ainda nao demonstrados."
Write-Output "SEGURANCA: somente leitura, nenhuma senha, SQL ou conexao externa."
