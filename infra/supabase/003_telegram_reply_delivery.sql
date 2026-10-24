-- ORBITA | Webhook telegram com fila de respostas preparada.
-- Compatível com serviço anterior: amplia status e mantém 'received'/'processed'.
alter table public.orbita_telegram_updates
  drop constraint if exists orbita_telegram_updates_status_check;
alter table public.orbita_telegram_updates
  add constraint orbita_telegram_updates_status_check
  check (status in ('received', 'replied', 'processed'));
-- As políticas e grants existentes não são ampliados.
