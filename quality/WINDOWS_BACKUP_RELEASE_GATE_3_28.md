# ORBITA Aurora 3.28 — Prova HTTP concluída e backup privado no Windows

## Evidência de homologação — 26/10/2026

O operador executou o script `quality/auth_chat_fixture_http.py` em
duas contas **reais** do Supabase Auth do projeto exclusivo ORBITA.
O resultado local, sem compartilhar JWT/senhas, foi:

> PASSOU — chat HTTP isolado entre duas contas; fixture excluída.
> PASSOU — tentativa de excluir o chat alheio negada pela RLS.

Em seguida, uma consulta administrativa **somente leitura** conferiu no
projeto Supabase `tbqfymedgdsdrgkqmuni`:

| Evidência | Resultado |
| --- | --- |
| Contas Auth com e-mail confirmado | 2 |
| Registros do ORBITA | 1, preservado |
| Mensagens na tabela de chat | 0 |
| Fixtures com prefixo `ORBITA_RLS_FIXTURE_` | 0 |
| Tabela de propostas da SQL 002 | Não instalada |
| RPC da SQL 002 | Não instalada |

Esta combinação conclui o gate de **isolamento de leitura/remoção cruzada
por HTTP** exercitado pelo teste, com limpeza verificada. Ela NÃO equivale
a homologação de todas as ações de escrita, recuperação de conta, Safari,
webhook ou recuperação de banco.

## Diagnóstico de timeout do pooler (Aurora 3.28.1)

Se o Windows informar **`pg_dump: connection timed out`**, isto ainda não
é uma falha da senha. Primeiro, sem fornecer credenciais, rode:

```powershell
Test-NetConnection aws-1-sa-east-1.pooler.supabase.com -Port 5432
Test-NetConnection tbqfymedgdsdrgkqmuni.supabase.co -Port 443
```

Os endereços acima são apenas os observados no ensaio do titular e no
projeto ORBITA. Confirme o **host real do Session pooler no Connect**;
este pode mudar. Verifique `TcpTestSucceeded` em cada resultado.
O comando `Test-NetConnection` não autentica no banco e não envia senha.

- **5432 False / 443 True:** acesso HTTPS não significa acesso nativo
  PostgreSQL. A rede pode bloquear 5432, o pooler pode estar inacessível
  ou o host pode ter mudado. Confirme a URL no Dashboard e teste em outra
  rede autorizada, como hotspot particular, sem alterar o firewall global.
- **5432 True:** repita o script. Se ocorrer outro erro, verifique o
  *database user*, senha do banco, `sslmode=require` e detalhes de
  conexão exibidos no Dashboard; não redefina a senha precipitadamente.
- **443 False:** problema mais amplo de conexão, DNS, VPN, rede ou
  indisponibilidade da rota local; verifique a conectividade antes de
  prosseguir.

O script passou a checar **5432 antes de pedir a senha** e a tratar os erros
nativos do PowerShell 5.1 de modo controlado. Não force a troca para porta
6543 do transaction pooler apenas para contornar o erro: para `pg_dump`,
o Supabase recomenda conexão direta quando possível, ou o **Session pooler**
em redes IPv4. Documentação de referência:
https://supabase.com/docs/guides/database/connecting-to-postgres

Atenção: o script **não cria backup** enquanto 5432 estiver indisponível.
Uma tentativa malsucedida não comprova recuperabilidade. Mantenha SQL 002/003
bloqueadas e nunca compartilhe senhas ou dumps.

## O backup é o próximo bloqueio

Projeto ORBITA usa Supabase Free. O histórico de backup diário gerenciado
dos planos pagos não está disponível no Free; recomenda-se exportação
lógica privada. Fonte:
https://supabase.com/docs/guides/platform/backups

O utilitário Python da Aurora 3.25 usa permissões estilo POSIX
(`0700`/`0600`), inadequadas para uma avaliação fiel de ACLs NTFS.
**Para Windows, use a variante específica desta fase**:

- `quality/private_database_backup_windows.ps1`
- `quality/verify_database_backup_windows.ps1`

A versão PowerShell cria pasta privada fora do Git, restringe ACLs com
`icacls` ao usuário titular, SYSTEM e Administrators, exige o projeto
correto e TLS, faz `pg_dump` custom, verifica com `pg_restore --list`,
confere quatro tabelas essenciais e grava manifesto com SHA-256.
O verificador **não conecta ao banco**: revisita o hash, tamanho, catálogo
e permissões no arquivo local. Os scripts não enviam dados à conversa nem
mudam banco.

