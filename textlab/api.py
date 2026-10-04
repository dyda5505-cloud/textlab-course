import logging
import os
from flask import Flask, Response, jsonify, request
from . import store

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger('textlab.api')

def create_app(database=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 1_000_000
    path = database or os.environ.get('DATABASE_PATH', 'data/jobs.db')
    store.initialize(path)

    @app.get('/health')
    def health():
        store.statistics(path)
        return jsonify(status='ok')

    @app.post('/api/jobs')
    def submit():
        if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify(error='Размер запроса превышает 1 МБ'), 413
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get('text'), str):
            return jsonify(error='Поле text должно быть строкой'), 400
        text = payload['text']
        if not text.strip() or len(text) > 200_000:
            return jsonify(error='Введите от 1 до 200000 символов'), 400
        identifier = store.enqueue(path, text)
        logger.info('job_submitted id=%s characters=%d', identifier, len(text))
        return jsonify(id=identifier, status='queued'), 202

    @app.get('/api/jobs/<identifier>')
    def result(identifier):
        job = store.get_job(path, identifier)
        if job is None:
            return jsonify(error='Задача не найдена'), 404
        return jsonify(job)

    @app.get('/metrics')
    def metrics():
        counts = store.statistics(path)
        lines = ['# HELP textlab_jobs_submitted_total Total accepted analysis jobs.',
                 '# TYPE textlab_jobs_submitted_total counter',
                 f'textlab_jobs_submitted_total {sum(counts.values())}',
                 '# HELP textlab_jobs Current jobs by status.',
                 '# TYPE textlab_jobs gauge']
        for status in ('queued', 'running', 'done', 'failed'):
            lines.append(f'textlab_jobs{{status="{status}"}} {counts.get(status, 0)}')
        return Response('\n'.join(lines) + '\n', content_type='text/plain; version=0.0.4')

    return app
