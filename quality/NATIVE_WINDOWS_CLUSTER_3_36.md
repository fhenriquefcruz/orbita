# ORBITA — Aurora 3.36 | Novo PostgreSQL 17 LOCAL, sem Docker/WSL/Linux

**Status:** script disponível em homologação, **não executado no computador do operador**.
**Backup original:** validado por SHA-256, NTFS e TOC; **recuperabilidade não comprovada**.

## Por que um segundo cluster?

O Windows já possui `postgresql-x64-17` em execução, escutando
`0.0.0.0:5432` e `[::]:5432`. Esse servidor preexistente nunca deve
ser utilizado como alvo de `pg_restore`, mesmo que permita criar bancos
individuais. Não alterar sua configuração, serviço ou autenticação.

O procedimento 3.36 cria um **cluster independente** do serviço antigo:

| Propriedade | Segundo cluster ORBITA |
| --- | --- |
| Diretório | `$HOME\orbita-restore-sandbox\data` (fora do Git) |
| Porta | `55432`, se livre |
| Interface de rede | **`127.0.0.1` apenas** |
| Usuário bootstrap | `orbita_restore_admin` |
| Autenticação | SCRAM-SHA-256 |
| Senha | nova, digitada duas vezes pelo operador no `initdb --pwprompt`; nunca em arquivo, histórico ou chat |
| Evidências | logs privados dentro da pasta do sandbox |
| Banco principal | `postgresql-x64-17` em 5432 **intocado** |

O script tem quatro modos: `-Check` (padrão, leitura somente),
`-Initialize` (inicialização), `-Start` e `-Stop`. Apenas os três
últimos exigem `-ConfirmLocalCluster ORBITA-ISOLATED-55432`.

### 1. Atualizar e verificar SEM modificar nada

```powershell
cd "$HOME\orbita"
git pull --ff-only origin feat/supabase-auth-protected-panel
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_cluster.ps1 -Check
```

A saída de `-Check` indica binários, ocupação da porta 55432 e existência
do sandbox. **Nenhum arquivo será criado no modo -Check.**

### 2. Inicializar somente depois de conferir o diagnóstico

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_cluster.ps1 -Initialize -ConfirmLocalCluster ORBITA-ISOLATED-55432
```

**Mudança local explícita:** cria pasta privada NTFS fora do Git e usa
`initdb` para inicializar um PostgreSQL 17 **novo e vazio**.
Solicita uma senha **nova e diferente da senha Supabase de produção**.
Não compartilhe a senha. Não inicia o servidor nem copia/restaura o dump.

Se `initdb` falhar ou a pasta existir, o programa **não sobrescreve** nem
apaga dados. Investigar localmente antes de novas tentativas.

### 3. Iniciar a nova instância, com confirmação

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_cluster.ps1 -Start -ConfirmLocalCluster ORBITA-ISOLATED-55432
```

O programa confere o marcador de identificação próprio, versão 17, ACL,
`postgresql.conf`, `pg_hba.conf`, porta livre e depois inicia com
`pg_ctl` apontando **somente** para o diretório exclusivo. Depois confere
que `55432` aceita conexão apenas em `127.0.0.1`.

**Se houver erro na inicialização:** não altere o PostgreSQL 5432,
não publique `server.log` nem faça `pg_restore`. Peça revisão técnica
pela mensagem de erro **sem informações privadas**.

### 4. Para encerrar o servidor de ensaio

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_native_windows_cluster.ps1 -Stop -ConfirmLocalCluster ORBITA-ISOLATED-55432
```

O `-Stop` atua **somente** no diretório identificado do sandbox, sem
parar ou reiniciar o serviço Windows existente.

## O que NÃO está feito

- O arquivo `.dump` original **não** é restaurado nesta fase.
- Um dump custom feito por `pg_dump` sobre Supabase pode incluir objetos
  Auth, extensões, papéis reservados e dependências incompatíveis com
  PostgreSQL padrão. Não assumir que um simples `pg_restore` terá sucesso.
- Um ensaio de restauração e de integridade de dados do ORBITA será planejado
  posteriormente contra `127.0.0.1:55432`, com destino/versões verificados
  e sem ignorar erros. Em caso de incompatibilidade, corrigir o procedimento
  ou gerar export filtrado oficial; **não** declarar sucesso.
- Mesmo com recuperação PostgreSQL, **Supabase Auth (GoTrue), API, RLS
  funcional e serviços adicionais** exigem testes próprios em ambiente
  compatível. O cluster nativo não os reproduz.
- SQL novas `002_action_proposals.sql`, `003_telegram_delivery.sql`,
  release de produção `main`, Vercel, webhook e flags ficam bloqueados.

**Política de privacidade:** não copiar dumps, manifestos, logs com dados,
senhas ou tokens para GitHub, chat, arquivos públicos ou Vercel.

Documentação oficial utilizada:
- [PostgreSQL 17 — initdb](https://www.postgresql.org/docs/17/app-initdb.html)
- [PostgreSQL 17 — pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html)
- [PostgreSQL 17 — pg_hba.conf e SCRAM](https://www.postgresql.org/docs/17/auth-pg-hba-conf.html)
- [PostgreSQL 17 — listen_addresses / port](https://www.postgresql.org/docs/17/runtime-config-connection.html)
- [Supabase — restauração entre instâncias](https://supabase.com/docs/guides/self-hosting/restore-from-platform)
