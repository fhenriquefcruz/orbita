import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from fastapi.testclient import TestClient
    from api.index import app
except ImportError:
    TestClient = None

@unittest.skipIf(TestClient is None, 'FastAPI/httpx indisponíveis')
class TestWebhook(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.config = {
            'TELEGRAM_BOT_TOKEN': '111:EXAMPLE_NONSECRET_TEST_TOKEN_123456',
            'TELEGRAM_WEBHOOK_SECRET': 'test-secret',
            'ORBITA_OWNER_ID': '54321',
            'SUPABASE_URL': 'https://orbita-test.supabase.co',
            'SUPABASE_SECRET_KEY': 'sb_secret_dummy_only',
            'ORBITA_USER_UUID': '11111111-1111-4111-8111-111111111111',
        }
    def test_disabled_without_secrets(self):
        with patch.dict(os.environ, {k:'' for k in self.config}, clear=False):
            r=self.client.post('/api/telegram',json={'update_id':1})
            self.assertEqual(r.status_code,503)
    def test_wrong_header_rejected(self):
        with patch.dict(os.environ, self.config):
            r=self.client.post('/api/telegram',json={'update_id':1},headers={'X-Telegram-Bot-Api-Secret-Token':'wrong'})
            self.assertEqual(r.status_code,403)
    def test_authorized_button_is_routed_to_explicit_confirmation(self):
        callback = {
            'update_id': 123,
            'callback_query': {
                'id':'callback-one','from':{'id':54321},
                'data':'orbita:confirm:ABCDEF123456',
                'message':{'chat':{'id':54321,'type':'private'}}
            }
        }
        from unittest.mock import MagicMock
        with patch.dict(os.environ, self.config):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text', return_value='✅ Registro #15 salvo') as reply, patch(
                    'api.index.telegram_call') as telegram:
                cloud.return_value.claim_update.return_value = True
                response = self.client.post('/api/telegram',json=callback,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json().get('ok'))
        reply.assert_called_once()
        self.assertEqual(reply.call_args.args[0], 'confirmar ABCDEF123456')
        cloud.return_value.finish_update.assert_called_once()
        self.assertEqual([x.args[1] for x in telegram.call_args_list],
                         ['sendMessage','answerCallbackQuery'])

    def test_callback_from_other_account_never_hits_storage(self):
        update={
            'update_id':124,
            'callback_query':{
                'id':'callback-other','from':{'id':22222},
                'data':'orbita:confirm:ABCDEF123456',
                'message':{'chat':{'id':54321,'type':'private'}}
            }
        }
        with patch.dict(os.environ, self.config):
            with patch('api.index.CloudMemory') as cloud:
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json().get('ignored'))
        cloud.assert_not_called()

    def test_malformed_callback_does_not_claim_update(self):
        update={
            'update_id':125,
            'callback_query':{
                'id':'callback-bad','from':{'id':54321},
                'data':'orbita:delete:ABCDEF123456',
                'message':{'chat':{'id':54321,'type':'private'}}
            }
        }
        with patch.dict(os.environ, self.config):
            with patch('api.index.CloudMemory') as cloud:
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json().get('ignored'))
        cloud.assert_not_called()

    def test_v2_replays_saved_reply_after_failed_delivery_without_reexecuting(self):
        update={'update_id':130,'message':{'chat':{'id':54321,'type':'private'},
               'from':{'id':54321},'text':'/tarefa P1 | Fechar relatório'}}
        config={**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'1'}
        with patch.dict(os.environ,config):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text', return_value='✅ Registro #42 salvo') as reply, patch(
                    'api.index.telegram_call') as telegram:
                mem=cloud.return_value
                mem.claim_update.side_effect=[True,False]
                mem.get_update.return_value={
                    'status':'processed','response':'✅ Registro #42 salvo'}
                mem.mark_delivered.return_value=True
                telegram.side_effect=[TimeoutError('Telegram offline'), {'message_id':7}]
                first=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
                self.assertEqual(first.status_code,503)
                second=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(second.status_code,200)
        self.assertTrue(second.json().get('replayed'))
        reply.assert_called_once()
        mem.finish_update.assert_called_once()
        mem.mark_delivered.assert_called_once_with(130)
        self.assertEqual(telegram.call_count,2)
        self.assertEqual(telegram.call_args.kwargs['timeout'],10)

    def test_v2_delivered_update_is_not_sent_twice(self):
        update={'update_id':131,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'/tarefas'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'1'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text') as reply, patch(
                    'api.index.telegram_call') as telegram:
                cloud.return_value.claim_update.return_value=False
                cloud.return_value.get_update.return_value={'status':'delivered'}
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json().get('duplicate'))
        reply.assert_not_called()
        telegram.assert_not_called()

    def test_v2_pending_without_response_never_reexecutes_action(self):
        update={'update_id':132,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'confirmar ABCDEF123456'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'1'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text') as reply, patch(
                    'api.index.telegram_call') as telegram:
                cloud.return_value.claim_update.return_value=False
                cloud.return_value.get_update.return_value={'status':'received','response':None}
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json().get('pending'))
        reply.assert_not_called()
        telegram.assert_not_called()

    def test_v2_mark_delivered_failure_cannot_claim_success(self):
        update={'update_id':133,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'/tarefas'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'1'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text',return_value='Lista de tarefas'), patch(
                    'api.index.telegram_call') as telegram:
                cloud.return_value.claim_update.return_value=True
                cloud.return_value.mark_delivered.return_value=False
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,503)
        cloud.return_value.finish_update.assert_called_once()
        telegram.assert_called_once()

    def test_legacy_saves_before_send_and_acks_after_success(self):
        events = []
        update={'update_id':140,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'/tarefa P1 | Enviar comprovante'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text',return_value='✅ Registrado') as reply, patch(
                    'api.index.telegram_call') as telegram:
                mem=cloud.return_value
                mem.claim_update.return_value=True
                mem.stage_reply.side_effect=lambda *_: events.append('staged')
                telegram.side_effect=lambda *_args,**_kwargs: events.append('sent')
                mem.finish_update.side_effect=lambda *_: events.append('acked')
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(events,['staged','sent','acked'])
        reply.assert_called_once()
        mem.stage_reply.assert_called_once_with(140,'✅ Registrado')
        mem.finish_update.assert_called_once_with(140)
        mem.mark_delivered.assert_not_called()

    def test_legacy_failed_telegram_send_replays_without_duplicate_action(self):
        update={'update_id':141,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'/tarefa P1 | Enviar comprovante'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text',return_value='✅ Registro #12 salvo') as reply, patch(
                    'api.index.telegram_call') as telegram:
                mem=cloud.return_value
                mem.claim_update.side_effect=[True,False]
                mem.get_update.return_value={
                    'status':'replied','response':'✅ Registro #12 salvo'}
                telegram.side_effect=[TimeoutError('Telegram offline'),{'message_id':7}]
                first=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
                self.assertEqual(first.status_code,503)
                mem.finish_update.assert_not_called()
                second=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(second.status_code,200)
        self.assertTrue(second.json().get('replayed'))
        reply.assert_called_once()
        mem.stage_reply.assert_called_once_with(141,'✅ Registro #12 salvo')
        mem.finish_update.assert_called_once_with(141)
        self.assertEqual(telegram.call_count,2)
        self.assertEqual(telegram.call_args.args[2]['text'],'✅ Registro #12 salvo')
        mem.mark_delivered.assert_not_called()

    def test_legacy_refuses_send_if_reply_was_not_persisted(self):
        update={'update_id':142,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'/tarefa Fechar pendência'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text',return_value='Registrado'), patch(
                    'api.index.telegram_call') as telegram:
                cloud.return_value.claim_update.return_value=True
                cloud.return_value.stage_reply.side_effect=RuntimeError('DB indisponivel')
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,503)
        telegram.assert_not_called()
        cloud.return_value.finish_update.assert_not_called()

    def test_legacy_received_unresolved_never_reexecutes_command(self):
        update={'update_id':143,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'/feito 3'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text') as reply, patch(
                    'api.index.telegram_call') as telegram:
                cloud.return_value.claim_update.return_value=False
                cloud.return_value.get_update.return_value={
                    'status':'received','response':None}
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json().get('pending'))
        reply.assert_not_called()
        telegram.assert_not_called()

    def test_v2_cutover_replays_legacy_replied_without_reexecuting(self):
        update={'update_id':151,'message':{
            'chat':{'id':54321,'type':'private'},
            'from':{'id':54321},'text':'/tarefa Fechar documento'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'1'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text') as reply, patch(
                    'api.index.telegram_call') as telegram:
                mem=cloud.return_value
                mem.claim_update.return_value=False
                mem.get_update.return_value={'status':'replied','response':'Resposta ja preparada'}
                mem.mark_delivered.return_value=True
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json().get('replayed'))
        reply.assert_not_called()
        mem.stage_reply.assert_not_called()
        mem.finish_update.assert_called_once_with(151)
        mem.mark_delivered.assert_called_once_with(151)
        telegram.assert_called_once()

    def test_v2_cutover_cannot_claim_success_if_legacy_ack_fails(self):
        update={'update_id':152,'message':{
            'chat':{'id':54321,'type':'private'},
            'from':{'id':54321},'text':'/feito 3'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'1'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text') as reply, patch(
                    'api.index.telegram_call') as telegram:
                mem=cloud.return_value
                mem.claim_update.return_value=False
                mem.get_update.return_value={'status':'replied','response':'Resposta ja preparada'}
                mem.finish_update.side_effect=RuntimeError('ACK indisponivel')
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,503)
        reply.assert_not_called()
        telegram.assert_called_once()
        mem.mark_delivered.assert_not_called()

    def test_legacy_mode_does_not_require_new_schema(self):
        update={'update_id':134,'message':{'chat':{'id':54321,'type':'private'},
                'from':{'id':54321},'text':'/tarefas'}}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}):
            with patch('api.index.CloudMemory') as cloud, patch(
                    'api.index.reply_text',return_value='Lista de tarefas'), patch(
                    'api.index.telegram_call') as telegram:
                cloud.return_value.claim_update.return_value=True
                response=self.client.post('/api/telegram',json=update,headers={
                    'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(response.status_code,200)
        cloud.return_value.mark_delivered.assert_not_called()
        telegram.assert_called_once()

    def test_another_user_ignored_even_with_valid_secret(self):
        update={'update_id':7,'message':{'chat':{'id':111,'type':'private'},'from':{'id':111},'text':'Olá'}}
        with patch.dict(os.environ,self.config):
            r=self.client.post('/api/telegram',json=update,headers={'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
            self.assertEqual(r.status_code,200)
            self.assertTrue(r.json().get('ignored'))
