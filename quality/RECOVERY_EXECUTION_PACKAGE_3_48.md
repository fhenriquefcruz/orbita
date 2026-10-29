# ORBITA | Plano executivo de recuperacao isolada — Aurora 3.48

## Objetivo e decisao de arquitetura

Substituir a sequencia de pequenos diagnósticos por **um pacote consolidado de preflight**, seguido de gates funcionais distintos. A recuperacao **nao deve ser executada** com base apenas em SHA256, `pg_isready`, login SCRAM ou inventario do TOC.

O backup privado provem de Supabase; o destino Windows ja inicializado e um PostgreSQL 17 **nativo**, nao um projeto Supabase local completo. A equivalencia entre os dois ambientes exige revisar extensoes, roles e schemas gerenciados, ownership, objetos privilegiados, politicas RLS e dependencias de Auth/Storage/Realtime. Um `pg_restore` bem-sucedido em parte nao comprova funcionamento do sistema.

**Risco especial:** a documentacao PostgreSQL alerta que restaurar um dump de origem confiavel apenas a nivel de backup nao significa executar SQL seguro; o dump pode conter SQL/codigo arbitrario sob privilegios do destino. Antes de executar restore, inspecionar e limitar o destino e privilegios, sem publicar SQL/dados privados em GitHub ou chat.

## Evidencia disponivel

| Componente | Evidencia / estado | Gate |
|---|---|---|
| Backup privado | hash SHA256, ACL e manifesto anteriormente conferidos | validado historicamente, necessita reconfirmacao no dia do restore |
| TOC anterior | 599 objetos; 42 TABLE DATA; 7 POLICY; 9 SCHEMA | apenas inventario |
| Sandbox Windows | PostgreSQL 17, marcador, ACL e rede `127.0.0.1:55432` | aprovado |
| Persistencia curta | 3 amostras `ATIVO_ISOLADO` em 60 s | aprovado |
| Verificacao em outro processo | PID/listener exclusivo confirmados | aprovado |
| Duas leituras adicionais com intervalo de 60 s | `CLUSTER ATIVO` nas duas | aprovado |
| Fechamento do console de origem | nao consta confirmacao explicita | pendente/condicional |
| Aurora 3.46 `pg_isready` em Windows do operador | codigo integrado, nenhuma saida real ainda | pendente |
| Aurora 3.47 senha SCRAM local | codigo integrado, nenhuma saida real ainda | pendente |
| Auditoria de compatibilidade de roles/extensoes | matriz offline nesta PR; dados reais ainda nao lidos | pendente |
| SQL de negocio / integridade recuperada | nao realizado | bloqueado |
| Supabase Auth, JWT e RLS na recuperacao | nao realizado | bloqueado |
| Operacoes `main`, deploy, Telegram | nao autorizadas | bloqueado |

## Novas entregas neste pacote

### A. Matriz de compatibilidade do arquivo

O script existente `quality/private_restore_archive_inventory_windows.ps1` passa a classificar, em memoria, apenas **quantidades e categorias** do TOC do `pg_restore --list`:
- tipos `EXTENSION`, `ACL`, `DEFAULT ACL`, `POLICY`, `ROW SECURITY`;
- `FUNCTION/PROCEDURE`, `TRIGGER/EVENT TRIGGER`, `FOREIGN*`, `PUBLICATION/SUBSCRIPTION`;
- `SEQUENCE SET`, `BLOB/BLOBS`;
- presenca agregada de objetos em schemas administrados tipicamente pelo Supabase, sem divulgar quais objetos sao;
- major version de origem `POSTGRES_17` / `OUTRO_MAJOR` / `NAO_INFORMADO`, sem divulgar string bruta da origem.

A matriz **nao classifica** nomes de owners ou funcoes do dump como seguros. Dados de roles/GRANT/SECURITY DEFINER ainda exigem revisao sob ambiente privado, e a presenca de objetos no TOC nao prova que eles possam ser criados ou executados no destino.

### B. Painel de gates em uma unica execucao

`quality/private_restore_readiness_summary_windows.ps1`:

- `-SelfTest`: dados artificiais e nenhuma conexao.
- `-Check`: executa a Aurora 3.46 para observar protocolo TCP somente no sandbox validado e executa o inventario 3.37/3.48, que revalida assinatura SHA256, ACL do backup e TOC offline.
- Nunca solicita senha, executa SQL, altera servidor, configura servico, inicia processo PostgreSQL ou chama `pg_restore` com `-d` ou `--dbname`.
- Filtra a saida das ferramentas: imprime apenas `CLUSTER_TCP`, `ARQUIVO_BACKUP`, proximas fases e bloqueios. Em erro de qualquer subetapa, devolve `NAO_DEMONSTRADO` sem expor dados nem traces.
- **Nao declara a compatibilidade aprovada.** O modelo de risco, se necessario, pode ser consultado separadamente no inventario existente.

