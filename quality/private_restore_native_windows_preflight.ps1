# ORBITA Aurora 3.35 | Diagnostico para ensaio em PostgreSQL NATIVO no Windows.
# LEITURA APENAS: nao instala programas, nao cria banco, nao acessa producao.
param(
  [string]$ManifestPath = "",
  [switch]$ToolsOnly
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail([string]$reason) {
  throw [InvalidOperationException]::new($reason)
}
function Find-Tool([string]$name) {
  $command = Get-Command ($name + ".exe") -ErrorAction SilentlyContinue
  if ($command -and $command.Source) { return [string]$command.Source }
  $fallback = "C:\Program Files\PostgreSQL\17\bin\" + $name + ".exe"
  if (Test-Path -LiteralPath $fallback -PathType Leaf) { return $fallback }
  return $null
}
function Get-ToolMajor([string]$executable) {
  if (-not $executable) { return 0 }
  $oldPreference = $ErrorActionPreference
  $output = @()
  $exitCode = 1
  try {
    $ErrorActionPreference = "Continue"
    $output = @(& $executable --version 2>$null)
    $exitCode = $LASTEXITCODE
  } catch {
    return 0
  } finally {
    $ErrorActionPreference = $oldPreference
  }
  if ($exitCode -ne 0) { return 0 }
  $line = ($output -join " ").Trim()
  if ($line -match '\b(\d+)\.\d+') { return [int]$Matches[1] }
  return 0
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Diagnostico disponivel apenas no Windows."
}

Write-Output "=== ORBITA 3.35 | MODO NATIVO WINDOWS; SOMENTE LEITURA ==="
if ($ToolsOnly) {
  Write-Output "BACKUP: verificacao pulada explicitamente pelo modo -ToolsOnly (uso em CI)."
} else {
  if (-not $ManifestPath) {
    $backupDir = Join-Path $HOME "orbita-backups-privados"
    if (-not (Test-Path -LiteralPath $backupDir -PathType Container)) {
      Fail "Pasta privada de backup nao encontrada."
    }
    $newest = Get-ChildItem -LiteralPath $backupDir -Filter "*.manifest.json" -File |
      Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $newest) { Fail "Manifesto privado nao encontrado." }
    $ManifestPath = $newest.FullName
  }
  $verifier = Join-Path $PSScriptRoot "verify_database_backup_windows.ps1"
  if (-not (Test-Path -LiteralPath $verifier -PathType Leaf)) {
    Fail "Verificador privado indisponivel."
  }
  & powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File $verifier -ManifestPath ([IO.Path]::GetFullPath($ManifestPath))
  if ($LASTEXITCODE -ne 0) { Fail "Backup nao validado; ensaio bloqueado." }
  Write-Output "BACKUP: arquivo local validado; restauracao AINDA NAO TESTADA."
}

Write-Output "=== SOFTWARE POSTGRESQL NO WINDOWS ==="
$names = @("pg_restore","psql","pg_ctl","initdb","postgres")
$toolVersions = @{}
$resolved = @{}
foreach ($name in $names) {
  $path = Find-Tool $name
  $major = Get-ToolMajor $path
  $toolVersions[$name] = $major
  $resolved[$name] = $path
  if ($major -ge 17) {
    Write-Output ("{0}: DISPONIVEL (versao principal {1})." -f $name,$major)
  } elseif ($path) {
    Write-Output ("{0}: INCOMPATIVEL OU INDETERMINADO (exigir 17+)." -f $name)
  } else {
    Write-Output ("{0}: NAO ENCONTRADO." -f $name)
  }
}
$serverReady = $true
foreach ($required in @("pg_ctl","initdb","postgres")) {
  if ($toolVersions[$required] -lt 17) { $serverReady = $false }
}
$clientReady = $toolVersions["psql"] -ge 17 -and $toolVersions["pg_restore"] -ge 17

Write-Output "=== SERVICOS E PORTAS LOCAIS (INVENTARIO, NAO AUTORIZACAO) ==="
try {
  $services = @(Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue)
  if ($services.Count -eq 0) {
    Write-Output "SERVICO POSTGRESQL: NAO ENCONTRADO (instalacao portatil ainda e possivel)."
  } else {
    foreach ($service in $services) {
      Write-Output ("SERVICO POSTGRESQL: {0} - {1} (NAO reutilizar nem alterar sem verificar)." -f $service.Name,$service.Status)
    }
  }
} catch {
  Write-Output "SERVICO POSTGRESQL: CONSULTA INDISPONIVEL."
}
$listenOk = $false
try {
  $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 5432,55432 -ErrorAction SilentlyContinue)
  foreach ($listener in $listeners) {
    Write-Output ("PORTA OCUPADA: {0}:{1} (nao modificar)." -f $listener.LocalAddress,$listener.LocalPort)
  }
  if ($listeners.Count -eq 0) {
    Write-Output "PORTAS 5432/55432: SEM LISTENERS DETECTADOS (nao prova reserva de porta)."
  }
  $listenOk = $true
} catch {
  Write-Output "PORTAS: NAO FOI POSSIVEL INSPECIONAR LISTENERS."
}

Write-Output "=== RESULTADO DO PRE-FLIGHT ==="
if ($clientReady -and $serverReady) {
  Write-Output "POSTGRES NATIVO: BINARIOS 17+ PRESENTES. INSTANCIA ISOLADA AINDA NAO CRIADA."
} elseif ($clientReady) {
  Write-Output "POSTGRES NATIVO: CLIENTE 17+ PRONTO; SERVIDOR LOCAL NAO COMPROVADO."
} else {
  Write-Output "POSTGRES NATIVO: CLIENTE OU SERVIDOR INCOMPLETOS."
}
Write-Output "LIMITACAO: PostgreSQL comum nao reproduz automaticamente Supabase Auth, roles, extensoes e RLS."
Write-Output "SEGURANCA: nenhuma instalacao, escrita no banco, restore, criacao de servico ou conexao remota."
Write-Output "RELEASE: restauracao completa NAO COMPROVADA; SQL 002/003 e producao permanecem bloqueadas."
