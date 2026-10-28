# ORBITA — Aurora 3.37 | Verificação de identidade local + inventário do arquivo

**Data:** 28/10/2026 • **Ambiente:** Windows nativo, sem Docker/WSL/Linux.

A Aurora 3.36 trouxe um gerenciador **separado** para criar e iniciar
outro cluster PostgreSQL 17 em `$HOME\orbita-restore-sandbox`,
`127.0.0.1:55432`. Ainda **não há evidência enviada pelo titular** de
que ele tenha executado `-Initialize` ou `-Start`; não presumir cluster
criado. O servidor Windows preexistente `postgresql-x64-17` em
`0.0.0.0:5432` permanece **fora do escopo**.

## Próximas verificações (sempre leitura apenas)

```powershell
cd "$HOME\orbita"
git pull --ff-only origin feat/supabase-auth-protected-panel

# Estado da infraestrutura de recuperação — nunca executa initdb.
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_cluster.ps1 -Check

# Verificar se o cluster identificado pertence ao ORBITA e está isolado.
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_verify.ps1

# Conferir somente a ESTRUTURA do backup validado, sem expor dados.
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_archive_inventory_windows.ps1
```

Não executar `-Initialize` novamente caso a pasta privada já exista;
o gerenciador se recusa a sobrescrevê-la.

### O que o verificador de instância confere

- Pasta do sandbox e ACL privada, sem junctions/symlinks.
- Marcador ORBITA `ORBITA_NATIVE_RESTORE_SANDBOX_V1`, versão PostgreSQL 17.
- `postgresql.conf` com `listen_addresses='127.0.0.1'`,
  `port=55432`, `password_encryption='scram-sha-256'`.
- `pg_hba.conf` com apenas loopback SCRAM e rejeições gerais,
  sem regras inesperadas nem inclusão de configurações não auditadas.
- Ausência de overrides inseguros em `postgresql.auto.conf`.
- `pg_ctl status` associado ao diretório **exclusivo**,
  sem revelar a linha de comando ao chat.
- Se ativo, exige **um único listener** `127.0.0.1:55432`,
  cujo PID coincide com `postmaster.pid` da mesma pasta.
- Se ainda não iniciado, distingue `CLUSTER AUSENTE` de `CLUSTER PARADO`.
- Não conecta ao PostgreSQL, não solicita senha, não faz SQL ou restauração.

Se alguma verificação falhar, manter o dump privado sem uso e investigar
antes de qualquer `pg_restore`. **Nenhum resultado positivo autoriza
automática ou implicitamente uma restauração.**

### O que o inventário do arquivo mostra

- Invoca primeiro `verify_database_backup_windows.ps1` (hash SHA-256,
  permissões NTFS, catálogo das tabelas essenciais).
- Executa apenas `pg_restore --list` **sem `-d` ou host**, de modo que
  não abre conexão PostgreSQL nem executa SQL.
- Produz somente **contagens** de entradas/objetos `TABLE DATA`,
  `POLICY` e `SCHEMA`, e quatro indicadores booleanos para
  `auth.users` e as três tabelas essenciais `public.orbita_*`.
- Não imprime a listagem completa do arquivo, registros de usuário,
  tokens, conteúdo do dump, nomes de objetos adicionais ou credenciais.
- Não interpreta mera presença de objeto como recuperação ou validade de
  roles, funções, extensões, RLS ou login da plataforma.

O dump foi produzido por `pg_dump` convencional (custom); restaurá-lo
em PostgreSQL nativo pode resultar em objetos Supabase incompatíveis.
NÃO aplicar `--clean`, `--create`, `--if-exists` nem `--exit-on-error`
em ambiente não validado. Antes de executar qualquer comando de
restauração, revisar detalhadamente os objetos/diferenças de compatibilidade
**em dispositivo privado** e planejar uma importação isolada com
critérios verificáveis para cada tabela.

## Fases de recuperação

| Gate | Situação |
| --- | --- |
| Backup privado: SHA-256/ACL/TOC | **APROVADO** pelo titular |
| Ferramentas PostgreSQL 17 nativas | **APROVADAS** pelo titular |
| Cluster secundário configurado e ativo | **PENDENTE de saída real do Windows** |
| Inventário offline completo e compatibilidade | **PENDENTE** |
| `pg_restore` funcional em destino isolado | **NÃO EXECUTADO** |
| Recuperação funcional completa Supabase Auth/RLS/APIs | **NÃO EXECUTADA**, requer ambiente compatível |
| SQL novas 002/003 e release produção | **BLOQUEADOS** |

A CI executa apenas testes sintéticos do leitor de TOC e do verificador
de configuração; não importa backup, não usa senha e não cria cluster.

**Referências:** [PostgreSQL 17 pg_restore --list](https://www.postgresql.org/docs/17/app-pgrestore.html),
[PostgreSQL 17 pg_ctl status](https://www.postgresql.org/docs/17/app-pg-ctl.html),
[Supabase migração e restauração](https://supabase.com/docs/guides/self-hosting/restore-from-platform).
