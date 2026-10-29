# ORBITA Aurora 3.48 | Painel textual sanitizado para gates de recuperacao.
# -SelfTest: apenas dados artificiais. -Check: pg_isready + SHA256/TOC offline.
# Nenhum login, senha, SQL, criacao, start/stop ou restore.
[CmdletBinding()]
param([switch]$SelfTest,[switch]$Check)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$tcpScript = Join-Path $PSScriptRoot "private_restore_native_windows_readiness.ps1"
$archiveScript = Join-Path $PSScriptRoot "private_restore_archive_inventory_windows.ps1"

function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Get-TcpStatus([string[]]$lines) {
  $identity = @($lines | Where-Object {
    ([string]$_) -ceq "IDENTIDADE: PG17, ACL, configuracao, PID e listener exclusivo aprovados."
  }).Count -eq 1
  $ready = @($lines | Where-Object {
    ([string]$_) -ceq "PG_ISREADY: ACEITANDO_CONEXOES"
  }).Count -eq 1
  $gate = @($lines | Where-Object {
    ([string]$_) -ceq "GATE: PRONTIDAO_TCP_APROVADA."
  }).Count -eq 1
  $denied = @($lines | Where-Object {
    ([string]$_) -like "GATE: BLOQUEADO*" -or
    ([string]$_) -like "GATE: PRONTIDAO_TCP_NAO_APROVADA*"
  }).Count -gt 0
  if ($identity -and $ready -and $gate -and -not $denied) {
    return "PRONTIDAO_TCP_APROVADA"
  }
  return "NAO_DEMONSTRADA"
}
function Get-ArchiveStatus([string[]]$lines) {
  $list = @($lines | Where-Object {
    ([string]$_) -match '^TOC: \d+ entradas, \d+ itens TABLE DATA, \d+ POLICY, \d+ SCHEMA\.$'
  }).Count -eq 1
  $risk = @($lines | Where-Object {
    ([string]$_) -ceq "COMPATIBILIDADE_COM_POSTGRESQL_NATIVO: NAO_DEMONSTRADA"
  }).Count -eq 1
  $gate = @($lines | Where-Object {
    ([string]$_) -ceq "GATE: SOMENTE_PLANEJAMENTO; RESTAURACAO E MIGRACOES BLOQUEADAS."
  }).Count -eq 1
  $end = @($lines | Where-Object {
    ([string]$_) -ceq "SEGURANCA: sem conexao ao banco, SQL, dump em stdout, senhas ou arquivos novos."
  }).Count -eq 1
  if ($list -and $risk -and $gate -and $end) { return "HASH_ACL_TOC_VERIFICADOS" }
  return "NAO_DEMONSTRADO"
}

if ($SelfTest -and $Check) { Fail "Escolha apenas um modo." }
if ($SelfTest) {
  $tcp = @(
    "IDENTIDADE: PG17, ACL, configuracao, PID e listener exclusivo aprovados.",
    "PG_ISREADY: ACEITANDO_CONEXOES",
    "GATE: PRONTIDAO_TCP_APROVADA."
  )
  $archive = @(
    "TOC: 599 entradas, 42 itens TABLE DATA, 7 POLICY, 9 SCHEMA.",
    "COMPATIBILIDADE_COM_POSTGRESQL_NATIVO: NAO_DEMONSTRADA",
    "GATE: SOMENTE_PLANEJAMENTO; RESTAURACAO E MIGRACOES BLOQUEADAS.",
    "SEGURANCA: sem conexao ao banco, SQL, dump em stdout, senhas ou arquivos novos."
  )
  if ((Get-TcpStatus $tcp) -cne "PRONTIDAO_TCP_APROVADA" -or
      (Get-TcpStatus (@($tcp + "GATE: PRONTIDAO_TCP_NAO_APROVADA; nao repetir start."))) -cne "NAO_DEMONSTRADA" -or
      (Get-TcpStatus @("PG_ISREADY: ACEITANDO_CONEXOES")) -cne "NAO_DEMONSTRADA" -or
      (Get-ArchiveStatus $archive) -cne "HASH_ACL_TOC_VERIFICADOS" -or
      (Get-ArchiveStatus @("TOC: 599 entradas, 42 itens TABLE DATA, 7 POLICY, 9 SCHEMA.")) -cne "NAO_DEMONSTRADO" -or
      (Get-ArchiveStatus (@($archive + "segredo nao previsto"))) -cne "HASH_ACL_TOC_VERIFICADOS") {
    Fail "Autoteste de consolidacao de gates falhou."
  }
  Write-Output "AUTOTESTE APROVADO: preflight consolidado sintetico, nenhum dado ou conexao real."
  exit 0
}
if (-not $Check) { Fail "Use -SelfTest ou -Check, sem efeitos colaterais." }
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Roteiro do operador exige Windows."
}
foreach ($path in @($tcpScript,$archiveScript)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    Fail "Verificador obrigatorio ausente."
  }
  if (((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail "Verificador com junction/symlink: abortado."
  }
}
Write-Output "=== ORBITA 3.48 | PRONTIDAO PARA HOMOLOGACAO ==="
Write-Output "MODO: SOMENTE LEITURA; sem senha, SQL ou restore."
$tcpStatus = "NAO_DEMONSTRADA"
try {
  $tcpOutput = @(& $tcpScript -Check)
  $tcpStatus = Get-TcpStatus $tcpOutput
} catch {
  $tcpStatus = "NAO_DEMONSTRADA"
}
Write-Output ("CLUSTER_TCP: " + $tcpStatus)
$backupStatus = "NAO_DEMONSTRADO"
try {
  # Inclui verificador de ACL, checksum e toc do arquivo real privado.
  $backupOutput = @(& $archiveScript)
  $backupStatus = Get-ArchiveStatus $backupOutput
} catch {
  $backupStatus = "NAO_DEMONSTRADO"
}
Write-Output ("ARQUIVO_BACKUP: " + $backupStatus)
Write-Output "POSTGRES_LOCAL_SCRAM: PENDENTE_DE_AUTORIZACAO."
Write-Output "SUPABASE_AUTH_JWT_RLS: NAO_INFERIDOS_DO_POSTGRESQL_LOCAL."
Write-Output "COMPATIBILIDADE_DO_RESTORE: NAO_DEMONSTRADA."
if ($tcpStatus -eq "PRONTIDAO_TCP_APROVADA" -and
    $backupStatus -eq "HASH_ACL_TOC_VERIFICADOS") {
  Write-Output "PROXIMO_GATE: AUTENTICACAO_LOCAL_OPCIONAL_3_47; SEM RESTORE."
} else {
  Write-Output "PROXIMO_GATE: RESOLVER_PRECHECK_FALHO; NAO_TENTAR_RESTART_AUTOMATICO."
}
Write-Output "BLOQUEADO: pg_restore, SQL 002/003, main, Vercel, Telegram e servico 5432."
Write-Output "SEGURANCA: nenhuma saida bruta de arquivo, senha, log ou SQL divulgada."
