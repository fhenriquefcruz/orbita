-- ORBITA | Migração já aplicada no projeto dedicado em 25/10/2026.
-- Supabase Migration: 20261025103735 / orbita_telegram_update_owner_index
-- Somente índice de desempenho sobre a coluna FK; não altera registros, concessões ou RLS.
-- As mudanças de esquema opcionais 002/003 seguem PENDENTES e exigem backup validado.
create index if not exists orbita_telegram_updates_user_id_idx
  on public.orbita_telegram_updates (user_id);
