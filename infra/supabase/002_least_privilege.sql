-- ORBITA 3.0 | Privilégios mínimos na Data API (projeto: orbita).
-- Deve ser executado após 001_core.sql. A política RLS é complementar aos grants.
revoke all on table public.orbita_records, public.orbita_chat_messages, public.orbita_telegram_updates from anon;
revoke all on table public.orbita_records, public.orbita_chat_messages, public.orbita_telegram_updates from authenticated;
grant select, insert, update, delete on table public.orbita_records to authenticated;
grant select, insert, delete on table public.orbita_chat_messages to authenticated;
-- orbita_telegram_updates: apenas o backend com credencial privilegiada.
grant select, insert, update, delete on table
  public.orbita_records, public.orbita_chat_messages, public.orbita_telegram_updates to service_role;
grant usage, select on sequence public.orbita_records_telegram_seq_seq,
  public.orbita_chat_messages_id_seq to authenticated, service_role;
