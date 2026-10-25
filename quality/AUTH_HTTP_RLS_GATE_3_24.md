# ORBITA Aurora 3.24 — Teste Auth/RLS HTTP com duas sessões reais

## Propósito e limite de segurança

O teste `quality/auth_http_rls_probe.py` consulta **somente por HTTP GET**
o projeto Supabase exclusivo `orbita`, cujo identificador público é
`tbqfymedgdsdrgkqmuni`. Ele utiliza duas sessões de contas Auth diferentes,
validadas pelo endpoint `/auth/v1/user`, e uma chave **publicável**.
Não utiliza `service_role`, e-mail, senha, refresh token, RPC com efeito,
backup ou credenciais de outros projetos. Não cria, altera nem exclui registros.

**A execução real NÃO ocorreu nesta etapa:** consulta administrativa, apenas
para contagem, confirmou que existe **uma conta Auth** no projeto, mas são
necessárias duas sessões legítimas. A tabela de chat possui **zero mensagens**,
de modo que a proteção do conteúdo do chat ainda não tem uma linha real para
servir de prova. Não inventar sucesso de login ou duas identidades.

## Comportamento do teste

1. Exige opt-in local explícito e correspondência com o projeto exclusivo.
   Variáveis ausentes causam saída 2, sem fazer conexão.
2. Exige dois JWTs de usuário distintos, válidos e devolvendo UUIDs diferentes
   em `GET /auth/v1/user`.
3. Consulta no endpoint PostgREST o registro da conta titular, projetando
   apenas `id,user_id`; a leitura cruzada com o token da outra conta deve
   retornar zero linhas.
4. Consulta o chat da conta titular projetando **somente `user_id`**.
   A outra conta não pode ver essas linhas. Se não houver chat do titular,
   registra **pendência**, nunca aprovação completa.
5. Confirma que a tabela interna `orbita_telegram_updates` nega `GET`
   a ambas as contas e ao visitante anônimo (HTTP 401/403).
6. Confirma que registros não podem ser lidos pelo anônimo.
7. Exige que Auth rejeite um JWT deliberadamente inválido (401/403).
8. Nunca imprime JWT, chave publicável, identificadores dos titulares,
   linhas, conteúdo de respostas ou corpo de erros do servidor.
9. Usa destino fixo HTTPS, evita redirecionamentos e restringe o cliente
   à lista de endpoints/consultas de diagnóstico.

Saídas: `0` = verificações de **leitura** aprovadas, incluindo existência de
ao menos uma mensagem do titular; `1` = falha ou evidência incompleta;
`2` = configuração ausente/não autorizada. Mesmo `0` **não autoriza
produção**: faltam testes de escrita/exclusão entre contas, reset de senha,
refresh/logout, concorrência da RPC e uso real no Safari/Telegram.

## Preparação futura no computador do operador

- Criar ou convidar uma segunda conta **de teste autorizada** no Auth do
  projeto ORBITA, sem usar conta de outro projeto. O processo envolve um
  segundo e-mail e sessão gerada legitimamente pelo próprio Supabase Auth.
- Obter duas sessões de curta duração por autenticação normal. Guardar os
  access tokens **somente no computador privado**; nunca copiá-los para esta
  conversa, GitHub, screenshots, logs, CI, comentários de PR ou documentos
  compartilhados. Não usar tokens `service_role`, `sb_secret_...`,
  refresh tokens nem senhas no script.
- Executar o comando manualmente num terminal privado, colocando os valores
  nas variáveis de ambiente abaixo. **Não digitar JWT em comandos salvos no
  histórico do shell.** A chave publicável está em `docs/cloud-config.js`.

```bash
export ORBITA_E2E_HTTP_RUN=YES_I_AUTHORIZE_READ_ONLY
export ORBITA_E2E_EXPECT_PROJECT=tbqfymedgdsdrgkqmuni

read -rs ORBITA_E2E_OWNER_JWT; echo
read -rs ORBITA_E2E_OTHER_JWT; echo
read -rs ORBITA_E2E_PUBLISHABLE_KEY; echo
export ORBITA_E2E_OWNER_JWT ORBITA_E2E_OTHER_JWT ORBITA_E2E_PUBLISHABLE_KEY

python quality/auth_http_rls_probe.py

unset ORBITA_E2E_OWNER_JWT ORBITA_E2E_OTHER_JWT ORBITA_E2E_PUBLISHABLE_KEY
unset ORBITA_E2E_HTTP_RUN ORBITA_E2E_EXPECT_PROJECT
```

Os comandos `read -rs` solicitam os valores sem exibí-los na tela;
os tokens ainda existem na memória do processo durante a execução.
Executar somente em computador confiável, nunca em ambiente compartilhado.
O teste usa TLS validado pela biblioteca padrão Python.

Se não existir um chat do titular, não criar registros artificiais no banco
real apenas para deixar esse teste verde. Preparar antes um fixture controlado,
plano de exclusão e backup verificável conforme `quality/SECURE_ROLLOUT_3_23.md`.

## Testes em CI e evidências

- `telegram/tests/test_auth_http_rls_probe.py`: 19 cenários mockados.
  Verifica a separação de sessões, isolamento de registros/chat, recusa de
  acesso privado/anônimo, recusa de JWT inválido, cliente apenas GET sem
  redirecionamento e proteção contra divulgação de credenciais.
- As execuções automáticas da CI **não** possuem JWTs de contas reais e não
  abrem conexão Supabase durante essa suíte.
- Último estado administrativo conferido no projeto em 24/10/2026:
  **uma conta Auth**. Teste real de duas sessões explicitamente pendente.

## Próximos gates

- Conta de teste distinta, JWT real, leitura cruzada HTTP.
- Backup recuperável e fixture de chat autorizado para testar RLS de fato.
- Escrever/editar/excluir/recuperar com permissões e limpeza de dados de teste.
- Aplicar SQL 002/003 somente com backup confirmado e homologação formal.
- Repetir segurança de RPC, webhook, confirmação por botões e entrega.
- Proteger o Auth contra senhas vazadas; validar recuperação e Safari/iPhone.
- Confirmar deploy Vercel e deixar a PR #7 em rascunho até aprovação completa.
