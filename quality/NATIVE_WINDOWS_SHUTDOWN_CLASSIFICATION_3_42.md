# ORBITA Aurora 3.42 — diferenciar desligamento regular de evento no console

## Evidencia recebida (Windows 28/10/2026)

O titular executou Aurora 3.41, com `-SelfTest` aprovado. Log privado `server.log` possui **29 linhas nao vazias, 26 classificadas e seis marcos relevantes**. A ultima sequencia observada foi:

- `POS_20 PRONTIDAO`;
- `POS_27 CHECKPOINT_DESLIGAMENTO`;
- `POS_29 DESLIGAMENTO`;
- `PEDIDO_RECONHECIDO_ENTRE_MARCOS: NAO`.

O estado do cluster foi previamente observado como **PARADO, sem listener em 55432**. O arquivo `postmaster.pid` encontra-se ausente; isso nao demonstra causa da parada.

## Significado tecnico

A mensagem `checkpoint starting: shutdown immediate` **nao equivale a parada imediata/crash**. Ela tambem pode ocorrer durante um encerramento normal ou rapido do PostgreSQL. A ausencia de `PEDIDO_DESLIGAMENTO` no classificador nao prova que uma solicitacao ou sinal nao ocorreu. O log pode reunir varias sessoes.

O comportamento do PostgreSQL 17 em Windows pode ser influenciado por condicoes de controle de console. Em um relato publicado em junho/2025, o fechamento/interrupcao de um `cmd.exe` associado a `pg_ctl` afetou o servidor, mas **nao existe evidencia suficiente para atribuir essa causa ao ORBITA**.

Referencias tecnicas:
- [Documentacao PostgreSQL 17: pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html)
- [Documentacao PostgreSQL 17: tipos de desligamento](https://www.postgresql.org/docs/17/server-shutdown.html)
- [Relato PostgreSQL BUG #18958 (contexto, nao diagnostico)](https://www.postgresql.org/message-id/18958-e398048dd0cdad11%40postgresql.org)

## Melhoria segura na Aurora 3.42

O diagnostico **existente** `quality/private_restore_native_windows_log_evidence.ps1` foi ampliado para reconhecer:
- `LOG: shutting down` como `ENCERRANDO`, alem de `database system is shutting down`;
- indicativo da excecao de console do Windows `0xC000013A` como `EXCECAO_CONSOLE`, com prioridade sobre o caso genérico de excecao de background worker;
- `PROCESSOS_ENCERRADOS`, `PROCESSOS_REINICIANDO` e `RECUPERACAO_APOS_QUEDA`.

A saida mostra apenas uma sequencia sanitizada das ultimas 300 linhas, sem nenhum texto original, nome, usuario, PID, SQL, senha, caminho de arquivo, IP ou timestamp. As categorias existem para orientar a investigacao, **nao para comprovar causalidade**.

O `-SelfTest` agora cobre a forma curta de desligamento, uma fixture com checkpoint normal sem pedido de parada, excecao de console e recuperacao. CI Windows continua testando sintaxe, ACL/identidade e proibição de ações.

## Proxima execucao local — somente apos CI e merge na homologacao

```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Alteracoes locais. Abortando pull." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "Falha no pull." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_log_evidence.ps1" -SelfTest
if ($LASTEXITCODE -ne 0) { throw "Falha no autoteste." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_log_evidence.ps1"
```

## Proximo gate

Com a ordem e classificacao consolidadas, avaliar se existe indicador objetivo de sinal de console. Caso nao exista, o proximo teste util sera uma **inicializacao observada com autorizacao explicita**, validação da porta 55432, PID do postmaster e verificacao posterior na mesma janela — preservando os controles da Aurora 3.37, sem restaurar dados. O procedimento precisara de revisão separada e testes preventivos antes de executar.

**Continuam bloqueados:** `-Initialize`, `-Start` repetido, `pg_restore`, SQL 002/003, quaisquer operacoes sobre 5432 ou o servico `postgresql-x64-17`, deploy para `main`, Vercel e Telegram. A integridade do backup `.dump` nao equivale a restauracao comprovada.
