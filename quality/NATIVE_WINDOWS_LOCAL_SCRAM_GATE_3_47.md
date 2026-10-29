# ORBITA — Aurora 3.47 | Autenticacao SCRAM somente no PostgreSQL isolado

## Ponto de partida (28/10/2026)

- Identidade e isolamento do sandbox PostgreSQL 17: aprovados.
- Estabilidade de 60 segundos: tres amostras `ATIVO_ISOLADO`.
- Segunda janela PowerShell e outras duas verificacoes de PID/listener, separadas por 60 segundos: aprovadas.
- Encerramento da janela originalmente usada para iniciar o servidor **nao confirmado explicitamente** pelo operador, portanto sua independencia apos fechar o console ainda e condicional.
- Aurora 3.46: `pg_isready` local em `127.0.0.1:55432` esta implementado, integrado e aprovado em CI, mas **AINDA NAO EXECUTADO no Windows do operador**.
- Backup e TOC validados anteriormente, **nao restaurados**. Nenhuma tabela importada.

## O que este gate resolve

`pg_isready` confirma que um servidor aceita conexoes sem testar credenciais. O gate 3.47 comprovara, **somente quando expressamente autorizado**, que a senha local `orbita_restore_admin` autentica no PostgreSQL isolado em `127.0.0.1:55432`.

Isto **nao comprova** Supabase Auth, JWT, RLS, roles do Supabase ou compatibilidade de `pg_restore`. O cluster Windows do ORBITA e um PostgreSQL nativo isolado, nao uma instancia completa do Supabase.

## Implementacao

Script `quality/private_restore_native_windows_local_auth.ps1`:

- `-SelfTest`: somente simula resultados e gates em memoria; nao abre rede, nao le log, nao pede senha.
- `-ProbeAuth -ConfirmLocalCluster ORBITA-ISOLATED-55432`: opt-in explicito do operador, com token de confirmacao literal.
- Antes de solicitar a senha, **executa a Aurora 3.46 `-Check`** e exige as tres linhas de identidade, `PG_ISREADY: ACEITANDO_CONEXOES` e `GATE: PRONTIDAO_TCP_APROVADA`; caso contrario, interrompe sem prompt.
- A senha e lida localmente com `Read-Host -AsSecureString`. **Nao copiar a senha ao ChatGPT, GitHub, CI, historico do shell ou arquivos.**
- Para autenticar, usa o binario PG17 conhecido `C:\Program Files\PostgreSQL\17\bin\psql.exe` exclusivamente no banco local `postgres`, usuario `orbita_restore_admin`, host `127.0.0.1` e porta `55432`. Flags `-X -w -q` desabilitam `psqlrc`, prompt adicional e mensagens normais.
- Usa exclusivamente o meta-comando `\conninfo` para estabelecer sessao e verificar o sucesso da conexao **sem executar SQL**. stdout/stderr do filho sao capturados e **nunca exibidos**.
- O segredo e transmitido temporariamente por `PGPASSWORD` no ambiente do **processo filho** via `.NET ProcessStartInfo`. O script limpa sua copia em texto gerenciado e zera o BSTR apos a execucao. **Limitacao de seguranca:** durante a operacao, a senha existe transitoriamente em memoria de processos; codigo gerenciado nao garante limpeza fisica de todas as copias. Um administrador local ou processo com privilegios elevados pode acessar recursos desses processos. Por isso, usar apenas na maquina confiavel do operador com senha de sandbox, NUNCA senha do Supabase de producao. Nao persiste senha em disco, scripts ou argumentos de linha de comando.
- O resultado e **apenas** `AUTENTICACAO: LOCAL_SCRAM_APROVADA` e `GATE: IDENTIDADE_TCP_E_LOGIN_LOCAL_APROVADOS`, ou uma categoria fixa de falha. O verificador de isolamento e prontidao e executado mais uma vez apos a conexao.
- Nao cria usuarios, tabelas, bancos, regras, servicos nem tarefas; nao faz `pg_restore`, SQL ou migrations. Nao executa `-Start` nem `-Stop`.

### Avisos para portabilidade

O inicio local via `pg_ctl` ja foi aprovado com a Aurora 3.44; o wrapper 3.45 corrigiu um falso-negativo na espera de pipes. **Nunca** repetir inicializacao enquanto o cluster estiver ativo. O gate 3.47 nao precisa iniciar nenhum PostgreSQL.

## Execucao futura — SOMENTE quando estiver no Windows

**Agora, no celular, nao ha nenhuma acao.** A CI deve passar antes de instalar este gate na homologacao.

Na estacao Windows, com `RemoteSigned` permitido e sem alterar a politica permanente:

```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Existem alteracoes locais." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "Falha no pull." }

powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_readiness.ps1" -SelfTest
if ($LASTEXITCODE -ne 0) { throw "Autoteste 3.46 falhou." }

powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_readiness.ps1" -Check
```

**Somente** se o retorno mostrar `PRONTIDAO_TCP_APROVADA` e o operador decidir realizar autenticacao local (sem arquivos nem SQL):

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_local_auth.ps1" -SelfTest
if ($LASTEXITCODE -ne 0) { throw "Autoteste 3.47 falhou." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_local_auth.ps1" -ProbeAuth -ConfirmLocalCluster ORBITA-ISOLATED-55432
```

A senha a digitar e a **criada durante o initdb do sandbox**, nao senha do Supabase real, de servicos de producao ou do GitHub. Nunca compartilhar o prompt com a senha em capturas de tela. Divulgar somente as saidas de status categorizadas.

Se o teste falhar ou ficar inconclusivo, **nao repetir automaticamente** nem tentar adivinhar a senha. Uma falha do wrapper nao autoriza restart. Nao diagnosticar divulgando stderr do `psql`.

## Gates futuros distintos

1. **Pendente de evidencias locais:** 3.46 `pg_isready` retorna `ACEITANDO_CONEXOES`.
2. **Pendente de evidencia local:** 3.47 autentica conta administrativa exclusiva do sandbox, sem SQL.
3. **Pendente de analise de compatibilidade:** roles/privilegios Supabase, extensoes, Ownerships, Auth, RLS, migracoes SQL 002/003 e recuperabilidade de 42 objetos `TABLE DATA`.
4. **Pendente de autorizacao exclusiva:** restauracao em destino isolado e descartavel, com plano de seguranca, rollback, inventario/pos-verificacao e testes funcionais. Nenhuma restauracao habilitada por estes gates.

**Proibido:** alterar o servico `postgresql-x64-17` em `5432`, realizar `pg_restore`, SQL 002/003, deploy `main`, Vercel ou Telegram.
