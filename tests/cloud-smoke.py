"""Explicit live smoke test. Creates and deletes only its own synthetic case."""
import os, sys, time, uuid, io, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'vendor'), str(ROOT / 'tests')]
import httpx
from openpyxl import load_workbook
from fixtures import INVOICE, PACKING, BL, image

def smoke(url, password):
    with httpx.Client(base_url=url, timeout=90, follow_redirects=False) as c:
        assert c.get('/healthz').json() == {'ok': True}
        assert c.get('/api/cases').status_code == 401
        assert c.post('/__cloud/login', headers={'origin': url}, data={'password': password}).status_code == 303
        health = c.get('/api/health').json()
        assert health['ocr']['ready'], health['ocr']
        assert {'eng', 'vie'} <= set(health['ocr']['languages'])
        headers = {'origin': url, 'x-ui-smart': 'local'}
        def post(path, **kwargs):
            r = c.post('/api' + path, headers=headers, **kwargs)
            r.raise_for_status()
            return r.json()
        case = post('/cases', json={'name': 'QA SYNTHETIC ' + uuid.uuid4().hex[:8], 'customer': 'NOT REAL CUSTOMER', 'mode': 'FCL'})['case']['id']
        job = None
        try:
            scan = io.BytesIO(); image(PACKING).save(scan, 'PNG')
            files = [('files', ('invoice.txt', INVOICE.encode(), 'text/plain')), ('files', ('packing.txt', PACKING.encode(), 'text/plain')), ('files', ('bl.txt', BL.encode(), 'text/plain')), ('files', ('packing-ocr.png', scan.getvalue(), 'image/png'))]
            uploaded = post('/cases/' + case + '/documents', files=files)
            assert all(d['status'] == 'uploaded' for d in uploaded['results'])
            job = post('/cases/' + case + '/process', json={'mode': 'local', 'allow_external': False})['id']
            for _ in range(120):
                state = c.get('/api/jobs/' + job).json()
                if state['status'] != 'running': break
                time.sleep(1)
            assert state['status'] == 'completed' and not state['errors'], state
            bundle = c.get('/api/cases/' + case).json()
            assert len(bundle['documents']) == 4 and all(d['status'] == 'read' for d in bundle['documents'])
            assert any(r['key'] == 'invoice_number' and '000123-A' in str(r['value']) for r in bundle['records'])
            blocked = c.post('/api/cases/' + case + '/export', headers=headers, json={'mode': 'Reviewed', 'workbook_type': 'A'})
            assert blocked.status_code == 409
            exported = post('/cases/' + case + '/export', json={'mode': 'Draft', 'workbook_type': 'A'})
            workbook = c.get(exported['download']); workbook.raise_for_status()
            wb = load_workbook(io.BytesIO(workbook.content), read_only=True)
            assert len(wb.sheetnames) == 7
            backup = post('/backup', json={})
            archive = c.get(backup['download']); archive.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
                assert any(name.endswith('smart.sqlite') for name in z.namelist())
            for name in ['invoice.txt', 'packing.txt', 'bl.txt', 'bl-conflict.txt']:
                assert c.get('/api/samples/' + name).status_code == 200
            print('LIVE PASS: auth, English/Vietnamese OCR, four-document FCL job, evidence records, Reviewed guard, 7-sheet Draft Excel, backup and samples.')
            print('OpenAI configured:', health['ai']['configured'], '; connected:', health['ai']['connected'])
        finally:
            if job:
                state = c.get('/api/jobs/' + job).json()
                if state.get('status') == 'running':
                    post('/jobs/' + job + '/cancel', json={})
                    for _ in range(70):
                        if c.get('/api/jobs/' + job).json().get('status') != 'running': break
                        time.sleep(1)
            cleanup = c.delete('/api/cases/' + case, headers=headers)
            cleanup.raise_for_status()

if __name__ == '__main__':
    smoke(os.environ['UI_SMART_SMOKE_URL'].rstrip('/'), os.environ['UI_SMART_PASSWORD'])
