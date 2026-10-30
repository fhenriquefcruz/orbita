"""Generate a transaction-only SQL homologation script for ORBITA's staged migrations.

No database connection, credentials, or external operations. The output is a
reviewable SQL file containing BEGIN ... ROLLBACK; it is never applied by Python.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL2 = ROOT / "infra/supabase/002_action_proposals.sql"
SQL3 = ROOT / "infra/supabase/003_telegram_delivery.sql"

TEST_BLOCK = r"""
DO $orbita_homologation$
DECLARE
  owner_uuid uuid;
  telegram_owner bigint := 740001;
  one_code text := upper(substr(replace(gen_random_uuid()::text,'-',''),1,12));
  cancelled_code text := upper(substr(replace(gen_random_uuid()::text,'-',''),1,12));
  expired_code text := upper(substr(replace(gen_random_uuid()::text,'-',''),1,12));
  returned_status text;
  first_sequence bigint;
  repeated_sequence bigint;
BEGIN
  SELECT id INTO owner_uuid FROM auth.users ORDER BY created_at LIMIT 1;
  IF owner_uuid IS NULL THEN
    RAISE EXCEPTION 'Homologação requer uma conta Auth existente; nenhum registro foi gravado';
  END IF;

  IF NOT (SELECT relrowsecurity FROM pg_class
          WHERE oid = 'public.orbita_action_proposals'::regclass) THEN
    RAISE EXCEPTION 'RLS ausente na tabela de propostas';
  END IF;
  IF has_table_privilege('anon','public.orbita_action_proposals','SELECT')
     OR has_table_privilege('authenticated','public.orbita_action_proposals','SELECT')
     OR has_table_privilege('anon','public.orbita_action_proposals','INSERT')
     OR has_table_privilege('authenticated','public.orbita_action_proposals','INSERT')
     OR has_table_privilege('authenticated','public.orbita_action_proposals','UPDATE') THEN
    RAISE EXCEPTION 'Privilégio indevido para cliente das propostas';
  END IF;
  IF has_function_privilege('anon',
           'public.orbita_confirm_action_proposal(text,uuid,bigint)','EXECUTE')
     OR has_function_privilege('authenticated',
           'public.orbita_confirm_action_proposal(text,uuid,bigint)','EXECUTE')
     OR NOT has_function_privilege('service_role',
           'public.orbita_confirm_action_proposal(text,uuid,bigint)','EXECUTE') THEN
    RAISE EXCEPTION 'Permissões inseguras na RPC de confirmação';
  END IF;
  IF NOT (SELECT NOT prosecdef FROM pg_proc
          WHERE oid='public.orbita_confirm_action_proposal(text,uuid,bigint)'::regprocedure) THEN
    RAISE EXCEPTION 'RPC de confirmação deve ser SECURITY INVOKER';
  END IF;

  INSERT INTO public.orbita_action_proposals
    (code,user_id,telegram_id,kind,title,priority)
  VALUES (one_code,owner_uuid,telegram_owner,'tarefa',
          'ORBITA DRY-RUN TEMPORARY TASK','P2');

  SELECT outcome,record_number INTO returned_status,first_sequence
  FROM public.orbita_confirm_action_proposal(one_code,owner_uuid,telegram_owner);
  IF returned_status <> 'saved' OR first_sequence IS NULL THEN
    RAISE EXCEPTION 'Primeira confirmação falhou: %',returned_status;
  END IF;

  SELECT outcome,record_number INTO returned_status,repeated_sequence
  FROM public.orbita_confirm_action_proposal(one_code,owner_uuid,telegram_owner);
  IF returned_status <> 'already' OR repeated_sequence <> first_sequence THEN
    RAISE EXCEPTION 'Repetição deixou de ser idempotente';
  END IF;

  SELECT outcome INTO returned_status
  FROM public.orbita_confirm_action_proposal(
    one_code,'00000000-0000-4000-8000-000000000000'::uuid,telegram_owner);
  IF returned_status <> 'missing' THEN
    RAISE EXCEPTION 'Outra conta pode confirmar a proposta';
  END IF;

  SELECT outcome INTO returned_status
  FROM public.orbita_confirm_action_proposal(one_code,owner_uuid,telegram_owner+1);
  IF returned_status <> 'missing' THEN
    RAISE EXCEPTION 'Outro Telegram ID pode confirmar a proposta';
  END IF;

  INSERT INTO public.orbita_action_proposals
    (code,user_id,telegram_id,kind,title,priority,status)
  VALUES (cancelled_code,owner_uuid,telegram_owner,'ideia',
          'ORBITA DRY-RUN CANCELLED IDEA','P3','cancelled');

  SELECT outcome INTO returned_status
  FROM public.orbita_confirm_action_proposal(cancelled_code,owner_uuid,telegram_owner);
  IF returned_status <> 'cancelled' THEN
    RAISE EXCEPTION 'Proposta cancelada foi confirmada';
  END IF;

  INSERT INTO public.orbita_action_proposals
    (code,user_id,telegram_id,kind,title,priority,created_at,expires_at)
  VALUES (expired_code,owner_uuid,telegram_owner,'tarefa',
          'ORBITA DRY-RUN EXPIRED TASK','P1',
          now()-interval '1 hour',now()-interval '20 minutes');

  SELECT outcome INTO returned_status
  FROM public.orbita_confirm_action_proposal(expired_code,owner_uuid,telegram_owner);
  IF returned_status <> 'expired' THEN
    RAISE EXCEPTION 'Proposta expirada foi confirmada';
  END IF;

  IF (SELECT count(*) FROM public.orbita_records WHERE id LIKE 'tg-action-%'
      AND payload->>'title'='ORBITA DRY-RUN TEMPORARY TASK') <> 1 THEN
    RAISE EXCEPTION 'Esperado exatamente um registro transitório';
  END IF;
