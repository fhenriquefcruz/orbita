# ORBITA Aurora 3.46 — Portao de prontidao TCP sem login nem SQL

## Evidencia de estabilidade

Em 28/10/2026, apos a inicializacao sem console (Aurora 3.44), o verificador de identidade (3.37) observou repetidamente:
- marcador do sandbox ORBITA, versao PostgreSQL 17, ACL e configuracao de rede aprovadas;
- PID do postmaster compativel com um listener exclusivo `127.0.0.1:55432`;
- tres amostras positivas no observador 3.43 ao longo de 60 segundos;
- nova dupla de verificacoes positivas separadas por `Start-Sleep -Seconds 60`.

A evidencia textual **nao confirma explicitamente** que a janela de origem foi fechada. Portanto a persistencia apos o fechamento desse console e **condicional**, nao fato confirmado.

O banco continua sem restauracao, sem SQL e sem autenticacao exercitada. O servico PostgreSQL principal em `5432` permanece intocado.

## Proxima pergunta tecnicamente relevante

Uma porta TCP estar ouvindo e um PID valido **nao garantem** que o processo aceite novas conexoes PostgreSQL. O diagnostico `pg_isready` verifica precisamente o estado de prontidao do protocolo, com os retornos documentados:
- `0`: servidor aceitando conexoes;
- `1`: servidor recusando conexoes;
- `2`: sem resposta;
- `3`: parametros invalidos.

A consulta `pg_isready` **nao valida senha nem a autenticacao e nao executa SQL**. Para evitar registros de conexao incorreta, o script informa `-U orbita_restore_admin -d postgres`, usuario inicial do sandbox e banco padrao do PostgreSQL. O `-q` suprime qualquer texto do utilitario, e apenas o codigo de status e publicado por categorias fixas.

Referencia: [PostgreSQL 17 — pg_isready](https://www.postgresql.org/docs/17/app-pg-isready.html).

## Implementacao

O script `quality/private_restore_native_windows_readiness.ps1`:
1. Em `-SelfTest`, trabalha exclusivamente em memoria e testa identidade de forma sintetica e os quatro codigos oficiais (alem de erro desconhecido). Nenhum arquivo privado, banco ou rede.
2. Em `-Check`, recusa executar em outro sistema operacional. Exige verificador versionado e binario exato do PostgreSQL 17 no caminho esperado, ambos sem junctions/symlinks.
3. Antes do teste TCP, exige resultado completo da Aurora 3.37: ACL/config/identidade validadas, postmaster ativo e listener exclusivo `127.0.0.1:55432`. Em falha, interrompe sem conexao.
4. Executa **uma unica chamada** `pg_isready -h 127.0.0.1 -p 55432 -U orbita_restore_admin -d postgres -q -t 3`, com stdout/stderr descartados.
5. Retorna apenas `PG_ISREADY: ACEITANDO_CONEXOES` ou outra categoria fixa e o gate `PRONTIDAO_TCP_APROVADA`/nao aprovada. Nunca publica mensagem de servidor, nome de usuario, senha, SQL nem log.
6. **Nao executa** `-Start`, `-Stop`, `-StartDetached`, `psql`, `pg_restore`, migrações ou deploy.

## Como executar (apos CI e merge na homologacao)

Na janela PowerShell que ja esta aberta, SEM repetir start:

```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Alteracoes locais; nao atualizar." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "git pull falhou." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_readiness.ps1" -SelfTest
if ($LASTEXITCODE -ne 0) { throw "Autoteste falhou." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_readiness.ps1" -Check
```

Se `PG_ISREADY: ACEITANDO_CONEXOES` e `GATE: PRONTIDAO_TCP_APROVADA`, teremos identificado um servidor ativo **e** aceitando conexoes naquele instante. Isso **NAO aprova automaticamente** restore, senhas ou RLS.

Se retornar qualquer outro codigo, parar, nao reiniciar, nao executar login/SQL ou restore. Devolver somente as saidas sanitizadas.

## Fronteiras preservadas

- `main`, produção, Vercel, Telegram, Supabase e PostgreSQL `postgresql-x64-17` em porta 5432 nao sao alvos.
- Backup real `.dump` e catalogo SHA previamente verificados, mas ainda **sem restore**.
- SQL 002/003 e qualquer importacao permanecem bloqueados.
- Proxima etapa a ser aprovada separadamente: autenticacao controlada para o banco privado, com verificacao de credenciais sem exibicao, e depois desenho do procedimento de restauracao com rollback.
