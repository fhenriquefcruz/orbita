# ORBITA Aurora 3.42 | Evidencias sanitizadas de server.log e destinos declarados.
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
  # Detecta a forma curta real do PostgreSQL 17: "LOG: shutting down".
  if ($line -match '(?i)database system is shutting down|\bLOG\s*:\s*shutting down\b') { return "ENCERRANDO" }
  # Códigos/expressões fixos; nao retornamos o conteudo da linha.
  if ($line -match '(?i)background worker.*terminated by exception\s+0xC000013A') { return "EXCECAO_CONSOLE" }
  if ($line -match '(?i)background worker.*terminated by exception') { return "EXCECAO_PROCESSO" }
  if ($line -match '(?i)terminating any other active server processes') { return "PROCESSOS_ENCERRADOS" }
  if ($line -match '(?i)all server processes terminated; reinitializing') { return "PROCESSOS_REINICIANDO" }
  if ($line -match '(?i)database system was not properly shut down|database system was interrupted') { return "RECUPERACAO_APOS_QUEDA" }
  if ($line -match '(?i)checkpoint starting: shutdown') { return "CHECKPOINT_DESLIGAMENTO" }
  if ($line -match '(?i)database system is shut down|sistema de banco de dados.{0,25}(?:desligad|encerrad)') { return "DESLIGAMENTO" }
  if ($line -match '(?i)\bLOG\s*:|\bWARNING\s*:|\bAVISO\s*:') { return "REGISTRO_GERAL" }
  return ""
}
# Retorna APENAS posicao relativa e categoria em enumeracao fechada.
# Nenhum trecho do arquivo privado e retornado.
function Get-Milestones([string[]]$sourceLines) {
  $relevant = @("PRONTIDAO","PEDIDO_DESLIGAMENTO","ENCERRANDO","CHECKPOINT_DESLIGAMENTO","DESLIGAMENTO","PANIC","FATAL","ERROR","EXCECAO_CONSOLE","EXCECAO_PROCESSO","PROCESSOS_ENCERRADOS","PROCESSOS_REINICIANDO","RECUPERACAO_APOS_QUEDA")
  for ($lineIndex = 0; $lineIndex -lt $sourceLines.Count; $lineIndex++) {
    $kind = Get-LogCategory ([string]$sourceLines[$lineIndex])
    if ($relevant -contains $kind) {
      [pscustomobject]@{ Position = ($lineIndex + 1); Kind = $kind }
    }
  }
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
      (Get-LogCategory "user@example.test SQL privado") -cne "" -or
      (Get-LogCategory "LOG: database system is shutting down") -cne "ENCERRANDO" -or
      (Get-LogCategory "LOG: checkpoint starting: shutdown immediate") -cne "CHECKPOINT_DESLIGAMENTO" -or
      (Get-LogCategory "LOG: shutting down") -cne "ENCERRANDO" -or
      (Get-LogCategory "LOG: background worker logical replication launcher (PID 999) was terminated by exception 0xC000013A") -cne "EXCECAO_CONSOLE" -or
      (Get-LogCategory "LOG: database system was not properly shut down; automatic recovery in progress") -cne "RECUPERACAO_APOS_QUEDA") {
    Fail "Autoteste de classificacao/privacidade falhou."
  }
  $synthetic = @(
    "2026 LOG: database system is ready to accept connections",
    "2026 LOG: received fast shutdown request",
    "2026 LOG: shutting down",
    "2026 LOG: checkpoint starting: shutdown immediate",
    "2026 LOG: database system is shut down",
    "usuario@example.test documento privado"
  )
  $marks = @(Get-Milestones $synthetic)
  if ($marks.Count -ne 5 -or $marks[0].Position -ne 1 -or
      $marks[1].Kind -cne "PEDIDO_DESLIGAMENTO" -or
      $marks[4].Position -ne 5 -or $marks[4].Kind -cne "DESLIGAMENTO" -or
      @($marks | Where-Object { $_.Kind -match '@|usuario|documento' }).Count -ne 0) {
    Fail "Autoteste de ordem de marcos, exclusao de dados e privacidade falhou."
  }
  # Não há hipótese de pedido apenas pelo texto "shutdown immediate" do checkpoint.
  $cleanSequence = @(
    "LOG: database system is ready to accept connections",
    "LOG: shutting down",
    "LOG: checkpoint starting: shutdown immediate",
    "LOG: database system is shut down"
  )
  $cleanMarks = @(Get-Milestones $cleanSequence)
  if ($cleanMarks.Count -ne 4 -or
      $cleanMarks[1].Kind -cne "ENCERRANDO" -or
      @($cleanMarks | Where-Object { $_.Kind -eq "PEDIDO_DESLIGAMENTO" }).Count -ne 0) {
    Fail "Autoteste de desligamento normal e pedido separado falhou."
  }
  Write-Output "AUTOTESTE APROVADO: marcos, shutdown curto e categorias seguras sem arquivo real."
  exit 0
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Exige Windows para analisar o sandbox privado."
}
Write-Output "=== ORBITA 3.42 | CICLO DE DESLIGAMENTO (SOMENTE LEITURA) ==="
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
      # Ordem relativa dos eventos especificos, sem timestamps nem conteudo bruto.
      $milestones = @(Get-Milestones $lines)
      Write-Output ("MARCOS_RELEVANTES: " + $milestones.Count)
      foreach ($milestone in @($milestones | Select-Object -Last 12)) {
        Write-Output ("MARCO: POS_" + $milestone.Position + " " + $milestone.Kind)
      }
      $lastReadiness = @($milestones | Where-Object { $_.Kind -eq "PRONTIDAO" } | Select-Object -Last 1)
      $lastShutdown = @($milestones | Where-Object { $_.Kind -eq "DESLIGAMENTO" } | Select-Object -Last 1)
      if ($lastReadiness.Count -gt 0 -and $lastShutdown.Count -gt 0) {
        if ($lastReadiness[0].Position -lt $lastShutdown[0].Position) {
          Write-Output "ORDEM: PRONTIDAO_ANTES_DO_ULTIMO_DESLIGAMENTO"
          $requestsInWindow = @($milestones | Where-Object {
            $_.Kind -eq "PEDIDO_DESLIGAMENTO" -and
            $_.Position -gt $lastReadiness[0].Position -and
            $_.Position -le $lastShutdown[0].Position
          })
          if ($requestsInWindow.Count -gt 0) {
            Write-Output "PEDIDO_RECONHECIDO_ENTRE_MARCOS: SIM"
          } else {
            Write-Output "PEDIDO_RECONHECIDO_ENTRE_MARCOS: NAO"
          }
          $consoleIndicators = @($milestones | Where-Object {
            $_.Kind -eq "EXCECAO_CONSOLE" -and
            $_.Position -gt $lastReadiness[0].Position -and
            $_.Position -le $lastShutdown[0].Position
          })
          Write-Output ("EXCECAO_CONSOLE_RECONHECIDA_ENTRE_MARCOS: " + $(if ($consoleIndicators.Count -gt 0) { "SIM" } else { "NAO" }))
          Write-Output "INTERPRETACAO: pedido/indicador NAO reconhecido nunca comprova ausencia do evento real."
          Write-Output "CHECKPOINT shutdown immediate NAO comprova parada abrupta."
        } else {
          Write-Output "ORDEM: ULTIMA_PRONTIDAO_APOS_ULTIMO_DESLIGAMENTO"
        }
      } else {
        Write-Output "ORDEM: INSUFICIENTE_PARA_COMPARACAO"
      }
      Write-Output "AVISO: ausencia de categoria nao demonstra ausencia do evento real."
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
