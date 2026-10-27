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
        cloud.return_value.finish_update.assert_not_called()
        cloud.return_value.stage_reply.assert_called_once_with(134, 'Lista de tarefas')
        cloud.return_value.confirm_legacy_sent.assert_called_once_with(134)
        telegram.assert_called_once()

    @staticmethod
    def _fixture(update_id, command='/tarefa P1 | Comprar material'):
        return {'update_id':update_id,
                'message':{'chat':{'id':54321,'type':'private'},
                           'from':{'id':54321,'is_bot':False},
                           'text':command}}

    def test_legacy_stages_response_before_sending(self):
        from unittest.mock import MagicMock
        update=self._fixture(140)
        events=[]
        mem=MagicMock()
        mem.claim_update.return_value=True
        mem.stage_reply.side_effect=lambda *args: events.append('staged')
        mem.confirm_legacy_sent.side_effect=lambda *args: events.append('processed')
        def sender(*args,**kwargs):
            events.append('sent')
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}), \
             patch('api.index.CloudMemory',return_value=mem), \
             patch('api.index.reply_text',return_value='Tarefa salva') as reply, \
             patch('api.index.telegram_call',side_effect=sender):
            result=self.client.post('/api/telegram',json=update,headers={
                'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(result.status_code,200)
        self.assertEqual(events,['staged','sent','processed'])
        reply.assert_called_once()
        mem.stage_reply.assert_called_once_with(140,'Tarefa salva')
        mem.confirm_legacy_sent.assert_called_once_with(140)
        mem.finish_update.assert_not_called()
        mem.mark_delivered.assert_not_called()

    def test_legacy_retry_replays_saved_answer_without_second_action(self):
        from unittest.mock import MagicMock
        mem=MagicMock()
        mem.claim_update.side_effect=[True,False]
        mem.get_update.return_value={'status':'replied','response':'Tarefa salva'}
        sent=MagicMock(side_effect=[TimeoutError('telegram offline'),{'message_id':7}])
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}), \
             patch('api.index.CloudMemory',return_value=mem), \
             patch('api.index.reply_text',return_value='Tarefa salva') as reply, \
             patch('api.index.telegram_call',sent):
            first=self.client.post('/api/telegram',json=self._fixture(141),headers={
                'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
            second=self.client.post('/api/telegram',json=self._fixture(141),headers={
                'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(first.status_code,503)
        self.assertEqual(second.status_code,200)
        self.assertTrue(second.json().get('resumed'))
        reply.assert_called_once()
        mem.stage_reply.assert_called_once_with(141,'Tarefa salva')
        mem.confirm_legacy_sent.assert_called_once_with(141)
        self.assertEqual(sent.call_count,2)
        mem.finish_update.assert_not_called()
        mem.mark_delivered.assert_not_called()

    def test_legacy_persistence_failure_never_sends(self):
        from unittest.mock import MagicMock
        mem=MagicMock()
        mem.claim_update.return_value=True
        mem.stage_reply.side_effect=RuntimeError('DB temporarily unavailable')
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}), \
             patch('api.index.CloudMemory',return_value=mem), \
             patch('api.index.reply_text',return_value='Resposta') as reply, \
             patch('api.index.telegram_call') as send:
            result=self.client.post('/api/telegram',json=self._fixture(142),headers={
                'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(result.status_code,503)
        reply.assert_called_once()
        send.assert_not_called()
        mem.confirm_legacy_sent.assert_not_called()

    def test_legacy_duplicate_after_processed_never_resends(self):
        from unittest.mock import MagicMock
        mem=MagicMock()
        mem.claim_update.return_value=False
        mem.get_update.return_value={'status':'processed','response':'Resposta'}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}), \
             patch('api.index.CloudMemory',return_value=mem), \
             patch('api.index.reply_text') as reply, \
             patch('api.index.telegram_call') as send:
            result=self.client.post('/api/telegram',json=self._fixture(143),headers={
                'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(result.status_code,200)
        self.assertTrue(result.json().get('duplicate'))
        reply.assert_not_called()
        send.assert_not_called()

    def test_v2_can_replay_pending_legacy_reply_on_migration(self):
        from unittest.mock import MagicMock
        mem=MagicMock()
        mem.claim_update.return_value=False
        mem.get_update.return_value={'status':'replied','response':'Resposta legada'}
        mem.mark_delivered.return_value=True
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'1'}), \
             patch('api.index.CloudMemory',return_value=mem), \
             patch('api.index.reply_text') as reply, \
             patch('api.index.telegram_call') as send:
            result=self.client.post('/api/telegram',json=self._fixture(144),headers={
                'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(result.status_code,200)
        self.assertTrue(result.json().get('replayed'))
        reply.assert_not_called()
        send.assert_called_once()
        mem.confirm_legacy_sent.assert_called_once_with(144)
        mem.mark_delivered.assert_called_once_with(144)
        mem.finish_update.assert_not_called()

    def test_received_without_answer_remains_pending(self):
        from unittest.mock import MagicMock
        mem=MagicMock()
        mem.claim_update.return_value=False
        mem.get_update.return_value={'status':'received','response':None}
        with patch.dict(os.environ,{**self.config,'ORBITA_WEBHOOK_DELIVERY_V2_ENABLED':'0'}), \
             patch('api.index.CloudMemory',return_value=mem), \
             patch('api.index.reply_text') as reply, \
             patch('api.index.telegram_call') as send:
            result=self.client.post('/api/telegram',json=self._fixture(145),headers={
                'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
        self.assertEqual(result.status_code,200)
        self.assertTrue(result.json().get('pending'))
        reply.assert_not_called()
        send.assert_not_called()

    def test_another_user_ignored_even_with_valid_secret(self):
        update={'update_id':7,'message':{'chat':{'id':111,'type':'private'},'from':{'id':111},'text':'Olá'}}
        with patch.dict(os.environ,self.config):
            r=self.client.post('/api/telegram',json=update,headers={'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
            self.assertEqual(r.status_code,200)
            self.assertTrue(r.json().get('ignored'))
