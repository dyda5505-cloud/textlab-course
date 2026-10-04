"""Persistent queue shared by backend and worker via a Docker volume."""
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

@contextmanager
def connection(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def initialize(path):
    with connection(path) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE IF NOT EXISTS jobs '
                   '(id TEXT PRIMARY KEY, text TEXT NOT NULL, status TEXT NOT NULL, '
                   'result TEXT, error TEXT, started REAL)')

def enqueue(path, text):
    identifier = str(uuid4())
    with connection(path) as db:
        db.execute('INSERT INTO jobs(id,text,status) VALUES (?,?,?)',
                   (identifier, text, 'queued'))
    return identifier

def get_job(path, identifier):
    with connection(path) as db:
        row = db.execute('SELECT id,status,result,error FROM jobs WHERE id=?',
                         (identifier,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result['result'] = json.loads(result['result']) if result['result'] else None
    return result

def claim(path):
    with connection(path) as db:
        db.execute('BEGIN IMMEDIATE')
        # Abandoned tasks become eligible again after a worker crash.
        db.execute("UPDATE jobs SET status='queued',started=NULL "
                   "WHERE status='running' AND started < ?", (time.time() - 300,))
        row = db.execute("SELECT id,text FROM jobs WHERE status='queued' "
                         'ORDER BY rowid LIMIT 1').fetchone()
        if row:
            db.execute("UPDATE jobs SET status='running',started=? WHERE id=?",
                       (time.time(), row['id']))
            return dict(row)
        return None

def finish(path, identifier, result=None, error=None):
    with connection(path) as db:
        db.execute('UPDATE jobs SET status=?,result=?,error=? WHERE id=?',
                   ('failed' if error else 'done',
                    json.dumps(result, ensure_ascii=False) if result is not None else None,
                    error, identifier))

def statistics(path):
    with connection(path) as db:
        rows = db.execute('SELECT status,COUNT(*) AS count FROM jobs GROUP BY status').fetchall()
    return {row['status']: row['count'] for row in rows}
