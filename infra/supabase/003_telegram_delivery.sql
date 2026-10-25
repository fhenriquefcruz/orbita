-- ORBITA Aurora 3.20 — entrega verificada de respostas do webhook.
-- APLICAR SOMENTE no Supabase dedicado ORBITA após teste e backup.
-- Não alterar políticas RLS: orbita_telegram_updates continua restrita
-- exclusivamente ao backend com chave secret.

begin;

alter table public.orbita_telegram_updates
  drop constraint if exists orbita_telegram_updates_status_check;
alter table public.orbita_telegram_updates
  add constraint orbita_telegram_updates_status_check
  check (status in ('received', 'processed', 'delivered'));

-- A coluna status anterior não é substituída e as respostas existentes
-- continuam sendo válidas; entregas antigas continuam como 'processed',
-- pois não há recibo confiável para afirmar que foram enviadas.
-- NÃO realizar backfill cego para 'delivered'.
-- Nenhum grant/policy novo para anon/authenticated.

commit;
