# ORBITA Aurora 3.39 — esclarecer log sem eventos reconhecidos

## Evidencia real de 28/10/2026

O titular executou `private_restore_native_windows_diagnose.ps1`:

- `AUTOTESTE APROVADO` com frases sinteticas.
- `PG_CTL: servidor declara estar PARADO.`
- `PORTA 55432: SEM LISTENER.`
- `EVENTOS RECONHECIDOS NO LOG: 0`.

**Interpretacao correta:** 0 eventos reconhecidos NAO prova ausencia de linhas. Ainda nao sabemos se o arquivo esta vazio, desatualizado, em outro idioma ou se mensagens foram registradas em outro destino.

## Novo diagnostico somente leitura

`quality/private_restore_native_windows_log_evidence.ps1` verifica apenas o sandbox privado do ORBITA:

1. Marcador, ACL, ausencia de junction/symlink e `PG_VERSION=17`.
2. Presenca, faixa de tamanho e faixa de idade de `server.log` (sem publicar caminho, tamanho preciso, data/hora).
3. Numero de linhas analisadas (ultimas 300), linhas nao vazias e categorias reconhecidas — sem mostrar nenhuma linha.
4. Presenca de `current_logfiles` e `postmaster.pid` sem ler o conteudo desses arquivos.
5. Declaracoes `logging_collector` e `log_destination` do `postgresql.conf`, sem revelar valores nao reconhecidos. **Nao prova a configuracao efetiva** (incluidos overrides).

**O script nao executa** `pg_ctl`, `postgres`, `pg_restore`, SQL, `Get-WinEvent`, acesso ao Supabase, mudanca de configuracao ou operacoes de rede. Nao grava arquivos.

### Executar no PowerShell, somente apos PR/CI

```powershell
cd "$HOME\orbita"
git status --short
git branch --show-current
git pull --ff-only origin feat/supabase-auth-protected-panel
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_log_evidence.ps1" -SelfTest
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\quality\private_restore_native_windows_log_evidence.ps1"
```

**Se houver arquivos locais modificados, ou o branch nao for o de homologacao, nao executar o pull.** Nao copiar conteudos brutos de `server.log` ou `postgresql.conf` para chat, GitHub ou tickets.

## Decisao baseada no resultado

| Evidencia | Interpretacao permitida | Proxima atividade |
| --- | --- | --- |
| `SERVER_LOG ... TAMANHO=VAZIO` | Log de `pg_ctl -l` sem bytes | Avaliar separadamente redirecionamento/logging, sem reiniciar |
| `LINHAS_NAO_VAZIAS>0`, `EVENTOS_CLASSIFICADOS=0` | Ha texto, mas parser nao reconheceu | Avaliar localmente idioma/formatacao; nao inferir causa |
| `ULTIMA_ATUALIZACAO=MAIS_DE_24H` | Arquivo potencialmente antigo | Verificar se eh o log da tentativa recente (sem divulgar timestamp) |
| `CURRENT_LOGFILES: PRESENTE` | Pode existir destino do collector | Investigar so no proprio Windows, sem copiar caminhos |
| `CATEGORIA: FATAL` ou `PANIC` | Mensagem de falha existe | Investigar localmente, sem revelar linha |
| Nenhum sinal conclusivo | Causa nao determinada | Nao repetir start nem restaurar |

## Gates de recuperacao

- Arquivo `.dump`, SHA-256, ACL e catalogo com 599 entradas: aprovados anteriormente.
- Cluster isolado PostgreSQL 17: criado e identidade validada.
- Persistencia do processo apos `pg_ctl start`: **pendente**.
- Recuperacao real, validacao de dados/Auth/RLS: **nao realizada**.
- Migrações SQL 002/003, fusao `main`, Vercel e webhook: **bloqueadas**.

Fonte de comportamento esperado: [PostgreSQL 17, pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html) e [Log de erros PostgreSQL 17](https://www.postgresql.org/docs/17/runtime-config-logging.html).
