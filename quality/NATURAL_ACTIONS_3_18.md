# ORBITA Aurora 3.18 — Ações naturais com confirmação explícita

## Contrato de experiência

A Vânia continua conversando livremente pelo Telegram com a API OpenAI
quando configurada. Pedidos explícitos de **anotar tarefas e ideias** têm
um fluxo próprio e determinístico, que não depende do modelo para interpretar
a confirmação ou executar uma alteração.

Exemplos reconhecidos:
- "Vânia, anote que preciso enviar o relatório amanhã"
- "Crie uma tarefa para revisar a apresentação urgente"
- "Registre uma ideia: criar um painel de visitas"
- "Tive uma ideia de melhorar a experiência mobile"

A resposta apresenta **tipo, título, prioridade** e um código aleatório de
12 caracteres hexadecimais, incluindo instruções completas para
`confirmar CÓDIGO` ou `cancelar CÓDIGO`. Nenhuma tarefa é criada nesta etapa.
A confirmação do código é obrigatória mesmo se o usuário disser "sim": essa
mensagem isolada não autoriza gravar nada. Uma proposta vale 15 minutos.
Códigos de propostas são vinculados ao titular e ao Telegram ID.

O pedido de "amanhã" é conservado como texto, **não agendado**; alarmes,
notificações e calendário continuam desativados. Pedidos naturais fora das
expressões explícitas reconhecidas seguem a conversa pela IA sem execução.
Não houve implementação de edição/exclusão natural nem áudio/botões nesta fase.

## Persistência e consistência

- **SQLite local**: tabela `action_proposals`; transação `BEGIN IMMEDIATE`
  envolvendo consulta/expiração, INSERT do registro e marcação de confirmação.
  Resultado repetido devolve o mesmo identificador, sem duplicata. Propostas
  sobrevivem à reinicialização do processo.
- **Supabase**: migração proposta em `infra/supabase/002_action_proposals.sql`
  cria `public.orbita_action_proposals` com RLS, sem acesso de `anon` ou
  `authenticated`. A única função de confirmação é
  `public.orbita_confirm_action_proposal`, `SECURITY INVOKER`, com execução
  concedida exclusivamente a `service_role`. Faz `SELECT ... FOR UPDATE`,
  verifica usuário, Telegram ID e expiração, cria registro e consome proposta
  numa única transação de banco. Repetições retornam `already`.
- O servidor usa `SUPABASE_SECRET_KEY` apenas no backend. O frontend jamais
  vê o segredo ou a tabela de propostas. Sem configuração completa, nenhuma
  migração ou execução é disparada automaticamente.
- Cada proposta possui código aleatório gerado pelo servidor e ID UUID; o ID
  final do registro é derivado desse UUID. Código inválido ou desconhecido
  nunca dispara INSERT. A reserva de código tem restrição UNIQUE.
- `/tarefa`, `/ideia`, `/feito` permanecem operacionais e independentes da
  API OpenAI. O processamento de `update_id` do webhook continua deduplicado.

## Gate operacional obrigatório

**Não há ativação em nuvem por padrão.** O backend com `CloudMemory`
verifica `ORBITA_NATURAL_ACTIONS_ENABLED=1` antes de aceitar propostas.
Se a variável estiver ausente ou em zero, explica que o recurso ainda está
em homologação. SQLite local permite exercícios não remotos.

Sequência de implantação segura, que **não foi executada nesta entrega**:
1. Executar a migração SQL no projeto *exclusivo* ORBITA, após revisão e backup.
2. Confirmar privilégios do RPC e RLS com duas contas separadas; `anon` e
   `authenticated` não devem consultar propostas, nem executar o RPC.
3. Testar confirmar/cancelar/expirar/duplicar sob concorrência real e auditar
   as linhas criadas na tabela `orbita_records`.
4. Definir `ORBITA_NATURAL_ACTIONS_ENABLED=1` somente no backend privado
   homologado. Não salvar variáveis privadas no GitHub.
5. Testar webhooks duplicados, restart serverless, bot local e cenários de
   falha na entrega da mensagem. Definir rotina de retenção/purga de
   propostas antigas antes de uso prolongado.
6. Homologar ainda os gates gerais da PR #7 (Auth/RLS HTTP, recuperação de
   senha e Safari/iPhone), sem mesclar em `main` prematuramente.

## Qualidade
- `telegram/tests/test_action_proposals.py`: parser conservador, proposta,
  expiração, cancelamento, idempotência, isolamento, recuperação e transação.
- `telegram/tests/test_cloud_proposals.py`: contrato da RPC, vínculo do
  titular, flag desligada e resposta remota obrigatória.
- `telegram/tests/test_natural_chat.py`: regressão da conversa livre com
  ação proposta e nenhuma gravação automática.
- Testes executados pelo workflow Python do GitHub Actions, sem tokens reais.
- Esta etapa NÃO representa E2E Supabase/Telegram real; publicação continua
  condicionada aos gates de segurança.

## Próximos incrementos
Controles "Confirmar"/"Cancelar" por botões InlineKeyboard do Telegram,
resposta a áudios e extração semântica mais abrangente mediante modelo em
modo estruturado, cada qual com validação estrita e sem execução tácita.
