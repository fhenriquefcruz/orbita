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
function Summarize-Compatibility([string]$toc) {
  # Usar SOMENTE tipos canonicos do TOC; jamais divulgar linhas, nomes ou donos.
  # Os tipos compostos precisam vir antes dos prefixos simples.
  $kinds = @(
    "DEFAULT ACL", "ROW SECURITY", "TABLE DATA", "SEQUENCE SET",
    "MATERIALIZED VIEW", "EVENT TRIGGER", "FOREIGN DATA WRAPPER",
    "FOREIGN TABLE", "USER MAPPING", "EXTENSION", "ACL", "FUNCTION",
    "PROCEDURE", "TRIGGER", "POLICY", "PUBLICATION", "SUBSCRIPTION",
    "SCHEMA", "BLOB", "BLOBS"
  )
  $counts = @{}
  foreach ($kind in $kinds) { $counts[$kind] = 0 }
  $rows = [regex]::Matches($toc,'(?m)^\s*\d+;\s+\d+\s+\d+\s+(?<payload>[^\r\n]*)')
  $managedObjects = 0
  foreach ($row in $rows) {
    $payload = $row.Groups["payload"].Value
    foreach ($kind in $kinds) {
      if ($payload.StartsWith($kind + " ",[StringComparison]::Ordinal) -or
          $payload.Equals($kind,[StringComparison]::Ordinal)) {
        $counts[$kind]++
        break
      }
    }
    # Supabase possui schemas/objetos gerenciados que nao existem automaticamente
    # no servidor PostgreSQL nativo isolado (nunca inferir compatibilidade).
    if ($payload -match '^(?:TABLE DATA|TABLE|SEQUENCE|FUNCTION|PROCEDURE|POLICY|ROW SECURITY|ACL|DEFAULT ACL|SCHEMA|VIEW|TRIGGER|INDEX|TYPE|EXTENSION)\s+(?:-\s+)?(?:auth|storage|realtime|extensions|vault|graphql|supabase_functions|pgsodium|net)(?:\s|$)') {
      $managedObjects++
    }
  }
  $sourceMajor = "NAO_INFORMADO"
  $sourceMatch = [regex]::Match($toc,'(?m)^;\s*Dumped from database version:\s*(\d{1,2})(?:\.|\s|$)')
  if ($sourceMatch.Success) {
    if ($sourceMatch.Groups[1].Value -eq "17") {
      $sourceMajor = "POSTGRES_17"
    } else {
      $sourceMajor = "OUTRO_MAJOR"
    }
  }
  return [pscustomobject]@{
    EntryCount = $rows.Count
    SourceMajor = $sourceMajor
    Extensions = $counts["EXTENSION"]
    Acl = $counts["ACL"]
    DefaultAcl = $counts["DEFAULT ACL"]
    Policies = $counts["POLICY"]
    RowSecurity = $counts["ROW SECURITY"]
    Functions = ($counts["FUNCTION"] + $counts["PROCEDURE"])
    Triggers = ($counts["TRIGGER"] + $counts["EVENT TRIGGER"])
    Managed = $managedObjects
    Foreign = ($counts["FOREIGN DATA WRAPPER"] + $counts["FOREIGN TABLE"] + $counts["USER MAPPING"])
    PubSub = ($counts["PUBLICATION"] + $counts["SUBSCRIPTION"])
    Blobs = ($counts["BLOB"] + $counts["BLOBS"])
    Sequences = $counts["SEQUENCE SET"]
  }
}
function Summarize-RestoreScope([string]$toc) {
  # Estatisticas conservadoras: NAO selecionam nem geram lista de restore.
  # Um objeto no esquema public nao e necessariamente independente do Supabase.
  $appData = 0
  $managedData = 0
  $otherData = 0
  $appObjectRows = 0
  $publicOtherData = 0
  $pattern = '(?m)^\s*\d+;\s+\d+\s+\d+\s+(?<kind>TABLE DATA|TABLE|SEQUENCE SET|SEQUENCE|INDEX|CONSTRAINT|POLICY|ROW SECURITY|TRIGGER|FUNCTION|PROCEDURE|ACL|DEFAULT ACL)\s+(?<schema>[a-zA-Z_][a-zA-Z_0-9]*)\s+(?<object>[^\s;]+)'
  $managedSchemas = @("auth","storage","realtime","extensions","vault","graphql","supabase_functions","pgsodium","net")
  foreach ($entry in [regex]::Matches($toc,$pattern)) {
    $kind = $entry.Groups["kind"].Value
    $schema = $entry.Groups["schema"].Value
    $name = $entry.Groups["object"].Value
    $isApp = ($schema -ceq "public" -and $name.StartsWith("orbita_",[StringComparison]::Ordinal))
    $isManaged = ($managedSchemas -ccontains $schema)
    if ($isApp) { $appObjectRows++ }
    if ($kind -cne "TABLE DATA") { continue }
    if ($isApp) {
      $appData++
    } elseif ($isManaged) {
      $managedData++
    } else {
      $otherData++
      if ($schema -ceq "public") { $publicOtherData++ }
    }
  }
  return [pscustomobject]@{
    AppTableData = $appData
    ManagedTableData = $managedData
    OtherTableData = $otherData
    OtherPublicTableData = $publicOtherData
    AppObjectRows = $appObjectRows
  }
}
function Show-RestoreScope($model,$scope,$inventory) {
  if (($scope.AppTableData + $scope.ManagedTableData + $scope.OtherTableData) -ne $inventory.TableData) {
    Fail "Particao de TABLE DATA diverge do TOC: nenhum procedimento de restore autorizado."
  }
  Write-Output "=== ORBITA | ESCOPO DE RECUPERACAO (SOMENTE TOC) ==="
  Write-Output ("TABLE_DATA_PUBLIC_ORBITA: " + $scope.AppTableData)
  Write-Output ("TABLE_DATA_SCHEMAS_GERENCIADOS: " + $scope.ManagedTableData)
  Write-Output ("TABLE_DATA_OUTROS: " + $scope.OtherTableData)
  Write-Output ("TABLE_DATA_PUBLIC_NAO_ORBITA: " + $scope.OtherPublicTableData)
  Write-Output ("ENTRADAS_PUBLIC_ORBITA_CANDIDATAS: " + $scope.AppObjectRows)
  if ($model.Managed -gt 0 -or $model.Extensions -gt 0 -or $model.PubSub -gt 0) {
    Write-Output "ESTRATEGIA: BACKUP_COMPLETO_NO_POSTGRES_NATIVO_NAO_APROVADO."
    Write-Output "PROXIMO_PLANO: ANALISAR_APP_ONLY_VS_SUPABASE_ISOLADO; NENHUM_FILTRO_EXECUTAVEL_GERADO."
  } else {
    Write-Output "ESTRATEGIA: COMPATIBILIDADE_NATIVA_AINDA_NAO_COMPROVADA."
    Write-Output "PROXIMO_PLANO: REVISAR_DEPENDENCIAS_ANTES_DE_QUALQUER_RESTORE."
  }
  Write-Output "AVISO: tabela identificada por nome nao prova independencia de Auth, triggers, FK ou roles."
  Write-Output "SEGURANCA: nenhum SQL, restore, lista de IDs ou dado privado publicado."
}
function Show-Compatibility($model) {
  Write-Output "=== ORBITA 3.48 | MATRIZ DE COMPATIBILIDADE OFFLINE ==="
  Write-Output ("VERSAO_ORIGEM: " + $model.SourceMajor)
  Write-Output ("DEPENDENCIAS: EXTENSION=" + $model.Extensions + "; FOREIGN=" + $model.Foreign + "; PUBSUB=" + $model.PubSub)
  Write-Output ("SEGURANCA_DDL: ACL=" + $model.Acl + "; DEFAULT_ACL=" + $model.DefaultAcl +
                "; POLICY=" + $model.Policies + "; ROW_SECURITY=" + $model.RowSecurity)
  Write-Output ("CODIGO_E_DADOS: FUNCOES=" + $model.Functions + "; TRIGGERS=" + $model.Triggers +
                "; SEQUENCE_SET=" + $model.Sequences + "; BLOB=" + $model.Blobs)
  Write-Output ("OBJETOS_EM_SCHEMAS_GERENCIADOS: " + $model.Managed)
  Write-Output "COMPATIBILIDADE_COM_POSTGRESQL_NATIVO: NAO_DEMONSTRADA"
  Write-Output "RISCO: extensoes, roles, owners, privilegios, RLS e dependencias exigem revisao."
  Write-Output "ALERTA: TOC nao comprova dados restauraveis nem codigo SQL confiavel."
  Write-Output "GATE: SOMENTE_PLANEJAMENTO; RESTAURACAO E MIGRACOES BLOQUEADAS."
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
  $riskSample = @'
; Dumped from database version: 17.4
10; 0 0 EXTENSION - pgcrypto postgres
11; 0 0 DEFAULT ACL public DEFAULT PRIVILEGES postgres
12; 0 0 ACL public my_table postgres
13; 0 0 POLICY public records records_select postgres
14; 0 0 ROW SECURITY public records postgres
15; 0 0 FUNCTION public f() postgres
16; 0 0 TRIGGER public t trigger postgres
17; 0 0 SCHEMA - auth postgres
18; 0 0 TABLE DATA auth users postgres
19; 0 0 PUBLICATION - publication postgres
20; 0 0 SEQUENCE SET public seq postgres
'@
  $risk = Summarize-Compatibility $riskSample
  if ($risk.SourceMajor -cne "POSTGRES_17" -or $risk.Extensions -ne 1 -or
      $risk.DefaultAcl -ne 1 -or $risk.Acl -ne 1 -or
      $risk.Policies -ne 1 -or $risk.RowSecurity -ne 1 -or
      $risk.Functions -ne 1 -or $risk.Triggers -ne 1 -or
      $risk.Managed -ne 2 -or $risk.PubSub -ne 1 -or
      $risk.Sequences -ne 1 -or $risk.EntryCount -ne 11) {
    Fail "Autoteste de classificacao de compatibilidade 3.48 falhou."
  }
  $otherVersion = Summarize-Compatibility "; Dumped from database version: 16.7"
  if ($otherVersion.SourceMajor -cne "OUTRO_MAJOR") {
    Fail "Autoteste de divergencia de versao major falhou."
  }
  $scopeSample = @'
1; 0 0 TABLE DATA auth users postgres
2; 0 0 TABLE DATA storage objects postgres
3; 0 0 TABLE DATA public orbita_records postgres
4; 0 0 TABLE DATA public orbita_chat_messages postgres
5; 0 0 TABLE DATA public independent_records postgres
6; 0 0 TABLE public orbita_records postgres
7; 0 0 POLICY public orbita_records select_self postgres
8; 0 0 TABLE DATA analytics history postgres
'@
  $scope = Summarize-RestoreScope $scopeSample
  if ($scope.AppTableData -ne 2 -or $scope.ManagedTableData -ne 2 -or
      $scope.OtherTableData -ne 2 -or $scope.OtherPublicTableData -ne 1 -or
      $scope.AppObjectRows -ne 4) {
    Fail "Autoteste de particao APP_ONLY e schemas gerenciados falhou."
  }
  $fakeInventory = [pscustomobject]@{ TableData = 6 }
  $fakeModel = [pscustomobject]@{ Managed = 2; Extensions = 1; PubSub = 0 }
  $checkLines = @(Show-RestoreScope $fakeModel $scope $fakeInventory)
  if (($checkLines -join " ") -notmatch 'BACKUP_COMPLETO_NO_POSTGRES_NATIVO_NAO_APROVADO') {
    Fail "Autoteste de bloqueio do restore nativo integral falhou."
  }
  $detectedMismatch = $false
  try {
    $badInventory = [pscustomobject]@{ TableData = 7 }
    $null = @(Show-RestoreScope $fakeModel $scope $badInventory)
  } catch { $detectedMismatch = $true }
  if (-not $detectedMismatch) { Fail "Autoteste nao bloqueou inconsistencia do TOC." }
  Write-Output "AUTOTESTE APROVADO: inventario, riscos e particao APP_ONLY sinteticos; nenhuma conexao."

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
$riskModel = Summarize-Compatibility ($lines -join [Environment]::NewLine)
if ($riskModel.EntryCount -ne $inventory.Entries) {
  Fail "Inconsistencia no numero de entradas do TOC; abortar planejamento."
}
Show-Compatibility $riskModel
$scopeModel = Summarize-RestoreScope ($lines -join [Environment]::NewLine)
Show-RestoreScope $riskModel $scopeModel $inventory
Write-Output "AVISO: TOC mostra objetos, NAO confirma linhas restauraveis, roles, extensoes ou Supabase Auth."
Write-Output "PROIBIDO: nao executar pg_restore de dados ate destino isolado verificado e plano de compatibilidade."
Write-Output "SEGURANCA: sem conexao ao banco, SQL, dump em stdout, senhas ou arquivos novos."
