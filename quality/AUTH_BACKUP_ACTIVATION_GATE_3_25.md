# ORBITA Aurora 3.25 — Segunda conta Auth e backup privado verificável

## Diagnóstico real em 25/10/2026

Conferências via conexão Supabase autorizada **apenas para leitura**:
- Projeto exclusivo ORBITA, ref `tbqfymedgdsdrgkqmuni`, região São Paulo, ativo.
- Organização ORBITA no plano **Free**.
- **Uma conta Auth**, com e-mail confirmado; segunda conta ainda **não existe**.
- A migração 002 (propostas) e a 003 (entrega Telegram) não foram aplicadas
  permanentemente no Supabase.
- Security Advisor mantém aviso `Leaked Password Protection Disabled`.

A conexão do plugin Supabase **não possui funções para convidar/criar
usuários Auth**, baixar dump completo, consultar um backup oficial ou
executar restauração isolada. Não inserir usuários diretamente nas tabelas
`auth.users` ou `auth.identities`: o fluxo normal do Auth deve gerenciar
credenciais, identidades, sessão e confirmação.

## 1. Preparar a segunda identidade autorizada

<https://supabase.com/dashboard/project/tbqfymedgdsdrgkqmuni/auth/users>

1. No Dashboard, confira **nome ORBITA** e ref
   `tbqfymedgdsdrgkqmuni` antes de qualquer operação.
2. Abra **Authentication → Users** e escolha **Add user / Invite user**
   (o rótulo pode variar). Use **outro e-mail que você controle**, não um
   endereço inventado nem endereço de terceiro. Se uma conta de teste
   adicional for criada, restrinja seu uso à homologação.
3. Conclua o convite ou cadastramento, defina senha forte diferente da
   principal e confirme a conta por fluxo de e-mail oficial, quando exigido.
   Não use link de convite fora dos domínios conhecidos do Supabase e ORBITA.
4. Confira, sem publicar e-mails, que a lista de usuários mostra **duas
   identidades diferentes, confirmadas**, não duas sessões do mesmo usuário.
5. **Não habilite inscrição pública** para facilitar o teste; adicione o
   segundo usuário com controle administrativo. Evite chaves `service_role`
   em navegador, planilhas, Issues, CI ou chat.
6. Após a homologação, revogue sessões e **exclua o usuário de teste quando
   não for mais necessário**, depois de remover qualquer fixture de teste.

Não foi possível completar essa ação pelo plugin disponível; depende de uma
caixa de e-mail de teste legítima e da etapa administrativa no Dashboard.
**Nunca envie a senha, o access token ou o link de convite nesta conversa.**

## 2. Executar login real de duas contas e verificar RLS

O verificador de duas sessões já existe em
`quality/auth_http_rls_probe.py`. Nesta fase foi adicionado
`quality/auth_dual_login_runner.py`, que simplifica o procedimento:
faz login padrão por senha diretamente em
`https://tbqfymedgdsdrgkqmuni.supabase.co/auth/v1/token?grant_type=password`,
mantém access tokens somente na memória do processo e executa em seguida
os mesmos testes GET de RLS da Aurora 3.24.

No computador privado, em terminal seguro, obtenha a **chave publicável**
que já consta de `docs/cloud-config.js` (não use chave secreta).
Insira-a apenas na sessão privada do terminal, preferencialmente via
`read -rs`, e execute:

```bash
export ORBITA_E2E_LOGIN_ACK=I_AUTHORIZE_TWO_LOCAL_AUTH_LOGINS
export ORBITA_E2E_EXPECT_PROJECT=tbqfymedgdsdrgkqmuni
read -rs ORBITA_E2E_PUBLISHABLE_KEY; echo
export ORBITA_E2E_PUBLISHABLE_KEY
python quality/auth_dual_login_runner.py
unset ORBITA_E2E_PUBLISHABLE_KEY
unset ORBITA_E2E_LOGIN_ACK ORBITA_E2E_EXPECT_PROJECT
```

O programa solicita os e-mails e as senhas por terminal local; as senhas
são obtidas por `getpass`, não ficam no histórico do shell, não são
impressas e não são persistidas. O programa envia **duas requisições POST
somente ao endpoint de login do Supabase**, e todo o restante são consultas
HTTP GET. Nunca executa INSERT/UPDATE/DELETE em registros.

**Gate adicional:** a tabela de chat não continha mensagens do titular na
última conferência. O verificador considera prova de chat **pendente** quando
não houver pelo menos uma mensagem real/fixture previamente autorizado.
Não criar dados artificiais para forçar um resultado verde sem preparação
da limpeza/backup.

