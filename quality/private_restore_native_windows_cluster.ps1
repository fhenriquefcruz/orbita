# ORBITA Aurora 3.36 | Gerenciamento de cluster PostgreSQL nativo ISOLADO.
# Nunca executa pg_restore, SQL, criacao de database, rede externa ou operacoes no servico 5432.
# -Check (padrao): leitura apenas. -Initialize/-Start/-Stop: requerem confirmacao explicita.
[CmdletBinding()]
param(
  [switch]$Check,
  [switch]$Initialize,
  [switch]$Start,
  [switch]$Stop,
  [string]$ConfirmLocalCluster = ""
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$port = 55432
$hostAddress = "127.0.0.1"
$confirmValue = "ORBITA-ISOLATED-55432"
$root = [IO.Path]::GetFullPath((Join-Path $HOME "orbita-restore-sandbox"))
$data = Join-Path $root "data"
$log = Join-Path $root "server.log"
$marker = Join-Path $root "orbita-local-only.marker"
$expectedMarker = "ORBITA_NATIVE_RESTORE_SANDBOX_V1"
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$enc = [Text.UTF8Encoding]::new($false)
$allowed = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value,"S-1-5-18","S-1-5-32-544")

function Fail([string]$message) { throw [InvalidOperationException]::new($message) }
function Get-Tool([string]$name) {
  $cmd = Get-Command ($name + ".exe") -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source) { return [string]$cmd.Source }
  $fallback = "C:\Program Files\PostgreSQL\17\bin\" + $name + ".exe"
  if (Test-Path -LiteralPath $fallback -PathType Leaf) { return $fallback }
  return $null
}
function Assert-NotLink([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return }
  $item = Get-Item -LiteralPath $path -Force
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Junction/symlink nao permitido no sandbox."
  }
}
function Assert-PrivateFolder([string]$path) {
  Assert-NotLink $path
  $acl = Get-Acl -LiteralPath $path
  if (-not $acl.AreAccessRulesProtected -and $path -eq $root) {
    Fail "Pasta raiz sem ACL protegida."
  }
  foreach ($entry in $acl.Access) {
    $sid = $entry.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowed -notcontains $sid) { Fail "ACL de terceiro no sandbox; abortando." }
  }
}
function Assert-Sandbox() {
  if (-not (Test-Path -LiteralPath $root -PathType Container)) {
    Fail "Sandbox ausente. Primeiro execute -Initialize com confirmacao."
  }
  Assert-PrivateFolder $root
  if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
    Fail "Identificador ORBITA ausente; nao operar neste diretorio."
  }
  Assert-NotLink $marker
  if (([IO.File]::ReadAllText($marker,$enc)).Trim() -ne $expectedMarker) {
    Fail "Identificador do sandbox nao corresponde."
  }
  if (-not (Test-Path -LiteralPath $data -PathType Container)) {
    Fail "Diretorio data do sandbox nao existe."
  }
  Assert-NotLink $data
  Assert-PrivateFolder $data
  $pgVersion = Join-Path $data "PG_VERSION"
  if (-not (Test-Path -LiteralPath $pgVersion -PathType Leaf) -or
      ([IO.File]::ReadAllText($pgVersion)).Trim() -ne "17") {
    Fail "Data directory nao e PostgreSQL 17."
  }
  $config = Join-Path $data "postgresql.conf"
  $hba = Join-Path $data "pg_hba.conf"
  if (-not (Test-Path -LiteralPath $config -PathType Leaf) -or
      -not (Test-Path -LiteralPath $hba -PathType Leaf)) {
    Fail "Configuracoes do cluster ausentes."
  }
  Assert-NotLink $config
  Assert-NotLink $hba
  $configText = [IO.File]::ReadAllText($config)
  $hbaText = [IO.File]::ReadAllText($hba)
  if ($configText -notmatch "(?m)^listen_addresses = '127\.0\.0\.1'\s*$" -or
      $configText -notmatch "(?m)^port = 55432\s*$" -or
      $configText -notmatch "(?m)^password_encryption = 'scram-sha-256'\s*$") {
    Fail "Configuracao de listener/porta/criptografia nao esta isolada."
  }
  if ($hbaText -notmatch '(?m)^host\s+all\s+all\s+127\.0\.0\.1/32\s+scram-sha-256\s*$' -or
      $hbaText -match '(?m)^\s*host\s+\S+\s+\S+\s+\S+\s+trust') {
    Fail "pg_hba.conf nao corresponde a autenticacao restrita."
  }
}
function Get-PortListeners() {
  try {
    return @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
  } catch {
    Fail "Nao foi possivel inspecionar a porta local 55432."
  }
}
function Assert-PortFree() {
  if (@(Get-PortListeners).Count -ne 0) {
    Fail "Porta 55432 ocupada; nao iniciar nem substituir outro processo."
  }
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Este script exige Windows."
}
$requested = @($Check,$Initialize,$Start,$Stop).Where({ $_ }).Count
if ($requested -gt 1) { Fail "Escolha apenas um modo: -Check, -Initialize, -Start ou -Stop." }
if ($root.Equals($repo,[StringComparison]::OrdinalIgnoreCase) -or
    $root.StartsWith($repo.TrimEnd('\') + '\',[StringComparison]::OrdinalIgnoreCase)) {
  Fail "A pasta do cluster nunca pode ficar dentro do Git."
}
Assert-NotLink $root
if ($Initialize -or $Start -or $Stop) {
  if ($ConfirmLocalCluster -cne $confirmValue) {
    Fail "Operacao local exige -ConfirmLocalCluster ORBITA-ISOLATED-55432."
  }
}

$initdb = Get-Tool "initdb"
$postgres = Get-Tool "postgres"
$pgctl = Get-Tool "pg_ctl"
if ($Check -or (-not $Initialize -and -not $Start -and -not $Stop)) {
  Write-Output "=== ORBITA 3.36 | CHECK LOCAL (SOMENTE LEITURA) ==="
  foreach ($required in @("initdb","postgres","pg_ctl")) {
    if (Get-Tool $required) { Write-Output ("BINARIO: " + $required + ".exe presente.") }
    else { Write-Output ("BINARIO: " + $required + ".exe ausente.") }
  }
  $listeners = @(Get-PortListeners)
  if ($listeners.Count -eq 0) {
    Write-Output "PORTA 55432: sem listener detectado."
  } else {
    foreach ($entry in $listeners) {
      Write-Output ("PORTA 55432: listener em " + $entry.LocalAddress + ".")
    }
  }
  if (Test-Path -LiteralPath $root -PathType Container) {
    try {
      Assert-Sandbox
      Write-Output "SANDBOX: existente e identidade/configuracao verificadas."
    } catch {
      Write-Output "SANDBOX: existente mas nao aprovado; nenhuma acao executada."
    }
  } else {
    Write-Output "SANDBOX: ainda nao inicializado."
  }
  Write-Output "SEGURANCA: nenhuma criacao de arquivos, execucao SQL, initdb, restore ou conexao externa."
  exit 0
}
if (-not $initdb -or -not $postgres -or -not $pgctl) {
  Fail "Binarios initdb/postgres/pg_ctl nao encontrados."
}
foreach ($tool in @($initdb,$postgres,$pgctl)) {
  $oldPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $versionLine = @(& $tool --version 2>$null) -join " "
    $result = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  if ($result -ne 0 -or $versionLine -notmatch '\b17\.\d+') {
    Fail "Exige binarios PostgreSQL de serie 17 em todas as operacoes."
  }
}

if ($Initialize) {
  if (Test-Path -LiteralPath $root) {
    Fail "Pasta sandbox ja existe. Nunca sobrescrever diretorio existente."
  }
  Assert-PortFree
  $userSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  New-Item -LiteralPath $root -ItemType Directory | Out-Null
  $ownerRule = "*" + $userSid + ":(OI)(CI)F"
  & icacls.exe $root /inheritance:r /grant:r $ownerRule "*S-1-5-18:(OI)(CI)F" "*S-1-5-32-544:(OI)(CI)F" 1>$null 2>$null
  if ($LASTEXITCODE -ne 0) { Fail "Nao foi possivel proteger a pasta do sandbox." }
  Assert-PrivateFolder $root
  Write-Output "PASTA PRIVADA: criada fora do Git, acesso restrito."
  Write-Output "INICIALIZACAO: o PostgreSQL pedira uma senha NOVA para orbita_restore_admin, duas vezes."
  Write-Output "ATENCAO: NAO reutilize a senha do Supabase de producao."
  # initdb le a senha diretamente no console, sem arquivo intermediario nem variavel de ambiente.
  & $initdb -D $data -U orbita_restore_admin --encoding=UTF8 --auth-host=scram-sha-256 --auth-local=scram-sha-256 --pwprompt --no-instructions
  if ($LASTEXITCODE -ne 0) { Fail "initdb nao concluiu. Sandbox parcial mantido para diagnostico; nao sobrescrever." }
  Assert-NotLink $data
  $config = Join-Path $data "postgresql.conf"
  $hba = Join-Path $data "pg_hba.conf"
  $overrides = @(
    "",
    "# ORBITA: cluster isolado 3.36",
    "listen_addresses = '127.0.0.1'",
    "port = 55432",
    "password_encryption = 'scram-sha-256'",
    "max_connections = 20",
    ""
  ) -join [Environment]::NewLine
  [IO.File]::AppendAllText($config,$overrides,$enc)
  $restrictedHba = @(
    "# ORBITA: somente IPv4 loopback e senha SCRAM",
    "host all all 127.0.0.1/32 scram-sha-256",
    "host all all 0.0.0.0/0 reject",
    "host all all ::/0 reject",
    ""
  ) -join [Environment]::NewLine
  [IO.File]::WriteAllText($hba,$restrictedHba,$enc)
  [IO.File]::WriteAllText($marker,$expectedMarker + [Environment]::NewLine,$enc)
  Assert-Sandbox
  Write-Output "INICIALIZADO: PostgreSQL 17 em pasta exclusiva, porta 55432 e acesso 127.0.0.1/SCRAM."
  Write-Output "NAO INICIADO: execute -Start separadamente apos verificar o resultado."
  Write-Output "NAO RESTAURADO: backup original permanece intocado."
  exit 0
}

Assert-Sandbox
if ($Start) {
  Assert-PortFree
  # O arquivo postgresql.conf do sandbox ja fixa a interface e a porta.
  Write-Output "INICIANDO: somente cluster ORBITA isolado, nao o servico postgresql-x64-17."
  $oldPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $pgctl -D $data -l $log -w -t 30 start 2>$null
    $result = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  if ($result -ne 0) { Fail "Cluster local nao iniciou; confira log PRIVADO sem publica-lo no chat." }
  $listeners = @(Get-PortListeners)
  if ($listeners.Count -lt 1 -or @($listeners | Where-Object { $_.LocalAddress -ne $hostAddress }).Count -ne 0) {
    Fail "Listener nao isolado como esperado. NAO restaurar dados; revise configuracao."
  }
  Write-Output "CLUSTER INICIADO: escutando exclusivamente 127.0.0.1:55432."
  Write-Output "RESTAURACAO NAO EXECUTADA: nenhuma tabela foi importada."
  exit 0
}
if ($Stop) {
  $oldPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $pgctl -D $data -m fast -w -t 30 stop 2>$null
    $result = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  if ($result -ne 0) { Fail "Nao foi possivel parar o cluster isolado; servidor principal nao foi alterado." }
  Write-Output "PARADO: somente cluster do sandbox ORBITA em 55432; dados preservados."
  exit 0
}
