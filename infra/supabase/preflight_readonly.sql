-- ORBITA Aurora 3.21 | Auditoria SOMENTE DE LEITURA.
-- Execute apenas no projeto Supabase dedicado ao ORBITA.
-- Não executa DDL, INSERT, UPDATE, DELETE, RPC ou consultas aos registros pessoais.
-- A saída é JSON sem UUID, e-mail, tokens, títulos ou outros dados privados.
WITH objects AS (
 SELECT to_regclass('public.orbita_records') AS records,
        to_regclass('public.orbita_chat_messages') AS chat,
        to_regclass('public.orbita_telegram_updates') AS updates,
        to_regclass('public.orbita_action_proposals') AS proposals,
        to_regprocedure('public.orbita_confirm_action_proposal(text,uuid,bigint)') AS confirm_rpc
), observed AS (
 SELECT
  (records IS NOT NULL AND chat IS NOT NULL AND updates IS NOT NULL) AS base_tables_exist,
  COALESCE((SELECT bool_and(c.relrowsecurity) FROM pg_class c
            WHERE c.oid IN (records, chat, updates)
            HAVING count(*) = 3), FALSE) AS base_tables_rls,
  (proposals IS NOT NULL) AS proposal_table_exists,
  COALESCE((SELECT c.relrowsecurity FROM pg_class c WHERE c.oid=proposals),FALSE) AS proposal_rls,
  NOT COALESCE(has_table_privilege('anon',proposals,'SELECT'),FALSE)
   AND NOT COALESCE(has_table_privilege('authenticated',proposals,'SELECT'),FALSE)
   AND NOT COALESCE(has_table_privilege('anon',proposals,'INSERT'),FALSE)
   AND NOT COALESCE(has_table_privilege('authenticated',proposals,'INSERT'),FALSE)
   AND NOT COALESCE(has_table_privilege('anon',proposals,'UPDATE'),FALSE)
   AND NOT COALESCE(has_table_privilege('authenticated',proposals,'UPDATE'),FALSE) AS proposal_client_access_blocked,
  COALESCE(has_table_privilege('service_role',proposals,'SELECT'),FALSE)
   AND COALESCE(has_table_privilege('service_role',proposals,'INSERT'),FALSE)
   AND COALESCE(has_table_privilege('service_role',proposals,'UPDATE'),FALSE) AS proposal_service_access,
  (confirm_rpc IS NOT NULL) AS confirm_rpc_exists,
  NOT COALESCE(has_function_privilege('anon',confirm_rpc,'EXECUTE'),FALSE)
   AND NOT COALESCE(has_function_privilege('authenticated',confirm_rpc,'EXECUTE'),FALSE) AS confirm_rpc_client_access_blocked,
  COALESCE(has_function_privilege('service_role',confirm_rpc,'EXECUTE'),FALSE) AS confirm_rpc_service_access,
  COALESCE((SELECT p.prosecdef=FALSE FROM pg_proc p WHERE p.oid=confirm_rpc),FALSE) AS confirm_rpc_security_invoker,
  COALESCE((SELECT pg_get_constraintdef(k.oid) ILIKE '%delivered%'
                 AND pg_get_constraintdef(k.oid) ILIKE '%replied%'
                 AND pg_get_constraintdef(k.oid) ILIKE '%processed%'
                 AND pg_get_constraintdef(k.oid) ILIKE '%received%'
             FROM pg_constraint k
             WHERE k.conrelid=updates
               AND k.conname='orbita_telegram_updates_status_check'
             LIMIT 1),FALSE) AS delivery_states_ready
 FROM objects
)
SELECT jsonb_build_object(
 'base_tables_exist', base_tables_exist,
 'base_tables_rls', base_tables_rls,
 'proposal_table_exists', proposal_table_exists,
 'proposal_rls', proposal_rls,
 'proposal_client_access_blocked', proposal_client_access_blocked,
 'proposal_service_access', proposal_service_access,
 'confirm_rpc_exists', confirm_rpc_exists,
 'confirm_rpc_client_access_blocked', confirm_rpc_client_access_blocked,
 'confirm_rpc_service_access', confirm_rpc_service_access,
 'confirm_rpc_security_invoker', confirm_rpc_security_invoker,
 'delivery_states_ready', delivery_states_ready
) AS report
FROM observed;
