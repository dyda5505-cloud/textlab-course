from concurrent.futures import ThreadPoolExecutor
import pytest
from textlab.analysis import analyze
from textlab.api import create_app
from textlab.worker import process_once
from textlab import store

@pytest.fixture
def database(tmp_path):
    path = str(tmp_path / 'jobs.db')
    store.initialize(path)
    return path

@pytest.mark.parametrize('text,words,unique', [
    ('', 0, 0), ('Привет, ПРИВЕТ! Мир.', 3, 2),
    ("don't stop", 2, 2), ('a_b 123', 3, 3), ('你好 世界', 2, 2),
    ('Straße STRASSE', 2, 1), ('   !? ', 0, 0),
])
def test_unicode_analysis(text, words, unique):
    result = analyze(text)
    assert result['characters'] == len(text)
    assert result['words'] == words
    assert result['unique_words'] == unique

def test_order_and_top_limit():
    result = analyze('b a b a c')
    assert result['top_words'] == [
        {'word': 'a', 'count': 2}, {'word': 'b', 'count': 2}, {'word': 'c', 'count': 1}]
    assert len(analyze(' '.join(f'word{i}' for i in range(20)))['top_words']) == 10

def test_async_lifecycle(database):
    client = create_app(database).test_client()
    response = client.post('/api/jobs', json={'text': 'мир мир'})
    assert response.status_code == 202
    identifier = response.json['id']
    assert client.get(f'/api/jobs/{identifier}').json['status'] == 'queued'
    assert process_once(database)
    result = client.get(f'/api/jobs/{identifier}').json
    assert result['status'] == 'done'
    assert result['result']['words'] == 2
    assert not process_once(database)
    metrics = client.get('/metrics').text
    assert 'textlab_jobs_submitted_total 1' in metrics
    assert 'textlab_jobs{status="done"} 1' in metrics
    assert client.get('/health').json == {'status': 'ok'}

@pytest.mark.parametrize('payload', [None, [], {}, {'text': 123}, {'text': ''},
                                         {'text': ' '}, {'text': 'x' * 200001}])
def test_reject_bad_input(database, payload):
    client = create_app(database).test_client()
    assert client.post('/api/jobs', json=payload).status_code == 400
    assert store.statistics(database) == {}

def test_http_errors(database):
    client = create_app(database).test_client()
    assert client.get('/api/jobs/missing').status_code == 404
    assert client.post('/api/jobs', data='not json', content_type='application/json').status_code == 400
    assert client.post('/api/jobs', data='x' * 1_000_001).status_code == 413

def test_claim_is_atomic(database):
    ids = {store.enqueue(database, 'hi') for _ in range(20)}
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs = list(pool.map(lambda _: store.claim(database), range(20)))
    assert {job['id'] for job in jobs} == ids
    assert store.claim(database) is None

def test_recover_abandoned_job(database):
    identifier = store.enqueue(database, 'recover')
    assert store.claim(database)['id'] == identifier
    with store.connection(database) as db:
        db.execute('UPDATE jobs SET started=0 WHERE id=?', (identifier,))
    assert store.claim(database)['id'] == identifier

def test_worker_failure(database, monkeypatch):
    identifier = store.enqueue(database, 'bad')
    def fail(_):
        raise ValueError('private details')
    monkeypatch.setattr('textlab.worker.analyze', fail)
    assert process_once(database)
    job = store.get_job(database, identifier)
    assert job['status'] == 'failed'
    assert job['error'] == 'Ошибка обработки текста'

def test_rollback(database):
    with pytest.raises(RuntimeError):
        with store.connection(database) as db:
            db.execute('INSERT INTO jobs(id,text,status) VALUES (?,?,?)', ('id', 't', 'queued'))
            raise RuntimeError('rollback')
    assert store.get_job(database, 'id') is None
