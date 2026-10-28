# ORBITA Aurora 3.33 - PRE-FLIGHT LOCAL: SOMENTE LEITURA
# Nao executa SQL, Docker create/run, pg_restore de dados, nem altera o Supabase.
param(
  [string]$ManifestPath = ""
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail([string]$message) {
  throw [InvalidOperationException]::new($message)
}
function Find-Exe([string]$name) {
  $cmd = Get-Command ($name + ".exe") -ErrorAction SilentlyContinue
  if ($cmd) { return [string]$cmd.Source }
  $fallback = "C:\Program Files\PostgreSQL\17\bin\" + $name + ".exe"
  if (Test-Path -LiteralPath $fallback -PathType Leaf) { return $fallback }
  return $null
}
function Read-Version([string]$tool) {
  $oldPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $value = @(& $tool --version 2>$null)
    $exit = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  if ($exit -ne 0) { return $null }
  return ($value -join " ").Trim()
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Este diagnostico exige Windows."
}
if (-not $ManifestPath) {
  $backupDir = Join-Path $HOME "orbita-backups-privados"
  if (-not (Test-Path -LiteralPath $backupDir -PathType Container)) {
    Fail "Pasta privada de backup nao encontrada."
  }
  $newest = Get-ChildItem -LiteralPath $backupDir -Filter "*.manifest.json" -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $newest) { Fail "Nenhum manifesto privado encontrado." }
  $ManifestPath = $newest.FullName
}
$manifest = [IO.Path]::GetFullPath($ManifestPath)
$verification = Join-Path $PSScriptRoot "verify_database_backup_windows.ps1"
if (-not (Test-Path -LiteralPath $verification -PathType Leaf)) {
  Fail "Verificador ORBITA indisponivel; atualize a homologacao."
}
Write-Output "=== AURORA 3.33 | BACKUP LOCAL ==="
& powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File $verification -ManifestPath $manifest
if ($LASTEXITCODE -ne 0) { Fail "Backup nao validado. Restauracao proibida." }

Write-Output "=== FERRAMENTAS DO ENSAIO ISOLADO ==="
$restoreExe = Find-Exe "pg_restore"
$psqlExe = Find-Exe "psql"
$pgReady = $false
if ($restoreExe -and $psqlExe) {
  $restoreVersion = Read-Version $restoreExe
  $psqlVersion = Read-Version $psqlExe
  $restoreMajor = if ($restoreVersion -match '^(?:pg_restore \(PostgreSQL\) )?(\d+)\.') {
    [int]$Matches[1]
  } else { 0 }
  $psqlMajor = if ($psqlVersion -match '^(?:psql \(PostgreSQL\) )?(\d+)\.') {
    [int]$Matches[1]
  } else { 0 }
  $pgReady = $restoreMajor -ge 17 -and $psqlMajor -ge 17
  if ($pgReady) { Write-Output "PostgreSQL CLI: OK (pg_restore/psql 17+)." }
  else { Write-Output "PostgreSQL CLI: INCOMPATIVEL ou nao detectado; exigir 17+." }
} else {
  Write-Output "PostgreSQL CLI: FALTA pg_restore ou psql 17+."
}

$dockerReady = $false
$docker = Get-Command docker.exe -ErrorAction SilentlyContinue
if ($docker) {
  $oldPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $serverVersion = @(& $docker.Source info --format '{{.ServerVersion}}' 2>$null)
    $dockerExit = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  $dockerReady = ($dockerExit -eq 0) -and -not [string]::IsNullOrWhiteSpace(($serverVersion -join ""))
  if ($dockerReady) { Write-Output "Docker Engine: DISPONIVEL (sem criar containers)." }
  else { Write-Output "Docker Engine: instalado, mas daemon indisponivel." }
} else {
  Write-Output "Docker Engine: NAO INSTALADO/NAO ENCONTRADO."
}
$supabase = Get-Command supabase -ErrorAction SilentlyContinue
$supabaseReady = $false
if ($supabase) {
  $oldPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $sbVersion = @(& supabase --version 2>$null)
    $sbExit = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  $supabaseReady = ($sbExit -eq 0) -and -not [string]::IsNullOrWhiteSpace(($sbVersion -join ""))
}
# Windows pode ter a CLI apenas via npx.cmd (sem Scoop nem npm global).
# Verificar exclusivamente o cache: --offline proibe downloads de pacotes.
# O comando --version nao solicita login nem conecta a qualquer projeto remoto.
$cliSource = if ($supabaseReady) { "comando supabase" } else { "" }
$npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
if (-not $supabaseReady -and $npx) {
  $oldPreference = $ErrorActionPreference
  $npxExit = 1
  $npxVersion = @()
  try {
    $ErrorActionPreference = "Continue"
    $npxVersion = @(& $npx.Source --offline --yes supabase --version 2>$null)
    $npxExit = $LASTEXITCODE
  } catch {
    $npxExit = 1
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  $versionLine = ($npxVersion -join " ").Trim()
  if ($npxExit -eq 0 -and $versionLine -match '^\d+\.\d+\.\d+$') {
    $supabaseReady = $true
    $cliSource = "cache local npx.cmd"
  }
}
if ($supabaseReady) {
  Write-Output ("Supabase CLI: DISPONIVEL via " + $cliSource + ".")
} elseif ($npx) {
  Write-Output "Supabase CLI: npx.cmd detectado, mas pacote offline nao disponivel. Para verificar separadamente: npx.cmd --yes supabase --version."
} else {
  Write-Output "Supabase CLI: NAO DETECTADO; npx.cmd ausente."
}

Write-Output "=== RESULTADO ==="
if ($pgReady -and $dockerReady -and $supabaseReady) {
  Write-Output "PRE-REQUISITOS LOCAIS PRESENTES - ensaio de restauracao AINDA NAO EXECUTADO."
} else {
  Write-Output "PRE-REQUISITOS INCOMPLETOS - planejar ambiente de teste antes de restaurar."
}
Write-Output "SEGURANCA: este script nao abriu o dump para restaurar, nao executou SQL, nao criou containers e nao conectou a producao."
Write-Output "BLOQUEIO: migracoes novas 002/003 e release continuam pendentes de recuperacao comprovada."
