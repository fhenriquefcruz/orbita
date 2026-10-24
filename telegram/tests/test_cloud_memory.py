import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloud_memory import CloudMemory


class FakeResponse:
    def __init__(self, rows):
        self.rows = rows
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self):
        return json.dumps(self.rows).encode()


class TestCloudMemory(unittest.TestCase):
    USER='11111111-1111-4111-8111-111111111111'
    def setUp(self):
        self.mem = CloudMemory('https://orbita-test.supabase.co','sb_secret_dummy_testing_only',self.USER)

    def test_url_require_https(self):
        with self.assertRaises(ValueError):
            CloudMemory('http://evil.example','secret',self.USER)

    def test_add_uses_server_key_and_user_scoped_json(self):
        def fake(req, timeout):
            self.assertIn('https://orbita-test.supabase.co/rest/v1/orbita_records',req.full_url)
            self.assertEqual(req.headers.get('Apikey'),'sb_secret_dummy_testing_only')
            self.assertNotIn('Authorization',req.headers)
            data=json.loads(req.data)
            self.assertEqual(data['user_id'],self.USER)
            self.assertEqual(data['payload']['priority'],'P1')
            return FakeResponse([{'telegram_seq': 42}])
        with patch('cloud_memory.urlopen',side_effect=fake):
            self.assertEqual(self.mem.add(5,'tarefa','Proposta','P1'),42)

    def test_list_owner_constraint(self):
        def fake(req, timeout):
            self.assertIn('user_id=eq.',req.full_url)
            return FakeResponse([{'telegram_seq':1,'payload':{'type':'tarefa','title':'A','priority':'P2','status':'a_fazer'}}])
        with patch('cloud_memory.urlopen',side_effect=fake):
            self.assertEqual(self.mem.list(5,'tarefa')[0]['id'],1)

    def test_cloud_history_order(self):
        with patch.object(self.mem,'_call',return_value=[{'role':'assistant','content':'Resposta'}, {'role':'user','content':'Pergunta'}]):
            self.assertEqual(self.mem.history(5)[0]['role'],'user')

    def test_complete_cannot_complete_idea(self):
        with patch.object(self.mem,'_call',return_value=[{'id':'tg-1','payload':{'type':'ideia','status':'a_fazer'}}]) as call:
            self.assertFalse(self.mem.complete(5,3))
            self.assertEqual(call.call_count,1)

    def test_duplicate_update_can_be_deduplicated(self):
        with patch.object(self.mem,'_call',return_value=[]) as call:
            self.assertFalse(self.mem.claim_update(100))
            self.assertIn('ignore-duplicates',call.call_args.kwargs['prefer'])
