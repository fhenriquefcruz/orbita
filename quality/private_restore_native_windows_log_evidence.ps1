# ORBITA Aurora 3.40 | Evidencias sanitizadas de server.log e destinos declarados.
# SOMENTE LEITURA. Nao executa SQL, pg_ctl, start/stop, pg_restore ou conexoes.
# Nunca imprime linhas, mensagens, caminhos ou timestamps brutos do log.
[CmdletBinding()]
param([switch]$SelfTest)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = [IO.Path]::GetFullPath((Join-Path $HOME "orbita-restore-sandbox"))
$data = Join-Path $root "data"
$marker = Join-Path $root "orbita-local-only.marker"
$log = Join-Path $root "server.log"
$config = Join-Path $data "postgresql.conf"
$expectedMarker = "ORBITA_NATIVE_RESTORE_SANDBOX_V1"
$allowed = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value,"S-1-5-18","S-1-5-32-544")

function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Get-SizeBand([long]$n) {
  if ($n -eq 0) { return "VAZIO" }
  if ($n -lt 4096) { return "ATE_4KB" }
  if ($n -lt 1048576) { return "4KB_A_1MB" }
  return "MAIS_DE_1MB"
}
function Get-LogCategory([string]$line) {
  # Categorias fechadas: nunca retornar parte da linha privada.
  if ($line -match '(?i)\bPANIC\s*:') { return "PANIC" }
  if ($line -match '(?i)\bFATAL\s*:') { return "FATAL" }
  if ($line -match '(?i)\bERROR\s*:') { return "ERROR" }
  if ($line -match '(?i)database system is ready to accept connections|sistema de banco de dados.{0,50}pront.{0,50}conex') { return "PRONTIDAO" }
  if ($line -match '(?i)received (fast|smart|immediate) shutdown request|solicita.{0,40}desligamento') { return "PEDIDO_DESLIGAMENTO" }
  if ($line -match '(?i)database system is shut down|sistema de banco de dados.{0,25}(?:desligad|encerrad)') { return "DESLIGAMENTO" }
  if ($line -match '(?i)\bLOG\s*:|\bWARNING\s*:|\bAVISO\s*:') { return "REGISTRO_GERAL" }
  return ""
}
function Assert-PrivateItem([string]$path,[bool]$protected) {
  if (-not (Test-Path -LiteralPath $path)) { Fail "Item obrigatorio do sandbox ausente." }
  $item = Get-Item -LiteralPath $path -Force
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Junction/symlink proibido no sandbox."
  }
  $acl = Get-Acl -LiteralPath $path
  if ($protected -and -not $acl.AreAccessRulesProtected) {
    Fail "Pasta privada sem ACL protegida."
  }
  foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowed -notcontains $sid) { Fail "ACL de terceiro detectada; diagnostico abortado." }
  }
}

if ($SelfTest) {
  if ((Get-SizeBand 0) -cne "VAZIO" -or (Get-SizeBand 4096) -cne "4KB_A_1MB" -or
      (Get-LogCategory "2026 LOG: database system is ready to accept connections") -cne "PRONTIDAO" -or
      (Get-LogCategory "2026 LOG: received fast shutdown request") -cne "PEDIDO_DESLIGAMENTO" -or
      (Get-LogCategory "2026 FATAL: segredo=user@example.test") -cne "FATAL" -or
      (Get-LogCategory "2026 LOG: usuario privado") -cne "REGISTRO_GERAL" -or
      (Get-LogCategory "user@example.test SQL privado") -cne "") {
    Fail "Autoteste de classificacao/privacidade falhou."
  }
  Write-Output "AUTOTESTE APROVADO: somente categorias fixas, nenhum arquivo real."
  exit 0
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Exige Windows para analisar o sandbox privado."
}
Write-Output "=== ORBITA 3.40 | EVIDENCIA DE LOG (SOMENTE LEITURA) ==="
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
  Fail "Sandbox ORBITA ausente; nenhuma acao realizada."
}
Assert-PrivateItem $root $true
Assert-PrivateItem $data $false
Assert-PrivateItem $marker $false
Assert-PrivateItem (Join-Path $data "PG_VERSION") $false
Assert-PrivateItem $config $false
if (([IO.File]::ReadAllText($marker)).Trim() -cne $expectedMarker -or
    ([IO.File]::ReadAllText((Join-Path $data "PG_VERSION"))).Trim() -ne "17") {
  Fail "Identidade ou versao do sandbox invalida."
}

