# ORBITA 3.28 - inspecciona backup local; NAO conecta ao banco.
param([Parameter(Mandatory=$true)][string]$ManifestPath)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$project = "tbqfymedgdsdrgkqmuni"
$allowed = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value,"S-1-5-18","S-1-5-32-544")
function Fail([string]$message) { throw [InvalidOperationException]::new($message) }
function Assert-Private([string]$path) {
  $parent = Split-Path -Parent $path
  $pAcl = Get-Acl -LiteralPath $parent
  if (-not $pAcl.AreAccessRulesProtected) { Fail "Pasta de backup sem protecao NTFS." }
  $acl = Get-Acl -LiteralPath $path
  foreach ($entry in $acl.Access) {
    $sid = $entry.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowed -notcontains $sid) { Fail "ACL de terceiros encontrada no backup." }
  }
}
function Has-TableData([string]$toc,[string]$schema,[string]$name) {
  $p = '(?m)^\s*\d+;\s+\d+\s+\d+\s+TABLE DATA\s+' +
       [regex]::Escape($schema) + '\s+' + [regex]::Escape($name) + '(?:\s|$)'
  return [regex]::IsMatch($toc,$p)
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { Fail "Este script exige Windows." }
$manifest = [IO.Path]::GetFullPath($ManifestPath)
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { Fail "Manifesto nao encontrado." }
Assert-Private $manifest
try { $data = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json }
catch { Fail "Manifesto JSON invalido." }
if ($data.project_ref -ne $project) { Fail "Manifesto de outro projeto." }
$name = [string]$data.archive_filename
$pattern = '^orbita_' + $project + '_\d{8}T\d{6}Z_[0-9a-f]{8}\.dump$'
if (-not [regex]::IsMatch($name,$pattern)) { Fail "Nome de arquivo invalido." }
$directory = Split-Path -Parent $manifest
$archive = Join-Path $directory $name
if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) { Fail "Backup ausente." }
$file = Get-Item -LiteralPath $archive -Force
if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { Fail "Backup nao pode ser link." }
Assert-Private $archive
if ([int64]$data.archive_bytes -ne $file.Length -or $file.Length -lt 1024) {
  Fail "Tamanho do backup divergente."
}
$hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
if ($hash -ine [string]$data.sha256) { Fail "Checksum SHA256 divergente." }
$command = Get-Command pg_restore.exe -ErrorAction SilentlyContinue
$pgRestore = if ($command) { $command.Source } else { "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" }
if (-not (Test-Path -LiteralPath $pgRestore -PathType Leaf)) { Fail "pg_restore 17+ nao encontrado." }
$lines = @(& $pgRestore --list $archive 2>$null)
if ($LASTEXITCODE -ne 0) { Fail "pg_restore nao reconheceu o dump." }
$toc = $lines -join [Environment]::NewLine
foreach ($table in @(@("auth","users"),@("public","orbita_records"),@("public","orbita_chat_messages"),@("public","orbita_telegram_updates"))) {
  if (-not (Has-TableData $toc $table[0] $table[1])) { Fail "Tabela obrigatoria ausente do dump." }
}
Write-Output "APROVADO - integridade, hash SHA256, ACLs e catalogo conferidos."
Write-Output "RESTAURACAO NAO TESTADA - SQL 002/003 continuam bloqueadas."
