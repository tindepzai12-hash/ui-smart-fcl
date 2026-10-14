"""Restore only while stopped; stage/validate before moving current data aside."""
import os,sys,zipfile,sqlite3,socket,shutil
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def restore(archive,data=None,check_server=True):
    target=Path(data or ROOT/'data').resolve()
    if not target.is_relative_to(ROOT):raise ValueError('Target must remain inside project')
    if check_server:
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1',8765))==0:raise ValueError('Dừng backend trước khi restore')
    stage=target.parent/('restore-stage-'+os.urandom(8).hex());stage.mkdir()
    try:
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>2*1024**3:raise ValueError('Backup vượt 2 GB')
            for info in z.infolist():
                p=(stage/info.filename).resolve()
                if not p.is_relative_to(stage) or Path(info.filename).parts[0] not in ['smart.sqlite','files','exports','templates']:raise ValueError('Backup chứa đường dẫn không hợp lệ')
                if info.is_dir():p.mkdir(parents=True,exist_ok=True)
                else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
        with closing(sqlite3.connect(stage/'smart.sqlite')) as c:
            with c:
                if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity check failed')
                if c.execute('SELECT max(version) FROM schema_versions').fetchone()[0]!=1:raise ValueError('Schema backup chưa hỗ trợ')
                tables=[('documents','files'),('exports','exports'),('templates','templates')]
                if c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bundle_sources'").fetchone():
                    tables.append(('bundle_sources','files'))
                for table,folder in tables:
                    for id,path in c.execute(f'SELECT id,path FROM {table}').fetchall():
                        file=Path(path).name
                        if not (stage/folder/file).is_file():raise ValueError('Backup thiếu file '+file)
                        c.execute(f'UPDATE {table} SET path=? WHERE id=?',(str(target/folder/file),id))
        old=target.parent/('data-before-restore-'+os.urandom(8).hex())
        if target.exists():target.rename(old)
        try:stage.rename(target)
        except Exception:
            if old.exists():old.rename(target)
            raise
        return old
    finally:
        if stage.exists() and stage.resolve().is_relative_to(ROOT):shutil.rmtree(stage)
if __name__=='__main__':
    try:print('Restored. Previous data:',restore(sys.argv[1]))
    except Exception as e:print(str(e));raise SystemExit(1)
