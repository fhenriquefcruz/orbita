# ORBITA Aurora 3.37 | Inventario OFFLINE do catalogo do backup privado.
# Somente leitura: nao conecta ao banco, nao executa SQL nem pg_restore de dados.
[CmdletBinding()]
param(
  [string]$ManifestPath = "",
  [switch]$SelfTest
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$project = "tbqfymedgdsdrgkqmuni"
function Fail([string]$reason) { throw [InvalidOperationException]::new($reason) }
function Has-TableData([string]$toc,[string]$schema,[string]$table) {
  $pattern = '(?m)^\s*\d+;\s+\d+\s+\d+\s+TABLE DATA\s+' +
    [regex]::Escape($schema) + '\s+' + [regex]::Escape($table) + '(?:\s|$)'
  return [regex]::IsMatch($toc,$pattern)
}
function Summarize-Toc([string]$toc) {
  $entryPattern = '(?m)^\s*\d+;\s+\d+\s+\d+\s+'
  $entries = [regex]::Matches($toc,$entryPattern).Count
  $dataRows = [regex]::Matches($toc,'(?m)^\s*\d+;\s+\d+\s+\d+\s+TABLE DATA\s+').Count
  $policyRows = [regex]::Matches($toc,'(?m)^\s*\d+;\s+\d+\s+\d+\s+POLICY\s+').Count
  $schemaRows = [regex]::Matches($toc,'(?m)^\s*\d+;\s+\d+\s+\d+\s+SCHEMA\s+').Count
  $authUsers = Has-TableData $toc "auth" "users"
  $orbitaRecords = Has-TableData $toc "public" "orbita_records"
  $orbitaChat = Has-TableData $toc "public" "orbita_chat_messages"
  $orbitaTelegram = Has-TableData $toc "public" "orbita_telegram_updates"
  return [pscustomobject]@{
    Entries = $entries
    TableData = $dataRows
    Policies = $policyRows
    Schemas = $schemaRows
    AuthUsers = $authUsers
    Records = $orbitaRecords
    Chat = $orbitaChat
    Telegram = $orbitaTelegram
  }
}
function Show-Inventory($data) {
  Write-Output ("TOC: {0} entradas, {1} itens TABLE DATA, {2} POLICY, {3} SCHEMA." -f $data.Entries,$data.TableData,$data.Policies,$data.Schemas)
  Write-Output ("TABLE DATA auth.users: " + $data.AuthUsers)
  Write-Output ("TABLE DATA public.orbita_records: " + $data.Records)
  Write-Output ("TABLE DATA public.orbita_chat_messages: " + $data.Chat)
  Write-Output ("TABLE DATA public.orbita_telegram_updates: " + $data.Telegram)
  if (-not ($data.AuthUsers -and $data.Records -and $data.Chat -and $data.Telegram)) {
    Fail "Catalogo sem todas as tabelas fundamentais: NAO restaurar."
  }
}

if ($SelfTest) {
  $sample = @'
;
; Archive created at some time
42; 2615 123 SCHEMA - public postgres
43; 0 123 TABLE DATA auth users postgres
44; 0 124 TABLE DATA public orbita_records postgres
45; 0 125 TABLE DATA public orbita_chat_messages postgres
46; 0 126 TABLE DATA public orbita_telegram_updates postgres
47; 0 127 POLICY public orbita_records orbita_records_select_self postgres
'@
  $found = Summarize-Toc $sample
  if ($found.Entries -ne 6 -or $found.TableData -ne 4 -or
      $found.Policies -ne 1 -or $found.Schemas -ne 1) {
    Fail "Teste sintetico falhou no contador do TOC."
  }
  if (-not ($found.AuthUsers -and $found.Records -and $found.Chat -and $found.Telegram)) {
    Fail "Teste sintetico falhou na deteccao de tabelas."
  }
  if (Has-TableData $sample "public" "orbita_action_proposals") {
    Fail "Teste sintetico encontrou objeto inexistente."
  }
  Write-Output "AUTOTESTE APROVADO: analise offline do TOC sem acessar backup real."
  exit 0
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Fail "Este inventario privado exige Windows."
}
if (-not $ManifestPath) {
  $dir = Join-Path $HOME "orbita-backups-privados"
  if (-not (Test-Path -LiteralPath $dir -PathType Container)) {
    Fail "Diretorio privado de backup nao encontrado."
  }
  $last = Get-ChildItem -LiteralPath $dir -Filter "*.manifest.json" -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $last) { Fail "Nenhum manifesto privado encontrado." }
  $ManifestPath = $last.FullName
}
$manifest = [IO.Path]::GetFullPath($ManifestPath)
$verify = Join-Path $PSScriptRoot "verify_database_backup_windows.ps1"
if (-not (Test-Path -LiteralPath $verify -PathType Leaf)) {
  Fail "Verificador ORBITA nao encontrado."
}
& powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File $verify -ManifestPath $manifest
if ($LASTEXITCODE -ne 0) { Fail "Backup nao verificado: analise abortada." }

$metadata = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
if ($metadata.project_ref -ne $project) { Fail "Manifesto de projeto inesperado." }
$archive = Join-Path (Split-Path -Parent $manifest) ([string]$metadata.archive_filename)
$cmd = Get-Command pg_restore.exe -ErrorAction SilentlyContinue
$pgRestore = if ($cmd -and $cmd.Source) {
  [string]$cmd.Source
} else {
  "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe"
}
if (-not (Test-Path -LiteralPath $pgRestore -PathType Leaf)) {
  Fail "pg_restore.exe nao encontrado."
}
$oldPreference = $ErrorActionPreference
try {
  $ErrorActionPreference = "Continue"
  $lines = @(& $pgRestore --list $archive 2>$null)
  $exitCode = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $oldPreference
}
if ($exitCode -ne 0) { Fail "Nao foi possivel ler o TOC do arquivo." }
$inventory = Summarize-Toc ($lines -join [Environment]::NewLine)
Write-Output "=== AURORA 3.37 | INVENTARIO RESTRITO DO ARQUIVO ==="
Show-Inventory $inventory
Write-Output "AVISO: TOC mostra objetos, NAO confirma linhas restauraveis, roles, extensoes ou Supabase Auth."
Write-Output "PROIBIDO: nao executar pg_restore de dados ate destino isolado verificado e plano de compatibilidade."
Write-Output "SEGURANCA: sem conexao ao banco, SQL, dump em stdout, senhas ou arquivos novos."
