# ORBITA — Aurora 3.33 | Backup íntegro, restauração ainda bloqueada

**Data:** 27/10/2026 • **Ambiente de homologação** • **Projeto de origem:** `tbqfymedgdsdrgkqmuni`.

## Evidência local do titular

Depois de diagnosticar falha de saída TCP 5432 na rede Wi-Fi anterior, a
conectividade do Session pooler do ORBITA foi comprovada com hotspot próprio
(`TcpTestSucceeded: True`). O titular informou que executou localmente
`quality/verify_database_backup_windows.ps1` com manifesto privado, obtendo:

```text
APROVADO - integridade, hash SHA256, ACLs e catalogo conferidos.
RESTAURACAO NAO TESTADA - SQL 002/003 continuam bloqueadas.
```

**Interpretação restrita:** o script local conseguiu ler e validar o dump
custom format e a integridade do catálogo, incluindo `auth.users`,
`public.orbita_records`, `public.orbita_chat_messages` e
`public.orbita_telegram_updates`. O caminho, hash, tamanho, conteúdo
e senhas do arquivo **não foram publicados** no Git ou no chat.

Isto **não prova ainda** restauração, recuperação de RLS, roles,
extensões, Auth em funcionamento nem consistência funcional dos dados.

## Próximo comando: inventário seguro do PC

Executar na branch de homologação atualizada do computador Windows:

```powershell
cd "$HOME\orbita"
git switch feat/supabase-auth-protected-panel
git pull --ff-only origin feat/supabase-auth-protected-panel
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\quality\private_restore_preflight_windows.ps1
```

O preflight **não tenta restaurar** e não executa SQL. Ele valida novamente
o manifesto privado, identifica `pg_restore` e `psql` 17+,
`docker.exe` e Docker Engine, e presença de Supabase CLI. Se o arquivo
não estiver na pasta padrão, usar `-ManifestPath` com caminho **local**.
Não compartilhar manifesto nem dump.

## Por que o local de restauração precisa ser escolhido com cuidado

O backup existente foi produzido com **`pg_dump` convencional** em formato
custom. Ele pode conter objetos internos do Supabase e referir roles,
Auth, extensões e privilégios que **não existem em um PostgreSQL comum**.
Não confundir "catálogo legível" com "restauração recuperável".

Segundo a documentação oficial do Supabase, para migrar entre instâncias
é possível gerar exports separados de **roles, schema e data** usando a
Supabase CLI, que aplica filtros específicos; o `pg_dump` convencional
inclui objetos internos e pode causar erros de permissões na restauração.

O comando `supabase db start --from-backup` é documentado para **outro
tipo de backup de cluster baixado da plataforma**. **Não** invocá-lo
para o arquivo `.dump` custom desta aplicação sem compatibilidade
documentada e comprovada.

## Gate de ensaio real (ainda PENDENTE)

1. Determinar se Docker Desktop/Engine, Supabase CLI, `psql` e `pg_restore`
   são utilizáveis no Windows. Não instalar nada com privilégios sem revisar.
2. Provisionar instância **local isolada**, idealmente no ambiente Supabase
   compatível e com endpoint **restrito a loopback**; nunca apontar variáveis
   de restauração para `*.supabase.co`.
3. Projetar restore compatível do arquivo `.dump`: roles, schema `auth`,
   extensões, constraints e dados. Se houver incompatibilidade, preparar
   export adicional específico (roles/schema/data) e novo ensaio local;
   não fingir sucesso usando `--clean`, `--if-exists` ou ignorando erros.
4. Restaurar somente no destino **descartável/local** conferido, guardar
   logs privados, e confirmar `pg_restore` com exit code 0 e sem falhas
   em objetos essenciais.
5. Validar número de linhas de `auth.users`, três tabelas `orbita_*`,
   chaves/constraints, RLS e capacidade de ler dados corretamente em
   contexto autorizado; executar testes HTTP da Auth **apenas no destino
   isolado**, nunca com tokens/segredos reais publicados.
6. Só depois registrar **RESTAURAÇÃO APROVADA** e discutir separadamente
   aplicação das novas SQLs em ambiente real.

### Limites obrigatórios

- **Produção:** `main`, banco ORBITA, Vercel e webhook inalterados.
- **SQL novas:** `002_action_proposals.sql` e
  `003_telegram_delivery.sql` **não aplicadas**.
- **Flags:** `ORBITA_NATURAL_ACTIONS_ENABLED=0` e
  `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED=0` até aprovação específica.
- **Confidencialidade:** Auth e memória pessoal estão dentro do dump.
  Manter arquivo privado fora do Git, em disco criptografado quando
  possível; não anexar à conversa, issues, Vercel ou armazenamento público.

### Referências oficiais

- [Supabase: conectar ao PostgreSQL](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supabase: restaurar em instância self-hosted](https://supabase.com/docs/guides/self-hosting/restore-from-platform)
- [Supabase: restaurar *backup de cluster* localmente — formato distinto](https://supabase.com/docs/guides/local-development/restoring-downloaded-backup)
- [Supabase: backups do plano Free](https://supabase.com/docs/guides/platform/backups)

**Estado final desta fase:** ARQUIVO ÍNTEGRO; RECUPERABILIDADE AINDA NÃO COMPROVADA.
