import io, time
from types import SimpleNamespace
from PIL import Image
from fastapi.testclient import TestClient
from backend import app as module, db, reader, ai
from backend.app import app, bundle
from fixtures import INVOICE

client = TestClient(app)
H = {'X-UI-Smart': 'local'}

def new():
    return client.post('/api/cases', headers=H, json={'name': 'TEST - separated collections'}).json()['case']['id']

def image():
    buf = io.BytesIO()
    Image.new('RGB', (100, 100), 'blue').save(buf, 'PNG')
    return buf.getvalue()

def upload(cid, path, name, data):
    r = client.post('/api/cases/' + cid + '/' + path, headers=H, files=[('files', (name, data))])
    assert r.status_code == 200, r.text
    return r.json()

def process(cid, mode='local'):
    r = client.post('/api/cases/' + cid + '/process', headers=H, json={'mode': mode, 'allow_external': mode == 'openai'})
    assert r.status_code == 200, r.text
    jid = r.json()['id']
    for _ in range(300):
        job = client.get('/api/jobs/' + jid).json()
        if job['status'] != 'running':
            return bundle(cid), job
        time.sleep(.01)
    raise AssertionError('timeout')

def move(did, target):
    r = client.patch('/api/documents/' + did + '/collection', headers=H, json={'collection': target})
    assert r.status_code == 200, r.text
    return r.json()

def test_reference_upload_has_no_effect_on_workflow_and_never_read(monkeypatch):
    cid = new()
    before = bundle(cid)
    ref = upload(cid, 'reference-files', 'invoice.png', image())
    did = ref['results'][0]['id']
    after = ref['bundle']
    assert not after['documents'] and not after['records'] and len(after['reference_files']) == 1
    assert after['case']['revision'] == before['case']['revision']
    assert after['blockers'] == before['blockers']
    assert client.get('/api/documents/' + did + '/preview/1').status_code == 200
    assert client.get('/api/documents/' + did + '/original').content == image()
    assert client.post('/api/cases/' + cid + '/process', headers=H, json={}).status_code == 422
    assert client.patch('/api/documents/' + did + '/classification', headers=H, json={'type': 'Invoice'}).status_code == 409
    upload(cid, 'documents', '1.txt', INVOICE.encode())
    original = reader.read_document
    def read(path, *args):
        assert str(path).endswith('.txt'), 'Reference image must not be read'
        return original(path, *args)
    monkeypatch.setattr(reader, 'read_document', read)
    after, job = process(cid)
    assert not job['errors'] and len(after['documents']) == 1 and after['records']
    duplicate = upload(cid, 'documents', 'bill-of-lading.png', image())
    assert duplicate['results'][0]['status'] == 'duplicate'

def test_move_hides_records_from_checks_export_and_restores_pending():
    cid = new()
    did = upload(cid, 'documents', '1.txt', INVOICE.encode())['results'][0]['id']
    before, _ = process(cid)
    saved_ids = {r['id'] for r in before['records']}
    after = move(did, 'reference')
    assert not after['documents'] and not after['records'] and len(after['reference_files']) == 1
    assert not any(c['key'] == 'total:' + did for c in after['checks'])
    assert db.rows('SELECT id FROM records WHERE document_id=?', (did,))
    record = before['records'][0]
    assert client.post('/api/records/' + record['id'] + '/verify', headers=H, json={'status':'verified', 'version':record['version']}).status_code == 409
    assert client.post('/api/cases/' + cid + '/records', headers=H, json={'kind':'field', 'key':'invoice_number', 'value':'BAD', 'note':'test note', 'document_id':did}).status_code == 409
    restored = move(did, 'document')
    assert not restored['reference_files'] and len(restored['documents']) == 1
    assert {r['id'] for r in restored['records']} == saved_ids
    assert all(r['status'] == 'pending' for r in restored['records'])
    assert not restored['documents'][0]['type_verified']
    assert client.get('/api/cases').json()[0]['document_count'] == 1

def test_ai_routes_clear_photo_before_ocr_and_never_extracts(monkeypatch):
    cid = new()
    upload(cid, 'documents', 'packing-list.png', image())
    monkeypatch.setattr(ai, 'key', lambda: 'test-key')
    monkeypatch.setattr(ai, 'route_image', lambda *args: ai.ImageRoute(category='reference', certainty='clear', reason='Ảnh container hiện trường'))
    def forbidden(*args, **kwargs): raise AssertionError('Photo must never reach OCR or extraction')
    monkeypatch.setattr(reader, 'read_document', forbidden)
    monkeypatch.setattr(ai, 'analyze', forbidden)
    b, job = process(cid, 'openai')
    assert not job['errors'] and not b['documents'] and not b['records']
    assert b['reference_files'][0]['collection_reason'] == 'Ảnh container hiện trường'

def test_scan_or_document_screenshot_stays_document(monkeypatch):
    cid = new()
    upload(cid, 'documents', 'container.png', image())
    monkeypatch.setattr(ai, 'key', lambda: 'test-key')
    monkeypatch.setattr(ai, 'route_image', lambda *args: ai.ImageRoute(category='document', certainty='clear', reason='Ảnh chụp hóa đơn'))
    monkeypatch.setattr(reader, 'read_document', lambda *args: [{'number':1,'text':INVOICE,'tables':[], 'method':'test OCR','quality':''}])
    monkeypatch.setattr(ai, 'analyze', lambda *args: (SimpleNamespace(document_type='Invoice', classification_evidence='COMMERCIAL INVOICE'), [], {'rejected':[]}))
    b, job = process(cid, 'openai')
    assert not job['errors'] and not b['reference_files'] and b['documents'][0]['type'] == 'Invoice'

def test_ambiguous_image_is_not_forced_into_reference_or_extracted(monkeypatch):
    cid = new()
    upload(cid, 'documents', '1.png', image())
    monkeypatch.setattr(ai, 'key', lambda: 'test-key')
    monkeypatch.setattr(ai, 'route_image', lambda *args: ai.ImageRoute(category='uncertain', certainty='uncertain', reason='Ảnh bị cắt'))
    monkeypatch.setattr(reader, 'read_document', lambda *args: [{'number':1,'text':INVOICE,'tables':[], 'method':'test OCR','quality':''}])
    monkeypatch.setattr(ai, 'analyze', lambda *args: (_ for _ in ()).throw(AssertionError('Do not extract ambiguous images')))
    b, job = process(cid, 'openai')
    assert not job['errors'] and not b['reference_files'] and not b['records']
    assert b['documents'][0]['type'] == 'Other' and b['documents'][0]['error']
