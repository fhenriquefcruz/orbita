-- ORBITA Aurora 3.23 — ensaio SQL de isolamento de identidade.
-- Somente leitura dos dados; transação local e ROLLBACK obrigatório.
-- Simula papéis PostgreSQL / JWT claims, NÃO equivale a Auth HTTP real.
-- Execute exclusivamente no projeto Supabase dedicado ORBITA, após revisão.
-- Não revela UUID, títulos, dados pessoais ou credenciais.
BEGIN;
SET LOCAL statement_timeout = '10s';

-- Recupera UUID do proprietário dentro do banco, sem mostrá-lo ao operador.
SELECT set_config('request.jwt.claim.sub',(
  SELECT user_id::text FROM public.orbita_records ORDER BY created_at LIMIT 1
),true);
SET LOCAL ROLE authenticated;
SELECT set_config('orbita.audit.owner_visible',
  (SELECT count(*)::text FROM public.orbita_records),true);
SELECT set_config('orbita.audit.owner_chat_visible',
  (SELECT count(*)::text FROM public.orbita_chat_messages),true);
SELECT set_config('orbita.audit.telegram_private',
  (NOT has_table_privilege(current_user,'public.orbita_telegram_updates','SELECT'))::text,true);
RESET ROLE;

-- UUID artificial que não pertence ao titular; não cria conta Auth.
SELECT set_config('request.jwt.claim.sub',
  '00000000-0000-4000-8000-000000000999',true);
SET LOCAL ROLE authenticated;
SELECT set_config('orbita.audit.nonowner_visible',
  (SELECT count(*)::text FROM public.orbita_records),true);
SELECT set_config('orbita.audit.nonowner_chat_visible',
  (SELECT count(*)::text FROM public.orbita_chat_messages),true);
RESET ROLE;

SET LOCAL ROLE anon;
SELECT set_config('orbita.audit.anon_denied',(
  NOT has_table_privilege(current_user,'public.orbita_records','SELECT')
  AND NOT has_table_privilege(current_user,'public.orbita_chat_messages','SELECT')
  AND NOT has_table_privilege(current_user,'public.orbita_telegram_updates','SELECT')
)::text,true);
RESET ROLE;

SELECT jsonb_build_object(
  'owner_has_visible_record',current_setting('orbita.audit.owner_visible',true)::integer >= 1,
  'nonowner_isolated',current_setting('orbita.audit.nonowner_visible',true)::integer = 0,
  'telegram_private',current_setting('orbita.audit.telegram_private',true)::boolean,
  'anon_restricted',current_setting('orbita.audit.anon_denied',true)::boolean,
  'nonowner_chat_isolated',current_setting('orbita.audit.nonowner_chat_visible',true)::integer = 0,
  'owner_chat_count_nonnegative',current_setting('orbita.audit.owner_chat_visible',true)::integer >= 0
) AS rls_access_evidence;
ROLLBACK;
