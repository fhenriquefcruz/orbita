# ORBITA Aurora 3.21 — Diagnóstico reproduzível de prontidão do Supabase

**Ambiente-alvo:** somente o projeto exclusivo ORBITA no Supabase.
**Política:** SQL somente leitura; nenhuma migração é executada automaticamente.
**Dependências:** nenhuma chave, UUID, senha ou exportação de registros é necessária para gerar ou avaliar o relatório.

## Execução

1. Abra o SQL Editor do projeto Supabase **ORBITA**. Revise a consulta
   `infra/supabase/preflight_readonly.sql` e execute-a como leitura.
2. A consulta produz uma única coluna `report` com **11 booleanos**.
   Ela lê apenas metadados do catálogo (`pg_class`, `pg_constraint`,
   `pg_proc`) e permissões; não seleciona títulos, mensagens, IDs de usuários,
   tokens ou qualquer linha da memória pessoal.
3. Salve apenas o objeto da coluna `report` em um arquivo local `resultado.json`.
   **Não copie tokens, URLs privadas, strings de conexão ou senhas.**
4. Opcionalmente execute `python quality/verify_release_report.py resultado.json`
   para obter os estados de prontidão. Código de saída: `0` = estrutura
   necessária pronta **para testes**, `1` = pendências, `2` = relatório
   incompleto/inválido (falha segura).

Exemplo do formato, com valores ilustrativos:

```json
{
  "base_tables_exist": true,
  "base_tables_rls": true,
  "proposal_table_exists": false,
  "proposal_rls": false,
  "proposal_client_access_blocked": true,
  "proposal_service_access": false,
  "confirm_rpc_exists": false,
  "confirm_rpc_client_access_blocked": true,
  "confirm_rpc_service_access": false,
  "confirm_rpc_security_invoker": false,
  "delivery_states_ready": false
}
```

**Atenção:** um campo de bloqueio de acesso pode resultar em `true` quando
a tabela/RPC ainda não existe; o avaliador exige **também** a existência
e permissões efetivas. Não tratar o booleano isolado como homologação.

## Conclusão observada no projeto real em 24/10/2026

A consulta foi executada via conexão Supabase autorizada, **apenas para
leitura**, sem criar nem modificar registros. Resultado:

| Dimensão | Resultado observado | Implicação |
| --- | --- | --- |
| Tabelas principais da memória | Presentes | Prontas para testes de leitura |
| RLS nas três tabelas base | Ativo | Requer validar 2 sessões HTTP reais |
| `orbita_action_proposals` | Ausente | SQL 002 pendente |
| RPC `orbita_confirm_action_proposal` | Ausente | SQL 002 pendente |
| Restrição de estados Telegram | Ainda sem `delivered`; preserva `replied` | SQL 003 pendente |
| Políticas de propostas e RPC | Não aplicáveis enquanto objetos não existirem | Não habilitar a funcionalidade |

Não houve tentativa de aplicar `002_action_proposals.sql` ou
`003_telegram_delivery.sql`, nem mudança de feature flags.
Os arquivos dessas migrações já existem na branch de homologação.

## Gates independentes que NÃO são verificados por esse relatório

A saída `0` **não autoriza publicação automática**. Continua obrigatório:
- Duas contas Auth reais e testes HTTP de isolamento RLS;
- Fluxo de sessão, recuperação de senha e fechamento da conta no Safari/iPhone;
- Verificar SMTP e proteção contra senhas vazadas, conforme auditoria do Auth;
- Validar concorrência e idempotência reais da RPC de confirmação de propostas;
- Exercitar falha, repetição e entrega de mensagens em um bot Telegram privado;
- Aplicar SQL 002/003 **somente** após revisão, backup e aprovação operacional;
- Habilitar `ORBITA_NATURAL_ACTIONS_ENABLED=1` e
  `ORBITA_WEBHOOK_DELIVERY_V2_ENABLED=1` apenas no backend **privado**,
  depois da correspondente migração e testes;
- Confirmar deploy bem-sucedido com Vercel e demais checks, sem tocar
  `main` ou publicar código incompleto.

## Evidências de qualidade

- `telegram/tests/test_release_preflight.py`: 11 cenários de retorno válido,
  incompleto, tipos indevidos, privilégios inseguros, RLS ausente e SQL somente
  leitura.
- CI executa o conjunto junto com Python, Node, Playwright e os demais testes
  de integridade. Nenhuma credencial é necessária.
- Não foi criada nova API pública de diagnósticos, justamente para não expor
  permissões/configurações sensíveis a visitantes não autenticados.

**Próximo avanço:** plano de homologação SQL 002/003 no projeto exclusivo,
repetição dessa consulta após a migração e validação do isolamento da RPC antes
de habilitar qualquer botão no bot hospedado.