try {
  $configText = [IO.File]::ReadAllText($config)
  $collectorMatches = [regex]::Matches($configText,'(?mi)^\s*logging_collector\s*=\s*(on|off)\b')
  $collector = if ($collectorMatches.Count -eq 0) { "NAO_DECLARADO" }
               elseif ($collectorMatches[$collectorMatches.Count - 1].Groups[1].Value -eq "on") { "ON_DECLARADO" }
               else { "OFF_DECLARADO" }
  $destMatches = [regex]::Matches($configText,"(?mi)^\s*log_destination\s*=\s*'([^']*)'")
  $destination = "NAO_DECLARADO"
  if ($destMatches.Count -gt 0) {
    $dest = $destMatches[$destMatches.Count - 1].Groups[1].Value
    if ($dest -match '(?i)eventlog') { $destination = "EVENTLOG_CITADO" }
    elseif ($dest -match '(?i)stderr') { $destination = "STDERR_CITADO" }
    else { $destination = "OUTRO_DECLARADO" }
  }
  Write-Output ("CONFIG: logging_collector=" + $collector + "; log_destination=" + $destination)
  Write-Output "CONFIG: valores declarados no arquivo, NAO comprovacao da configuracao efetiva."
} catch {
  Fail "Nao foi possivel classificar a configuracao local privada."
}

$current = Join-Path $data "current_logfiles"
if (Test-Path -LiteralPath $current) {
  Assert-PrivateItem $current $false
  Write-Output "CURRENT_LOGFILES: PRESENTE (conteudo e caminhos nao lidos)."
} else {
  Write-Output "CURRENT_LOGFILES: AUSENTE."
}
$postmasterPidFile = Join-Path $data "postmaster.pid"
if (Test-Path -LiteralPath $postmasterPidFile) {
  Assert-PrivateItem $postmasterPidFile $false
  Write-Output "POSTMASTER_PID: ARQUIVO_PRESENTE (nao comprova processo ativo)."
} else {
  Write-Output "POSTMASTER_PID: ARQUIVO_AUSENTE."
}

if (-not (Test-Path -LiteralPath $log -PathType Leaf)) {
  Write-Output "SERVER_LOG: AUSENTE."
} else {
  Assert-PrivateItem $log $false
  try {
    $file = Get-Item -LiteralPath $log -Force
    Write-Output ("SERVER_LOG: PRESENTE; TAMANHO=" + (Get-SizeBand $file.Length))
    $age = ([DateTime]::Now - $file.LastWriteTime).TotalHours
    $ageBand = if ($age -lt 0) { "INCONSISTENTE" }
               elseif ($age -le 1) { "ATE_1H" }
               elseif ($age -le 24) { "ATE_24H" }
               else { "MAIS_DE_24H" }
    Write-Output ("ULTIMA_ATUALIZACAO: " + $ageBand)
    if ($file.Length -gt 0) {
      $lines = @(Get-Content -LiteralPath $log -Tail 300 -ErrorAction Stop)
      $nonempty = @($lines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
      $categories = @(foreach ($line in $lines) {
        $category = Get-LogCategory ([string]$line)
        if ($category) { $category }
      })
      Write-Output ("LINHAS_INSPECIONADAS: " + $lines.Count)
      Write-Output ("LINHAS_NAO_VAZIAS: " + $nonempty)
      Write-Output ("EVENTOS_CLASSIFICADOS: " + $categories.Count)
      if ($categories.Count -gt 0) {
        foreach ($name in @($categories | Sort-Object -Unique)) {
          Write-Output ("CATEGORIA: " + $name)
        }
      } elseif ($nonempty -gt 0) {
        Write-Output "HIPOTESE: texto presente sem padroes reconhecidos; verificar idioma ou destino de log localmente."
      }
    }
  } catch {
    Fail "Falha ao ler log privado; nenhum conteudo sera mostrado."
  }
}
Write-Output "GATE: diagnostico inconclusivo ate esclarecer origem e persistencia do processo."
Write-Output "SEGURANCA: nenhuma escrita, start/stop, SQL, rede ou conteudo privado divulgado."
Write-Output "RESTAURACAO NAO EXECUTADA; migracoes 002/003 e producao bloqueadas."
