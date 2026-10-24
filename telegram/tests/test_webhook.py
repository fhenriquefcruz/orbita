import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
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
    def test_another_user_ignored_even_with_valid_secret(self):
        update={'update_id':7,'message':{'chat':{'id':111,'type':'private'},'from':{'id':111},'text':'Olá'}}
        with patch.dict(os.environ,self.config):
            r=self.client.post('/api/telegram',json=update,headers={'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
            self.assertEqual(r.status_code,200)
            self.assertTrue(r.json().get('ignored'))

    def test_new_response_saved_before_telegram_send(self):
        update = {'update_id': 85, 'message': {
            'chat': {'id': 54321, 'type': 'private'},
            'from': {'id': 54321, 'is_bot': False}, 'text': '/tarefa Comprar algo'}}
        mem = MagicMock()
        mem.claim_update.return_value = True
        events = []
        mem.stage_reply.side_effect = lambda *args: events.append('staged')
        mem.finish_update.side_effect = lambda *args: events.append('processed')
        def sender(*args, **kwargs):
            events.append('sent')
        with patch.dict(os.environ, self.config), \
             patch('api.index.CloudMemory', return_value=mem), \
             patch('api.index.reply_text', return_value='Registrado') as answer, \
             patch('api.index.telegram_call', side_effect=sender):
            response = self.client.post('/api/telegram', json=update,
                headers={'X-Telegram-Bot-Api-Secret-Token': 'test-secret'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(events, ['staged', 'sent', 'processed'])
        answer.assert_called_once()
        mem.stage_reply.assert_called_once_with(85, 'Registrado')
        mem.finish_update.assert_called_once_with(85)

    def test_failed_send_remains_queued_for_retry(self):
        update = {'update_id': 86, 'message': {
            'chat': {'id': 54321, 'type': 'private'},
            'from': {'id': 54321}, 'text': '/tarefa Texto'}}
        mem = MagicMock()
        mem.claim_update.return_value = True
        with patch.dict(os.environ, self.config), \
             patch('api.index.CloudMemory', return_value=mem), \
             patch('api.index.reply_text', return_value='Resposta'), \
             patch('api.index.telegram_call', side_effect=RuntimeError('fail')):
            response = self.client.post('/api/telegram', json=update,
                headers={'X-Telegram-Bot-Api-Secret-Token': 'test-secret'})
        self.assertEqual(response.status_code, 503)
        mem.stage_reply.assert_called_once_with(86, 'Resposta')
        mem.finish_update.assert_not_called()

    def test_retry_uses_persisted_answer_without_reexecuting_command(self):
        update = {'update_id': 87, 'message': {
            'chat': {'id': 54321, 'type': 'private'},
            'from': {'id': 54321}, 'text': '/tarefa Texto'}}
        mem = MagicMock()
        mem.claim_update.return_value = False
        mem.get_update.return_value = {'status': 'replied', 'response': 'Ja preparado'}
        with patch.dict(os.environ, self.config), \
             patch('api.index.CloudMemory', return_value=mem), \
             patch('api.index.reply_text') as answer, \
             patch('api.index.telegram_call') as send:
            response = self.client.post('/api/telegram', json=update,
                headers={'X-Telegram-Bot-Api-Secret-Token': 'test-secret'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('resumed'))
        answer.assert_not_called()
        send.assert_called_once()
        mem.finish_update.assert_called_once_with(87)

    def test_processed_update_does_not_send_twice(self):
        update = {'update_id': 88, 'message': {
            'chat': {'id': 54321, 'type': 'private'}, 'from': {'id': 54321}, 'text': '/tarefa Texto'}}
        mem = MagicMock()
        mem.claim_update.return_value = False
        mem.get_update.return_value = {'status': 'processed', 'response': 'Ja enviado'}
        with patch.dict(os.environ, self.config), \
             patch('api.index.CloudMemory', return_value=mem), \
             patch('api.index.telegram_call') as send:
            response = self.client.post('/api/telegram', json=update,
                headers={'X-Telegram-Bot-Api-Secret-Token': 'test-secret'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('duplicate'))
        send.assert_not_called()
