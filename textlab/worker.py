import logging
import os
import time
from .analysis import analyze
from . import store

logger = logging.getLogger('textlab.worker')

def process_once(path):
    job = store.claim(path)
    if job is None:
        return False
    try:
        result = analyze(job['text'])
        store.finish(path, job['id'], result=result)
        logger.info('job_completed id=%s words=%d', job['id'], result['words'])
    except Exception:
        logger.exception('job_failed id=%s', job['id'])
        store.finish(path, job['id'], error='Ошибка обработки текста')
    return True

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    path = os.environ.get('DATABASE_PATH', 'data/jobs.db')
    store.initialize(path)
    while True:
        if not process_once(path):
            time.sleep(0.5)

if __name__ == '__main__':
    main()
