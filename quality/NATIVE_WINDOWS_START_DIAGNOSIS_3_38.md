# ORBITA Aurora 3.38 — PostgreSQL informado como iniciado, depois parado

**Evidência do titular em 28/10/2026 (Windows):**

- `pg_ctl` na Aurora 3.36 informou `esperando o servidor iniciar....feito / servidor iniciado`, mas **não foram mostradas** as mensagens finais `CLUSTER INICIADO` e `RESTAURACAO NAO EXECUTADA` do gerenciador.
- Logo depois, a verificação Aurora 3.37 retornou `IDENTIDADE: ... aprovados` e **`CLUSTER PARADO`**.
- Inventário privado do arquivo: **599 entradas de TOC**, **42 TABLE DATA**, **7 POLICY**, **9 SCHEMA**; `auth.users`, `orbita_records`, `orbita_chat_messages` e `orbita_telegram_updates` presentes.
- SHA-256, NTFS ACL e catálogo do dump aprovado. **Não houve restauração real.**

## Diagnóstico

O `pg_ctl -w start` espera por indicação de prontidão durante a
inicialização; esse sucesso **não garante que a instância continue
ativa após o término de outro processo**. No Windows há peculiaridades
na relação entre console/processos de background; fechamento de console
ou sinais podem afetar o processo PostgreSQL, mas **não atribuir causa
sem evidência local do log**.

A saída recebida pode resultar de desligamento imediato do postmaster,
encerramento de sessão/processo, falha operacional ou diferença de
identidade do processo. Evitar inferir causa sem diagnóstico.

**Não executar `-Initialize`, `-Start`, `pg_restore` novamente.**
Nunca alterar o serviço original `postgresql-x64-17` na porta 5432.

### Comando seguro para esclarecer o encerramento

```powershell
cd "$HOME\orbita"
git pull --ff-only origin feat/supabase-auth-protected-panel
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_diagnose.ps1
```

O script exige marcador/ACL privada do ORBITA e:
- Executa somente `pg_ctl status` (leitura, não usa senhas).
- Consulta listeners em `55432` sem se conectar a eles.
- Inspeciona **somente localmente** as últimas 300 linhas de
  `$HOME\orbita-restore-sandbox\server.log`.
- **Não mostra nenhuma linha real do log**, nome, IP de cliente, SQL,
  email, token, hostname, path de backup ou credencial.
- Retorna apenas categorias para eventos reconhecidos:
  pronto para conexões, solicitação de desligamento, banco encerrado,
  exceção de processo, falha fatal/panic, acesso negado, configuração
  inválida ou falha de escuta.
- Sugere hipóteses, nunca uma causa definitiva apenas por `pg_ctl`.

A CI executa `-SelfTest` com frases sintéticas; **não** lê dump ou
logs privados nem inicializa ou encerra servidores.

### Próxima decisão técnica

Se a sequência indicar `PRONTO_PARA_CONEXOES` seguido de
`SOLICITACAO_DE_DESLIGAMENTO` ou `BANCO_ENCERRADO`, investigar
por que o PostgreSQL recebeu shutdown e testar uma execução interativa
com período de observação ou isolamento de processo, **sem reinstalar**.

Se houver `FATAL`/`PANIC`/acesso negado/configuração inválida,
revisar a causa detalhada **localmente**, sem publicar linhas de log.
Não tentar `pg_restore` até confirmar `CLUSTER ATIVO`, PID e
listener `127.0.0.1:55432` por verificador existente 3.37.

### Estados de liberação

| Controle | Estado |
| --- | --- |
| Backup .dump privado e íntegro | APROVADO |
| TOC mínimo 4 tabelas, 599 entradas | APROVADO |
| Cluster sandbox criado, identidade/ACL | APROVADO |
| Persistência do servidor após start | **FALHOU / PENDENTE** |
| Restore de dados | NÃO EXECUTADO |
| Supabase Auth/RLS/API | NÃO TESTADO |
| Migrações 002/003, main, Vercel, Telegram | BLOQUEADOS |

Fontes:
- [PostgreSQL 17: pg_ctl startup, status e logging](https://www.postgresql.org/docs/17/app-pg-ctl.html)
- [PostgreSQL bug 18958: console Windows e encerramento de servidor (caso contextual, não diagnóstico do ORBITA)](https://www.postgresql.org/message-id/18958-e398048dd0cdad11%40postgresql.org)
