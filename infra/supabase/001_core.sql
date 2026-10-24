-- ORBITA 3.0 | Memória compartilhada. Execute somente em projeto Supabase DEDICADO ao ORBITA.
-- Exige Supabase Auth; RLS é obrigatória para todos os registros expostos.
create extension if not exists pgcrypto;

create table if not exists public.orbita_records (
  id text primary key check (length(id) between 1 and 128),
  user_id uuid not null references auth.users(id) on delete cascade,
  payload jsonb not null check (jsonb_typeof(payload) = 'object'),
  telegram_seq bigint generated always as identity unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists orbita_records_owner_updated_idx
  on public.orbita_records (user_id, updated_at desc);
alter table public.orbita_records enable row level security;

drop policy if exists orbita_records_select_self on public.orbita_records;
create policy orbita_records_select_self on public.orbita_records
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists orbita_records_insert_self on public.orbita_records;
create policy orbita_records_insert_self on public.orbita_records
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists orbita_records_update_self on public.orbita_records;
create policy orbita_records_update_self on public.orbita_records
  for update to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
drop policy if exists orbita_records_delete_self on public.orbita_records;
create policy orbita_records_delete_self on public.orbita_records
  for delete to authenticated using ((select auth.uid()) = user_id);
grant select, insert, update, delete on public.orbita_records to authenticated;

create table if not exists public.orbita_chat_messages (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user','assistant')),
  content text not null check (length(content) between 1 and 12000),
  created_at timestamptz not null default now()
);
create index if not exists orbita_chat_owner_time_idx
  on public.orbita_chat_messages (user_id, id desc);
alter table public.orbita_chat_messages enable row level security;

drop policy if exists orbita_chat_select_self on public.orbita_chat_messages;
create policy orbita_chat_select_self on public.orbita_chat_messages
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists orbita_chat_insert_self on public.orbita_chat_messages;
create policy orbita_chat_insert_self on public.orbita_chat_messages
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists orbita_chat_delete_self on public.orbita_chat_messages;
create policy orbita_chat_delete_self on public.orbita_chat_messages
  for delete to authenticated using ((select auth.uid()) = user_id);
grant select, insert, delete on public.orbita_chat_messages to authenticated;

-- Não há política para anon. Nunca colocar a chave sb_secret_ no navegador.
-- Garantir testes de isolamento RLS com duas identidades antes da operação real.

-- Proteção contra processamento duplicado de updates enviados pelo Telegram.
create table if not exists public.orbita_telegram_updates (
  update_id bigint primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'received' check (status in ('received','processed')),
  response text,
  created_at timestamptz not null default now()
);
alter table public.orbita_telegram_updates enable row level security;
-- SEM concessões nem políticas para anon/authenticated: somente backend com chave secret.
revoke all on public.orbita_telegram_updates from anon, authenticated;