### 1. Instalar os utilitários PostgreSQL

No PowerShell do Windows, teste:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" --version
```

Se não existir, o pacote de PostgreSQL 17 está disponível pelo WinGet:

```powershell
winget install --id PostgreSQL.PostgreSQL.17 -e --source winget
```

A instalação desse pacote pode instalar também o **servidor PostgreSQL
local** e pedir configuração administrativa. A senha desse servidor local
**não** é a senha do banco Supabase e não deve ser usada por engano.
O processo de backup precisa apenas dos executáveis `pg_dump` e
`pg_restore` da versão 17 ou posterior. A instalação é feita no próprio
PC, nunca pela ferramenta conectada.

Feche/reabra o PowerShell se instalar componentes novos.

### 2. Atualizar homologação e checar pré-requisitos

```powershell
cd "$HOME\orbita"
git pull --ff-only origin feat/supabase-auth-protected-panel
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_database_backup_windows.ps1 -CheckPrerequisites
```

Esse comando é apenas um diagnóstico, **sem conexão ao Supabase**.
Se informar `PRONTO`, o backup pode ser iniciado. Se informar ausência
do `pg_dump`, reveja a instalação (inclusive PATH ou diretório versão 17).

### 3. Gerar backup local com autorização explícita

Abra o projeto ORBITA no dashboard do Supabase, clique em **Connect**,
selecione **Session pooler (porta 5432)** e identifique:
- Host correspondente ao **projeto ORBITA**, terminando em
  `.pooler.supabase.com`.
- Database user **postgres.tbqfymedgdsdrgkqmuni**.
- Senha do **banco de dados** do projeto ORBITA, obtida de sua
  configuração privada. Não confundir com login de usuário do painel.

```powershell
cd "$HOME\orbita"
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_database_backup_windows.ps1 -ConfirmProject tbqfymedgdsdrgkqmuni
```

Quando solicitado, digite **host** e **database user** que aparecem no
Connect e a **senha do banco em prompt oculto**. Nunca digite a senha em
linha de comando, não a envie pelo chat e não a inclua na URL do GitHub.

O backup é criado no diretório privado
`%USERPROFILE%\orbita-backups-privados`, fora da pasta Git.
O arquivo contém dados do banco e pode incluir dados de usuários,
hashes e registros sensíveis. Use disco criptografado (BitLocker) e
cópia adicional em armazenamento privado criptografado.

### 4. Revalidar integridade da exportação

Após receber `BACKUP CRIADO`, verifique o manifesto mais recente:

```powershell
$manifest = Get-ChildItem "$HOME\orbita-backups-privados" -Filter "*.manifest.json" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\verify_database_backup_windows.ps1 -ManifestPath $manifest.FullName
```

Resultado pretendido:

```text
APROVADO - integridade, hash SHA256, ACLs e catalogo conferidos.
RESTAURACAO NAO TESTADA - SQL 002/003 continuam bloqueadas.
```

**Importante:** `BACKUP CRIADO` / `APROVADO` validam um **arquivo**,
não sua recuperabilidade integral. Uma restauração isolada testada ainda
é requisito. `pg_restore --list` **não é um restore**.

### 5. Próxima fase: restauração isolada

Escolher um destino temporário e totalmente separado do Supabase produtivo
com PostgreSQL compatível e, quando necessário, ambiente Supabase para
validar roles, políticas RLS, funções, esquema `auth` e dados.

Recomenda-se ensaio de restauração documentado, revisão dos erros de
extensões/roles e verificação dos registros após restaurar. O backup
`pg_dump` contém banco lógico, mas não garante sozinho a restauração de
configurações externas do Supabase, arquivos Storage ou segredos de
serviços. **Não criar projeto pago ou restaurar sobre produção sem
autorização explícita.**

Até essa restauração ocorrer, SQL 002/003 continuam não aplicadas,
`main` continua protegida e as duas flags de ações naturais e webhook
delivery v2 continuam desativadas por padrão.

## Segurança e limites desta entrega

- A checagem do banco real e a prova de chat concluída são eventos
  separados dos novos utilitários Windows. Os scripts Windows ainda não
  foram executados pelo titular no computador real.
- A suíte automática GitHub é offline; valida a presença dos controles
  importantes nos scripts, mas **não valida as ACLs NTFS de um PC real**.
- O operador só deve considerar a integridade aprovada após executar no
  Windows e inspecionar a saída.
- Nunca incluir um `.dump`, senha, URI de conexão com credencial, JWT ou
  manifesto sensível em PRs, issues, anexos ou mensagens.
