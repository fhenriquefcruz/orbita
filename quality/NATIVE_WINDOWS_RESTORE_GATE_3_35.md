# ORBITA — Aurora 3.35 | Recuperação de dados usando apenas Windows

**Atualizado em 28/10/2026** • Homologação, **sem Linux/WSL/Docker**.

## Fatos confirmados pelo titular no PowerShell

- Backup privado validado: SHA-256, NTFS ACL, TOC de `pg_restore`.
- Ferramentas `psql` e `pg_restore` compatíveis com PostgreSQL 17.
- Serviço **`postgresql-x64-17` Running**.
- `C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe` existe.
- Porta local **5432** está ocupada pelo PID 3656, em **`0.0.0.0` e `::`**.
- Docker e WSL **não são pré-requisitos** para um ensaio de PostgreSQL **apenas**.
- Não há prova de recuperação funcional do Supabase Auth, roles ou API.

**Risco:** listener em `0.0.0.0` ou `::` significa que o processo aceita tentativas de conexão em múltiplas interfaces. Não prova acessibilidade por terceiros (firewall e `pg_hba.conf` também controlam acesso). **Não modificar este serviço, suas portas, configuração ou bancos** neste ensaio.

## Executar agora: diagnóstico seguro

```powershell
cd "$HOME\orbita"
git switch feat/supabase-auth-protected-panel
git pull --ff-only origin feat/supabase-auth-protected-panel
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_preflight.ps1
```

O script reaproveita o verificador privado original. Em seguida:
- identifica as versões `pg_restore`, `psql`, `pg_ctl`, `initdb`, `postgres`;
- lista nomes/estados de serviços PostgreSQL existentes;
- aponta listeners nas portas 5432 e 55432;
- alerta para bind wildcard (todas as interfaces);
- **não lê senhas**, não executa SQL, não cria bancos, não toca no firewall,
  não altera serviço, não instala programas e não transfere dumps.

O modo `-ToolsOnly` só serve para CI (não prova integridade do dump).

## Estratégia futura: segundo cluster, fora do servidor existente

Preparar um **segundo cluster PostgreSQL 17** em diretório privado e
isolado fora do repositório (por exemplo,
`$HOME\orbita-restore-sandbox\data`), **sem mexer** na instância da
porta 5432:

| Elemento | Destino planejado | Observação |
| --- | --- | --- |
| Software | binários PostgreSQL 17 já instalados | não requer Linux |
| Processo | instância `pg_ctl` do usuário, não serviço existente | sem `sc.exe`, `net stop`, `pg_ctl restart` no serviço |
| Dados | pasta privada sob usuário local | ACL sem acesso a terceiros |
| Porta | 55432, somente se livre | porta diferente da 5432 existente |
| Listener | `127.0.0.1` | **não** `0.0.0.0` ou `::` |
| Autenticação | SCRAM-SHA-256, inclusive em loopback | nunca `trust` com dados privados |
| Destino do restore | banco novo e descartável no segundo cluster | identificar host/porta antes de cada comando |
| Arquivo fonte | `orbita-backups-privados` | não mover/copiá-lo para Git |
| Limpeza | somente após comprovar resultados e revisar artefatos | sem apagar backup original |

Não rodar `initdb` nem `pg_restore` ainda: confirmar primeiro que
`initdb.exe` e `postgres.exe` existem e a porta 55432 está livre.
Não reutilizar o cluster existente, mesmo que possamos criar outra
database nele: preservar seu estado e suas outras aplicações.

## Critérios mínimos de recuperação — escopo delimitado

**Nível A: arquivo íntegro** — já aprovado. SHA-256, catálogo e ACL;
sem evidência de recuperação.

**Nível B: recuperação de dados PostgreSQL** — pendente. Restaurar em
cluster isolado, verificar saída sem falhas ignoradas, confrontar contagens,
chaves, constraints e registros sensíveis à integridade, validar ACLs do
destino e manter dados privados. Um dump `pg_dump` custom do Supabase pode
conter schemas, roles, extensões, funções e dependências **incompatíveis**
com o PostgreSQL padrão. Falhas exigem correção/estratégia compatível;
**não** declarar sucesso parcial como restauração completa.

**Nível C: recuperação da plataforma Supabase** — pendente, separada.
Validar Auth/GoTrue e cenários RLS com duas identidades, APIs e
permissões da plataforma em ambiente Supabase compatível. PostgreSQL
nativo sozinho **não** comprova Nível C. Se o computador não permite
contêineres, planejar destino **externo isolado** sujeito a autorização
específica e eventuais custos, sem compartilhar secrets em GitHub/ChatGPT.

## Proibições e critérios de encerramento

- Jamais executar `pg_restore` contra `db.tbqfymedgdsdrgkqmuni.supabase.co`,
  `*.pooler.supabase.com` ou serviço local existente `localhost:5432`.
- Jamais rodar `pg_restore --clean`, `dropdb`, `pg_ctl stop/restart` do
  serviço existente ou `supabase db push/reset` no projeto remoto.
- Nenhuma mudança em `main`, Vercel ou webhook Telegram.
- Migrações novas `002_action_proposals.sql` e
  `003_telegram_delivery.sql` **continuam bloqueadas**.
- Não anexar dumps, tokens ou manifestos privados em issues, mensagens
  ou repositórios.

### Referências

- [Supabase: Restoring a Platform Project to Self-Hosted](https://supabase.com/docs/guides/self-hosting/restore-from-platform) — atenção: filtragem específica Supabase CLI e dependência de roles/Auth.
- [Supabase: Connecting to Postgres](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [PostgreSQL 17: initdb](https://www.postgresql.org/docs/17/app-initdb.html)
- [PostgreSQL 17: pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html)
- [PostgreSQL 17: pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html)