### C. Gates por criterio, nao por numero de "Auroras"

Apos os preparos acima e sem reiniciar o PostgreSQL:

1. **Prontidao consolidada:** `CLUSTER_TCP: PRONTIDAO_TCP_APROVADA` e `ARQUIVO_BACKUP: HASH_ACL_TOC_VERIFICADOS`. Ainda nao e autorizacao de restore.
2. **Credencial local opcional:** operador autoriza executar 3.47, digita apenas senha isolada com entrada oculta, e obtem `GATE: IDENTIDADE_TCP_E_LOGIN_LOCAL_APROVADOS.` Nunca usar credenciais do Supabase de producao.
3. **Analise da matriz real:** contar extensoes, ACLs, policies, schema gerenciado, versionamento e objetos de codigo. Se houver dependencia ausente ou papel/owner incompativel, classificar como **bloqueador de recuperacao nativa** e preparar procedimento especifico; nao tentar `pg_restore` por tentativa e erro.
4. **Modelo de destino:** avaliar restauracao em **banco novo e descartavel** dentro do cluster privado, criado de `template0` apenas apos autorizacao especifica. Nao tocar no banco `postgres`, nem no servico principal da porta 5432. Nome/role/ACL do banco de destino precisam ser revisados em manifesto separado antes de comandos capazes de escrever.
5. **Previsao de objetos e codigo:** documentar como roles, ACL, ownership, RLS, extensoes e dependencias dos schemas Supabase serao tratadas; revisar scripts executados pelo restore para evitar SQL inseguro. Evitar `--clean`, `--create` e `--disable-triggers` sem analise formal.
6. **Restauracao (NAO IMPLEMENTADA):** somente sob confirmacao expressa, alvo isolado, backup SHA reconfirmado, registro sanitizado de resultado, erro => abortar e nao auto-repetir; planejar rollback por descarte do banco de teste.
7. **Aceitacao funcional:** objetos esperados presentes, contagens seguras, FK/constraints, sequencias, queries de smoke apenas no destino privado, testes das operacoes ORBITA e evidencias de Auth/JWT/RLS na infraestrutura apropriada. A aprovacao do banco nativo, sozinha, nunca libera Supabase Auth ou producao.

## Proxima execucao quando houver PC Windows

**Um unico bloco**, sem senha, sem SQL e sem restore:

```powershell
cd "$HOME\orbita"
if ((git branch --show-current).Trim() -ne "feat/supabase-auth-protected-panel") { throw "Branch incorreta." }
if (@(git status --porcelain).Count -gt 0) { throw "Alteracoes locais, abortar." }
git pull --ff-only origin feat/supabase-auth-protected-panel
if ($LASTEXITCODE -ne 0) { throw "Atualizacao falhou." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_readiness_summary_windows.ps1" -SelfTest
if ($LASTEXITCODE -ne 0) { throw "Autoteste falhou." }
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_readiness_summary_windows.ps1" -Check
```

Para consultar a matriz detalhada de riscos (somente contagens), e **somente se necessario**:
```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_archive_inventory_windows.ps1"
```

**Nenhum comando de inicializacao**; se a prontidao nao estiver comprovada, parar. Se o hash/TOC nao passar, parar. Nao compartilhar backup, SQL, manifestos, logs ou senhas.

## Criterios de definicao de pronto (Definition of Done)

- [x] Scripts de verificacao isolada e monitoramento passivo versionados
- [x] Cluster observado ativo em outra janela, em verificacoes sucessivas
- [x] Aurora 3.46 e 3.47 implementadas com testes sinteticos no Windows CI
- [x] Matriz de compatibilidade offline e painel consolidado implementados neste pacote
- [ ] Aurora 3.48 `-Check` executada **localmente** e sem erros
- [ ] Gate 3.47 autorizado/executado com senha local (se necessario)
- [ ] Extensoes/roles/ownership/RLS revisados para o destino nativo
- [ ] Plano de banco descartavel e rollback aprovado
- [ ] Restauracao de teste autorizada e efetivamente realizada (nao antes)
- [ ] Checks funcionais sem exposicao de dados
- [ ] Auth/JWT/RLS Supabase comprovados em homologacao apropriada
- [ ] Liberacao posterior de producao por procedimento independente

**Nao misturar validacao PostgreSQL nativa com migracoes de Supabase, deploy de aplicativo ou WhatsApp/Telegram.**

Referencias oficiais: [PostgreSQL 17 — pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html), [PostgreSQL 17 — pg_isready](https://www.postgresql.org/docs/17/app-pg-isready.html).
