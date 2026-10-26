# ORBITA 3.28 | Operacao MANUAL. Nunca salva senhas, nunca altera banco.
param(
  [switch]$CheckPrerequisites,
  [string]$ConfirmProject = "",
  [string]$BackupDirectory = (Join-Path $HOME "orbita-backups-privados")
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ref = "tbqfymedgdsdrgkqmuni"
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$destination = [IO.Path]::GetFullPath($BackupDirectory)
$allowed = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value,"S-1-5-18","S-1-5-32-544")

function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Find-Tool([string]$tool) {
  $cmd = Get-Command ($tool + ".exe") -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $fallback = "C:\Program Files\PostgreSQL\17\bin\" + $tool + ".exe"
  if (Test-Path -LiteralPath $fallback -PathType Leaf) { return $fallback }
  Fail ("Instale os utilitarios PostgreSQL 17: " + $tool)
}
function Assert-Private([string]$path) {
  $acl = Get-Acl -LiteralPath $path
  $item = Get-Item -LiteralPath $path -Force
  if ($item.PSIsContainer) {
    if (-not $acl.AreAccessRulesProtected) { Fail "ACL herdada na pasta de backup; abortando." }
  } else {
    # Arquivos podem herdar ACEs de uma pasta ja protegida.
    # Verifique primeiro a pasta e, depois, todos os ACEs efetivos do arquivo.
    $parent = Split-Path -Parent $path
    $parentAcl = Get-Acl -LiteralPath $parent
    if (-not $parentAcl.AreAccessRulesProtected) { Fail "Pasta do arquivo nao protegida." }
  }
  foreach ($entry in $acl.Access) {
    $sid = $entry.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowed -notcontains $sid) { Fail "ACL de terceiros presente no backup; abortando." }
  }
}
function Secure-Folder([string]$path) {
  if (-not (Test-Path -LiteralPath $path -PathType Container)) {
    New-Item -Path $path -ItemType Directory -Force | Out-Null
  }
  $item = Get-Item -LiteralPath $path -Force
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Pasta com junction/symlink nao permitida."
  }
  $userSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  $ownerAcl = "*" + $userSid + ":(OI)(CI)F"
  & icacls.exe $path /inheritance:r /grant:r $ownerAcl "*S-1-5-18:(OI)(CI)F" "*S-1-5-32-544:(OI)(CI)F" 1>$null 2>$null
  if ($LASTEXITCODE -ne 0) { Fail "Nao foi possivel proteger ACL da pasta." }
  Assert-Private $path
}
function Has-TableData([string]$toc,[string]$schema,[string]$name) {
  $p = '(?m)^\s*\d+;\s+\d+\s+\d+\s+TABLE DATA\s+' +
    [regex]::Escape($schema) + '\s+' + [regex]::Escape($name) + '(?:\s|$)'
  return [regex]::IsMatch($toc,$p)
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { Fail "Este script exige Windows." }
$pgDump = Find-Tool "pg_dump"
$pgRestore = Find-Tool "pg_restore"
$pgVersion = (& $pgDump --version) -join " "
$number = [regex]::Match($pgVersion,'(\d+)\.(\d+)')
if (-not $number.Success -or [int]$number.Groups[1].Value -lt 17) {
  Fail "O pg_dump precisa ser versao 17 ou superior."
}
if ($CheckPrerequisites) {
  Write-Output "PRONTO - ferramentas PostgreSQL disponiveis; nenhuma conexao executada."
  exit 0
}
if ($ConfirmProject -ne $ref) { Fail "Informe -ConfirmProject com o identificador ORBITA." }
if ($destination.Equals($repo,[StringComparison]::OrdinalIgnoreCase) -or
    $destination.StartsWith(($repo.TrimEnd('\') + '\'),[StringComparison]::OrdinalIgnoreCase)) {
  Fail "Nunca grave backup dentro da pasta Git."
}
$hostName = (Read-Host "Host do projeto ORBITA em Connect / Session pooler").Trim().ToLowerInvariant()
$dbUser = (Read-Host "Database user exibido em Connect").Trim()
$direct = $hostName -eq ("db."+$ref+".supabase.co") -and $dbUser -eq "postgres"
$pooler = $hostName -match '^[a-z0-9.-]+\.pooler\.supabase\.com$' -and $dbUser -eq ("postgres."+$ref)
if (-not ($direct -or $pooler)) { Fail "Host/usuario nao pertencem ao projeto ORBITA." }
# Antes de pedir uma senha, comprovar uma conexao TCP a porta escolhida.
try {
  $reachable = Test-NetConnection -ComputerName $hostName -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
} catch {
  Fail "Nao foi possivel testar a rede PostgreSQL. Confira DNS e firewall."
}
if (-not $reachable) {
  Fail "PORTA 5432 INACESSIVEL: confira Connect > Session pooler e Test-NetConnection. Tente uma rede autorizada diferente. Nenhuma senha foi utilizada."
}
$securePass = Read-Host "Senha do BANCO ORBITA (oculta)" -AsSecureString
if ($securePass.Length -eq 0) { Fail "Senha ausente." }
$partial = $null
try {
  Secure-Folder $destination
  $prefix = "orbita_" + $ref + "_" + [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ") + "_" + [Guid]::NewGuid().ToString("N").Substring(0,8)
  $partial = Join-Path $destination ($prefix + ".partial")
  $archive = Join-Path $destination ($prefix + ".dump")
  $manifest = Join-Path $destination ($prefix + ".manifest.json")
  foreach ($file in @($partial,$archive,$manifest)) {
    if (Test-Path -LiteralPath $file) { Fail "Arquivo de backup ja existe; abortando." }
  }
  $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePass)
  try {
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
  }
  $env:PGHOST = $hostName
  $env:PGUSER = $dbUser
  $env:PGPORT = "5432"
  $env:PGDATABASE = "postgres"
  $env:PGSSLMODE = "require"
  $env:PGCONNECT_TIMEOUT = "10"
  # Windows PowerShell 5.1 trata stderr nativo como erro terminante
  # quando a preferencia e Stop. Suprimir a mensagem so nesta chamada,
  # capturar o codigo de saida e devolver mensagem sem segredos.
  $preference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $pgDump --format=custom --no-password --file $partial 1>$null 2>$null
    $dumpExit = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $preference
  }
  if ($dumpExit -ne 0 -or -not (Test-Path -LiteralPath $partial -PathType Leaf)) {
    Fail "pg_dump nao concluiu. Confira conexao 5432, credencial do BANCO e acesso TLS. Nenhuma migracao executada."
  }
  if ((Get-Item -LiteralPath $partial).Length -lt 1024) {
    Fail "Arquivo de dump inesperadamente pequeno."
  }
  Assert-Private $partial
  $preference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $tocLines = @(& $pgRestore --list $partial 2>$null)
    $listExit = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $preference
  }
  if ($listExit -ne 0) { Fail "pg_restore nao conseguiu listar o dump." }
  $toc = $tocLines -join [Environment]::NewLine
  foreach ($tab in @(@("auth","users"),@("public","orbita_records"),@("public","orbita_chat_messages"),@("public","orbita_telegram_updates"))) {
    if (-not (Has-TableData $toc $tab[0] $tab[1])) {
      Fail "Backup incompleto: tabela obrigatoria nao encontrada."
    }
  }
  $digest = (Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant()
  $size = (Get-Item -LiteralPath $partial).Length
  Move-Item -LiteralPath $partial -Destination $archive
  $partial = $null
  $metadata = [ordered]@{
    project_ref = $ref
    created_utc = [DateTime]::UtcNow.ToString("o")
    archive_filename = [IO.Path]::GetFileName($archive)
    archive_bytes = $size
    sha256 = $digest
    toc_inspected = $true
    expected_tables_present = $true
    restore_tested = $false
    recoverable_confirmed = $false
  }
  [IO.File]::WriteAllText($manifest,(($metadata | ConvertTo-Json -Depth 3) + [Environment]::NewLine),[Text.UTF8Encoding]::new($false))
  Assert-Private $archive
  Assert-Private $manifest
  Write-Output "BACKUP CRIADO - arquivo privado, SHA256 e catalogo verificados."
  Write-Output "RESTAURACAO PENDENTE - sem autorizacao para SQL 002/003."
  Write-Output ("Manifesto privado: " + [IO.Path]::GetFileName($manifest))
} finally {
  if ($partial -and (Test-Path -LiteralPath $partial)) {
    Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue
  }
  $env:PGPASSWORD = $null
  $env:PGHOST = $null
  $env:PGUSER = $null
  $env:PGPORT = $null
  $env:PGDATABASE = $null
  $env:PGSSLMODE = $null
  $env:PGCONNECT_TIMEOUT = $null
  $securePass = $null
}
