"""Versioned SQLite storage. All values are bound parameters."""
import json, os, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv('UI_SMART_DATA', str(ROOT / 'data'))).resolve()
DATA.mkdir(parents=True, exist_ok=True)
for folder in ['files', 'exports', 'backups', 'templates']:
    (DATA / folder).mkdir(exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return uuid.uuid4().hex
def encode(value): return json.dumps(value, ensure_ascii=False)

@contextmanager
def connect():
    conn = sqlite3.connect(DATA / 'smart.sqlite', timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally: conn.close()

def migrate():
    with connect() as c:
        c.executescript((ROOT / 'backend' / 'migrations' / '001.sql').read_text(encoding='utf-8'))
        columns = {r['name'] for r in c.execute('PRAGMA table_info(documents)')}
        if 'collection' not in columns:
            c.execute("ALTER TABLE documents ADD COLUMN collection TEXT NOT NULL DEFAULT 'document' CHECK(collection IN ('document','reference'))")
        if 'collection_reason' not in columns:
            c.execute("ALTER TABLE documents ADD COLUMN collection_reason TEXT NOT NULL DEFAULT ''")
        if 'extraction_required' not in columns:
            c.execute('ALTER TABLE documents ADD COLUMN extraction_required INTEGER NOT NULL DEFAULT 0')
        c.execute('PRAGMA journal_mode=WAL')
        # Recover work interrupted by an application restart. Files are retained.
        c.execute("UPDATE documents SET status='error', error='Xử lý bị gián đoạn. Chọn thử lại.' WHERE status='reading'")
        c.execute("UPDATE cases SET status='Needs verification' WHERE status='Reading'")

def one(sql, args=()):
    with connect() as c:
        row=c.execute(sql,args).fetchone()
        return dict(row) if row else None
def rows(sql, args=()):
    with connect() as c: return [dict(r) for r in c.execute(sql,args).fetchall()]
def execute(sql,args=()):
    with connect() as c: c.execute(sql,args)

def audit(c, case_id, action, entity='', before=None, after=None, reason='', actor='Nhân viên local'):
    c.execute('INSERT INTO audit VALUES (?,?,?,?,?,?,?,?,?)',
              (uid(),case_id,now(),actor,action,entity,encode(before),encode(after),reason))

def touch(c, case_id):
    c.execute("UPDATE cases SET updated_at=?, reviewed_at=NULL, status='Needs verification', revision=revision+1 WHERE id=?",(now(),case_id))
