import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from urllib.parse import parse_qs, urlsplit
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

    def test_complete_only_confirms_one_version_matched_row(self):
        before = {'id':'tg-1','updated_at':'2026-10-24T20:30:00+00:00',
                  'payload':{'id':'tg-1','title':'Minha tarefa',
                             'type':'tarefa','status':'em_andamento','priority':'P1'}}
        snapshot = json.loads(json.dumps(before))
        with patch.object(self.mem, '_call', side_effect=[[before], [{'id':'tg-1'}]]) as call:
            self.assertTrue(self.mem.complete(5, 17))
            self.assertEqual(call.call_count, 2)
            read = call.call_args_list[0]
            write = call.call_args_list[1]
            self.assertEqual(read.kwargs['query']['select'], 'id,payload,updated_at')
            self.assertEqual(read.kwargs['query']['user_id'], 'eq.' + self.USER)
            self.assertEqual(read.kwargs['query']['telegram_seq'], 'eq.17')
            self.assertEqual(write.args[:2], ('orbita_records','PATCH'))
            self.assertEqual(write.kwargs['query']['updated_at'], 'eq.2026-10-24T20:30:00+00:00')
            self.assertEqual(write.kwargs['query']['user_id'], 'eq.' + self.USER)
            self.assertEqual(write.kwargs['prefer'], 'return=representation')
            changes = write.kwargs['value']
            self.assertEqual(changes['payload']['status'], 'concluida')
            self.assertEqual(changes['payload']['completed_at'], changes['updated_at'])
            self.assertGreater(datetime.fromisoformat(changes['updated_at']),
                               datetime.fromisoformat(before['updated_at']))
            self.assertEqual(before, snapshot, 'a leitura não pode ser mutada por referência')

    def test_complete_concurrent_edit_returning_zero_rows_is_not_success(self):
        row = {'id':'tg-1','updated_at':'2026-10-24T20:30:00Z',
               'payload':{'type':'tarefa','status':'a_fazer'}}
        with patch.object(self.mem, '_call', side_effect=[[row], []]) as call:
            self.assertFalse(self.mem.complete(5, 17))
            self.assertEqual(call.call_count, 2)
            self.assertEqual(call.call_args.kwargs['query']['updated_at'],
                             'eq.2026-10-24T20:30:00Z')

    def test_complete_never_accepts_wrong_row_confirmation(self):
        row = {'id':'tg-1','updated_at':'2026-10-24T20:30:00Z',
               'payload':{'type':'tarefa','status':'a_fazer'}}
        with patch.object(self.mem, '_call', side_effect=[[row], [{'id':'tg-other'}]]):
            self.assertFalse(self.mem.complete(5, 17))

    def test_complete_with_missing_or_invalid_revision_does_not_write(self):
        for stamp in (None, '', 'invalid', '2026-10-24T20:30:00'):
            with self.subTest(revision=stamp):
                row = {'id':'tg-1','updated_at':stamp,
                       'payload':{'type':'tarefa','status':'a_fazer'}}
                with patch.object(self.mem, '_call', return_value=[row]) as call:
                    self.assertFalse(self.mem.complete(5, 17))
                    self.assertEqual(call.call_count, 1)

    def test_complete_terminal_statuses_and_ideas_are_untouched(self):
        for kind, status in (('ideia','a_fazer'), ('tarefa','concluida'),
                             ('tarefa','cancelada'), ('tarefa','arquivada')):
            with self.subTest(kind=kind, status=status):
                row = {'id':'tg-1','updated_at':'2026-10-24T20:30:00Z',
                       'payload':{'type':kind,'status':status}}
                with patch.object(self.mem, '_call', return_value=[row]) as call:
                    self.assertFalse(self.mem.complete(5, 17))
                    self.assertEqual(call.call_count, 1)

    def test_complete_future_revision_moves_timestamp_forward(self):
        row = {'id':'tg-1','updated_at':'2032-01-01T00:00:00+00:00',
               'payload':{'type':'tarefa','status':'a_fazer'}}
        with patch.object(self.mem, '_call', side_effect=[[row],[{'id':'tg-1'}]]) as call:
            self.assertTrue(self.mem.complete(5, 17))
            timestamp = call.call_args.kwargs['value']['updated_at']
            self.assertGreater(datetime.fromisoformat(timestamp),
                               datetime.fromisoformat(row['updated_at']))

    def test_complete_postgrest_encodes_revision_and_checks_representation(self):
        calls = []
        row = {'id':'tg-1','updated_at':'2026-10-24T20:30:00+00:00',
               'payload':{'id':'tg-1','type':'tarefa','status':'a_fazer'}}
        def fake(req, timeout):
            calls.append(req)
            if req.method == 'GET':
                return FakeResponse([row])
            params = parse_qs(urlsplit(req.full_url).query)
            self.assertEqual(req.method, 'PATCH')
            self.assertEqual(params.get('updated_at'), ['eq.' + row['updated_at']])
            self.assertEqual(params.get('user_id'), ['eq.' + self.USER])
            self.assertEqual(params.get('id'), ['eq.tg-1'])
            self.assertEqual(req.headers.get('Prefer'), 'return=representation')
            return FakeResponse([])  # Outro dispositivo alterou a tarefa.
        with patch('cloud_memory.urlopen', side_effect=fake):
            self.assertFalse(self.mem.complete(5,17))
        self.assertEqual(len(calls), 2)

    def test_duplicate_update_can_be_deduplicated(self):
        with patch.object(self.mem,'_call',return_value=[]) as call:
            self.assertFalse(self.mem.claim_update(100))
            self.assertIn('ignore-duplicates',call.call_args.kwargs['prefer'])