END
$orbita_homologation$;

SELECT jsonb_build_object(
  'atomic_confirmation', 'pass',
  'repeat_idempotency', 'pass',
  'owner_isolation', 'pass',
  'telegram_isolation', 'pass',
  'cancelled_proposal', 'pass',
  'expired_proposal', 'pass',
  'client_privileges', 'pass',
  'rpc_invoker', 'pass',
  'delivery_state', (
    SELECT position('delivered' IN pg_get_constraintdef(oid))>0
    FROM pg_constraint
    WHERE conrelid='public.orbita_telegram_updates'::regclass
      AND conname='orbita_telegram_updates_status_check'
  )
) AS homologation_evidence;
"""


def build(root: Path = ROOT) -> str:
    """Build SQL, requiring exact migration identities and one outer transaction."""
    first = (root / "infra/supabase/002_action_proposals.sql").read_text(encoding="utf-8")
    second = (root / "infra/supabase/003_telegram_delivery.sql").read_text(encoding="utf-8")
    if ("create table if not exists public.orbita_action_proposals" not in first.lower()
            or "create or replace function public.orbita_confirm_action_proposal" not in first.lower()
            or "alter table public.orbita_telegram_updates" not in second.lower()):
        raise ValueError("Arquivos de migração não correspondem à arquitetura ORBITA.")
    if re.search(r"(?im)^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", first):
        raise ValueError("SQL 002 contém controle de transação inesperado.")
    second = re.sub(r"(?im)^\s*BEGIN\s*;\s*$", "", second)
    second = re.sub(r"(?im)^\s*COMMIT\s*;\s*$", "", second)
    if re.search(r"(?im)^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", second):
        raise ValueError("SQL 003 contém controle de transação inesperado.")
    return (
        "-- Somente homologação transacional ORBITA; REVISAO HUMANA obrigatória.\n"
        "-- NUNCA substituir ROLLBACK por COMMIT. Não executa deploy.\n"
        "BEGIN;\nSET LOCAL lock_timeout='2s';\n"
        "SET LOCAL statement_timeout='12s';\n"
        + first + "\n" + second + "\n" + TEST_BLOCK + "\nROLLBACK;\n"
    )


def main() -> int:
    try:
        script = build()
    except (OSError, ValueError) as exc:
        print(f"Falha ao montar homologação: {type(exc).__name__}", file=sys.stderr)
        return 2
    sys.stdout.write(script)
    return 0


if __name__ == "__main__":
    sys.exit(main())
