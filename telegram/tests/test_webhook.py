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
    def test_another_user_ignored_even_with_valid_secret(self):
        update={'update_id':7,'message':{'chat':{'id':111,'type':'private'},'from':{'id':111},'text':'Olá'}}
        with patch.dict(os.environ,self.config):
            r=self.client.post('/api/telegram',json=update,headers={'X-Telegram-Bot-Api-Secret-Token':'test-secret'})
            self.assertEqual(r.status_code,200)
            self.assertTrue(r.json().get('ignored'))