## 3. Preparar um backup privado no plano Free

Segundo a documentação oficial de backups do Supabase, backups diários
gerenciados são disponibilizados nos planos Pro/Team/Enterprise. No Free,
é recomendado o dump lógico com CLI ou PostgreSQL:

- https://supabase.com/docs/guides/platform/backups
- https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore

**Atenção:** o backup lógico pode conter contas Auth, hashes de senha,
dados financeiros/pessoais, segredos e tokens de banco. **Nunca subir o
arquivo ou manifesto para GitHub/ChatGPT/Drive público, nem anexá-lo à PR.**

No computador confiável com **PostgreSQL 17** (`pg_dump` e `pg_restore`
no PATH), crie um diretório FORA do repositório e com permissão privada:

```bash
mkdir -p "$HOME/orbita-backups-privados"
chmod 700 "$HOME/orbita-backups-privados"

export ORBITA_BACKUP_ACK=I_UNDERSTAND_BACKUP_IS_PRIVATE
export ORBITA_BACKUP_PROJECT=tbqfymedgdsdrgkqmuni
export PGDATABASE=postgres
export PGSSLMODE=require

# Copie APENAS host, usuário e porta mostrados em Connect no projeto ORBITA.
# Prefira Session Pooler; PGUSER deve ser postgres.tbqfymedgdsdrgkqmuni.
# Não copie senha na conversa nem digite connection URI no histórico.
read -r PGHOST
read -r PGUSER
read -r PGPORT
export PGHOST PGUSER PGPORT

read -rs PGPASSWORD; echo
export PGPASSWORD

python quality/private_database_backup.py "$HOME/orbita-backups-privados"

unset PGPASSWORD PGHOST PGUSER PGPORT PGDATABASE PGSSLMODE
unset ORBITA_BACKUP_ACK ORBITA_BACKUP_PROJECT
```

O programa:
- Rejeita outro projeto, outro host, conexão sem TLS, diretório público,
  arquivo já existente, dump vazio ou tabela essencial ausente.
- Executa `pg_dump` em formato custom, SEM comando DML/DDL, num arquivo
  temporário privado 0600 e valida o `pg_restore --list`.
- Exige presença de `auth.users` e das três tabelas base ORBITA com
  seus dados no catálogo, sem exibir linhas nem credenciais.
- Calcula SHA-256 e grava um manifesto JSON privado também 0600.
- **Sempre grava `restore_tested:false` e
  `recoverable_confirmed:false`**. Integridade de dump não basta para
  comprovar uma restauração.

Depois de copiar **o dump e seu manifesto** para armazenamento privado
externo, rode:

```bash
python quality/verify_backup_archive.py   "$HOME/orbita-backups-privados/NOME_DO_MANIFESTO.manifest.json"
```

Isso verifica tamanho, hash e catálogo novamente, sem conectar ao banco.
Proteja também o nome/caminho do arquivo, pois ele contém identificadores
operacionais. Para avançar além da integridade, **restaure em um PostgreSQL
ou projeto Supabase isolado e aprovado** (preferencialmente um ambiente
temporário de testes); depois verifique contagens, papéis, Auth, tabelas,
integridade referencial e capacidade de consulta. Uma restauração para
outro projeto Supabase pode demandar custo e reconfiguração de Auth,
extensões, Storage e segredos. Não criar projeto pago sem aprovação.

Se o dump não puder ser gerado ou restaurado em ambiente isolado, **não
autorizar a aplicação permanente** de SQL 002/003.

## Estado dos gates

| Gate | Situação |
| --- | --- |
| Projeto dedicado ativo e base com RLS | Confirmado |
| Conta proprietária com e-mail confirmado | Confirmado |
| Segunda conta de teste legítima | **Pendente — criada no Dashboard** |
| Prova HTTP com duas contas | **Pendente — aguardando duas sessões** |
| Ferramenta de backup com checks | Implementada, testes em CI |
| Backup privado realmente gerado | **Não executado nesta sessão** |
| Restauração em banco isolado | **Não comprovada** |
| SQL 002/003 aplicado permanentemente | **Bloqueado** |
| Telegram natural e entrega v2 ativos | **Desligados por padrão** |
| Revisão de Auth, Safari, Vercel | Ainda pendente |

A suíte offline desta etapa compreende testes de permissão de destino,
SHA, não exposição de segredo, rejeição de arquivos corrompidos e dois
logins locais simulados. A CI não possui credenciais e jamais executa
um dump/restore na base real.

**A aprovação em CI prova apenas a implementação da ferramenta.
O gate de recuperabilidade permanece vermelho até restauração real.**
