-- ORBITA Aurora 3.18 - Propostas de ações naturais com confirmação atômica.
-- Aplicar SOMENTE após homologação no Supabase dedicado ao ORBITA.
-- Não usar a chave secreta no painel. RPC acessível apenas ao backend service_role.

create table if not exists public.orbita_action_proposals (
  id uuid primary key default gen_random_uuid(),
  code text not null unique check (code ~ '^[0-9A-F]{12}$'),
  user_id uuid not null references auth.users(id) on delete cascade,
  telegram_id bigint not null,
  kind text not null check (kind in ('tarefa', 'ideia')),
  title text not null check (length(btrim(title)) between 1 and 1000),
  priority text not null check (priority in ('P0','P1','P2','P3')),
  status text not null default 'pending'
    check (status in ('pending','confirmed','cancelled','expired')),
  record_number bigint,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '15 minutes'),
  confirmed_at timestamptz,
  check (expires_at > created_at)
);

create index if not exists orbita_proposals_owner_time_idx
  on public.orbita_action_proposals (user_id, telegram_id, expires_at desc);

alter table public.orbita_action_proposals enable row level security;
revoke all on public.orbita_action_proposals from public, anon, authenticated;
grant select, insert, update on public.orbita_action_proposals to service_role;

-- SECURITY INVOKER: não eleva privilégios. Executável somente com credenciais
-- exclusivas do backend. O SELECT ... FOR UPDATE evita corrida entre confirmações.
create or replace function public.orbita_confirm_action_proposal(
  p_code text, p_user_id uuid, p_telegram_id bigint
) returns table(outcome text, record_number bigint)
language plpgsql volatile security invoker
set search_path = ''
as $function$
declare
  proposal public.orbita_action_proposals%rowtype;
  new_seq bigint;
  new_id text;
  now_at timestamptz;
begin
  select * into proposal
  from public.orbita_action_proposals
  where code = p_code and user_id = p_user_id and telegram_id = p_telegram_id
  for update;

  if not found then
    return query select 'missing'::text, null::bigint;
    return;
  end if;

  if proposal.status = 'confirmed' then
    return query select 'already'::text, proposal.record_number;
    return;
  end if;

  if proposal.status <> 'pending' then
    return query select proposal.status::text, null::bigint;
    return;
  end if;

  if proposal.expires_at <= pg_catalog.now() then
    update public.orbita_action_proposals
    set status = 'expired' where id = proposal.id;
    return query select 'expired'::text, null::bigint;
    return;
  end if;

  now_at := pg_catalog.now();
  new_id := 'tg-action-' || pg_catalog.replace(proposal.id::text, '-', '');
  insert into public.orbita_records
    (id, user_id, payload, created_at, updated_at)
  values (
    new_id,
    proposal.user_id,
    pg_catalog.jsonb_build_object(
      'id', new_id,
      'type', proposal.kind,
      'title', proposal.title,
      'context', case when proposal.kind = 'ideia' then 'criatividade' else 'pessoal' end,
      'priority', proposal.priority,
      'status', 'a_fazer',
      'source', 'Telegram ORBITA',
      'certainty', 'confirmado',
      'sensitivity', 'pessoal',
      'notify_mode', 'summary',
      'owner', case when proposal.kind = 'ideia' then 'Gusttavo Lima' else 'Zezé' end,
      'created_at', now_at,
      'updated_at', now_at
    ),
    now_at,
    now_at
  ) returning telegram_seq into new_seq;

  update public.orbita_action_proposals
  set status = 'confirmed', record_number = new_seq, confirmed_at = now_at
  where id = proposal.id;

  return query select 'saved'::text, new_seq;
end;
$function$;

revoke all on function public.orbita_confirm_action_proposal(text, uuid, bigint)
  from public, anon, authenticated;
grant execute on function public.orbita_confirm_action_proposal(text, uuid, bigint)
  to service_role;

-- As tabelas públicas do painel continuam protegidas por RLS;
-- a tabela de propostas não tem políticas para os clientes.
