# ORBITA Aurora 3.44 — hipótese testável: acoplamento ao console Windows

## Diagnóstico consolidado, 28/10/2026

Na tentativa supervisionada (Aurora 3.43), `pg_ctl -w start` informou `servidor iniciado` mas não foram emitidas as mensagens **finais do gerenciador** `CLUSTER INICIADO` e `RESTAURACAO NAO EXECUTADA`. A primeira amostra do verificador foi `PARADO`, e o monitor interrompeu corretamente sem retry.

O log sanitizado **posterior** cresceu de 29 para 42 linhas e acrescentou:
- `POS_32 DESLIGAMENTO` (mensagem de histórico de banco previamente desligado não equivale a shutdown atual);
- `POS_33 PRONTIDAO`;
- `POS_40 CHECKPOINT_DESLIGAMENTO`;
- `POS_42 DESLIGAMENTO`.

Nenhum pedido explícito ou exceção de console foi reconhecido, **o que não prova que tais eventos não ocorreram**. Um checkpoint de shutdown não revela quem enviou a solicitação. Identidade, ACL, rede e porta exclusiva do sandbox já passaram no Gate A.

### Hipótese operacional
O processo `pg_ctl` no console interativo pode estar ligado a eventos de controle do Windows, de modo que a finalização de `pg_ctl` ou sua associação com o console afete o postmaster e/ou interrompa a execução do script. **Ainda não é causa comprovada**. O bug PostgreSQL #18958 descreve cenário semelhante, mas diferente, envolvendo Ctrl-C/console em PostgreSQL 17 no Windows.

Em vez de continuar classificando os mesmos logs, testar **uma única execução de `pg_ctl` sem janela de console**. O objetivo é isolar a variável "console" mantendo **o mesmo cluster, dados, configuração e porta**. Se a hipótese estiver errada, continuar bloqueando restauração, sem tentar outra partida.

## Novo executável controlado

`quality/private_restore_native_windows_detached_start.ps1`:

- `-SelfTest`: apenas dados sintéticos, verificando confirmacao, isolamento de stdout/stderr e classificadores.
- `-StartDetached -ConfirmLocalCluster ORBITA-ISOLATED-55432`: intervenção **explícita e única**; preflight invoca o verificador Aurora 3.37 antes do start e EXIGE identidade aprovada, cluster parado e porta 55432 não ocupada.
- Inicia apenas `C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe` com parâmetros `-D` fixos no sandbox privado, `-l` para `server.log`, `-w -t 30 start`. A API `.NET ProcessStartInfo` usa `CreateNoWindow=true`, `UseShellExecute=false` e redirecionamento de stdout/stderr, que não são exibidos.
- Fixa `PGHOST=127.0.0.1` e `PGPORT=55432` **somente no subprocesso**, não no sistema operacional.
- Verifica saída do `pg_ctl` e, **ainda no script**, reexecuta o verificador 3.37 para comprovar PID e listener exclusivo. Um exit code zero, isoladamente, **não libera nada**.
- Não inicia serviços Windows, não grava configurações, não executa SQL nem restore, não mexe em `postgresql-x64-17`, não modifica porta 5432 e não tem retries. Em timeout, NÃO força kill: status fica inconclusivo e proíbe repetir start.

## Procedimento de teste — somente após CI e merge em homologação

Antes de executar qualquer start:
```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Alteracoes locais; abortar pull." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "Falha no pull." }
Get-ExecutionPolicy
& ".\quality\private_restore_native_windows_detached_start.ps1" -SelfTest
& ".\quality\private_restore_native_windows_verify.ps1"
```

Exigir `RemoteSigned` (na sessão atual, quando permitido), `AUTOTESTE APROVADO`, `IDENTIDADE: ... aprovados` e `CLUSTER PARADO`. Se qualquer etapa falhar, não executar start. **Não usar `powershell.exe -File` ou `pg_ctl` diretamente.**

Para iniciar o **sandbox** explicitamente, executar **uma vez só**:

```powershell
& ".\quality\private_restore_native_windows_detached_start.ps1" -StartDetached -ConfirmLocalCluster ORBITA-ISOLATED-55432
```

Somente se a saída contiver
`CLUSTER INICIADO: PID confirmado e listener exclusivo 127.0.0.1:55432.`
executar **no mesmo PowerShell aberto**:

```powershell
& ".\quality\private_restore_native_windows_stability.ps1" -Observe
```

Se o start falhar ou o monitor retornar `ESTABILIDADE_NAO_COMPROVADA`, **parar**. Não repetir. Executar somente os diagnósticos de leitura existentes:
```powershell
& ".\quality\private_restore_native_windows_log_evidence.ps1"
& ".\quality\private_restore_native_windows_verify.ps1"
```

**Nenhuma saída bruta do `server.log`, senhas, caminhos privados, SQL ou PID real deve ser compartilhada.** Compartilhar apenas saídas sanitizadas dos scripts.

## Critérios de sucesso

- `pg_ctl` conclui sem interferência aparente no PowerShell e o script emite suas confirmações finais;
- verificação local comprova que o listener é exclusivamente `127.0.0.1:55432` e que o PID pertence ao sandbox;
- observação passiva confirma três amostras `ATIVO_ISOLADO` por 60 s.

Se tudo passar, a próxima etapa será avaliar persistência depois do encerramento da sessão, **ainda sem autorização de restore**. Se falhar, considerar formalmente uma instância Windows service dedicada `ORBITA...` com `-S demand` e ACL apropriada **em uma intervenção separada**, jamais alterar o serviço principal.

## Segurança e liberação

- Backup privado e catálogo/SHAs anteriormente aprovados; recuperação funcional **NÃO EXECUTADA**.
- Migrações SQL 002/003, `main`, produção, Vercel e Telegram **BLOQUEADOS**.
- Nada no PR cria banco, cria Windows service, altera firewall, registra tarefa ou acessa a produção.

Referências:
- [PostgreSQL 17, pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html)
- [PostgreSQL Bug #18958 — Windows console CTRL-C](https://www.postgresql.org/message-id/18958-e398048dd0cdad11%40postgresql.org)
