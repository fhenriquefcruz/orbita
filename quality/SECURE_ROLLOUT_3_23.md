# ORBITA Aurora 3.23 — Verificação de acesso e condição de backup

## Ensaio PostgreSQL executado em 24/10/2026

Executei no projeto Supabase **exclusivo ORBITA** o conteúdo exato de
`infra/supabase/rls_role_rehearsal.sql`. Todos os seis campos do objeto
`rls_access_evidence` retornaram `true`:

| Verificação | Evidência |
| --- | --- |
| Papel `authenticated` simulando proprietário | Conseguiu enxergar ao menos seu registro |
| Papel `authenticated` simulando UUID não proprietário | Nenhum registro de terceiro foi exibido |
| Papel `authenticated` simulando UUID não proprietário | Nenhuma mensagem de chat foi exibida |
| Fila interna `orbita_telegram_updates` | Sem SELECT para o papel authenticated |
| Papel `anon` | Sem SELECT em registros, chat ou atualizações do Telegram |
| Leitura do chat do proprietário | Consulta executada sem erro; zero ou mais resultados |

A execução começou com `BEGIN`, mudou papéis com `SET LOCAL ROLE`
e definiu claims transitórias `request.jwt.claim.sub` apenas na sessão;
terminou em `ROLLBACK`. Nenhuma gravação, alteração de login, token ou
migração foi efetuada.

**Limite importante:** esta é uma prova de políticas PostgreSQL, **não** um
teste com duas contas reais pelo endpoint HTTP do Supabase Auth. A fase HTTP,
incluindo login, expiração/refresh, recuperação de senha, escrita e exclusão
entre contas, continua pendente e deve ocorrer antes de publicar.

## Como reproduzir

Execute somente no SQL Editor do projeto ORBITA:

`infra/supabase/rls_role_rehearsal.sql`

O arquivo produz um JSON `rls_access_evidence`, sem UUID, títulos, nomes,
e-mail ou conteúdos de mensagens. Salve apenas esse JSON em arquivo local
para avaliação opcional:

```bash
python quality/verify_rls_role_report.py resultado-rls.json
```

Códigos de saída: `0` = seis verificações aprovadas, `1` = alguma
falhou, `2` = estrutura JSON inválida ou incompleta. **Mesmo o código 0
não autoriza publicação**, pois as sessões HTTP reais e o backup ainda
não foram validados.

## Backup — bloqueador para alterações permanentes

Antes de executar as migrações 002 e 003 **definitivamente**:

1. Confirmar o plano do Supabase e uma cópia recuperável de data recente.
   Consulte Database → Backups no projeto; não pressupor que exista backup
   automático no plano gratuito.
2. Se o projeto não possuir backups recuperáveis, produzir um dump lógico
   privado da base com ferramentas oficiais (`supabase db dump` ou `pg_dump`)
   e armazenar fora do repositório. O backup deve preservar esquema, políticas,
   dados e as configurações necessárias para reconstruir o ambiente.
3. Testar ao menos a leitura do dump e preparar um procedimento de restauração
   antes de considerar o banco recuperável. Proteger o arquivo como dado
   confidencial: **não fazer commit, anexar a issues nem colar no chat.**
4. Registrar o ponto de recuperação e obter autorização específica para a
   mudança persistente. Não mesclar a PR principal na `main` por efeito
   da migração.
5. Revisar SQL 002/003 e aplicar mediante janela controlada, repetir
   `infra/supabase/preflight_readonly.sql` e os advisors. Nunca ativar
   `ORBITA_NATURAL_ACTIONS_ENABLED` ou
   `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED` antes dos respectivos testes
   de segurança e webhook.

**Situação desta etapa:** a conexão disponível permitiu consultas e o ensaio
de `ROLLBACK`, mas **não há ferramenta conectada para gerar e restaurar um
backup oficial verificável do banco**. Portanto, as migrações 002/003 não
foram aplicadas permanentemente nesta entrega.

Documentação oficial:
https://supabase.com/docs/guides/platform/backups

## Outros bloqueios ainda observados

- Security Advisor: **Leaked Password Protection Disabled**. Ver
  https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection
- Testes reais com duas contas Auth separadas, inclusive API PostgREST.
- Login e restauração de sessão em Safari/iPhone e recuperação de senha.
- Entrega da mensagem e callback do Telegram privado após implantação.
- Vercel com limite de builds do plano, sem confirmação de deploy recente.
- Definir política de expiração, alertas e comportamento do webhook antes de
  ligar notificações automáticas; todas permanecem desativadas.

## Evidências de qualidade

- `telegram/tests/test_rls_role_rehearsal.py` cobre nove cenários.
- `quality/verify_rls_role_report.py` rejeita booleans ausentes, tipos falsos
  e falhas de qualquer uma das políticas de acesso.
- O SQL de teste usa papéis transitórios e `ROLLBACK` explícito, não altera
  o banco, não usa chaves e não revela nenhum identificador privado.
- A PR de homologação continua sem autorização de publicação em `main`.

A próxima decisão operacional depende do **backup verificável** e do teste
HTTP com duas contas — não de mais uma simulação do SQL.
