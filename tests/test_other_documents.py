import io
from types import SimpleNamespace
from openpyxl import load_workbook
from backend import ai, reader
from backend.app import bundle
from test_commercial import create, sample
from test_core import client, H, upload, process


def test_six_main_types_and_unrelated_documents_are_separated():
    cid = create()
    main = ['invoice','packing','booking','contract','po','co']
    upload(cid, [(f'{i+1}.txt',sample(name+'.txt')) for i,name in enumerate(main)] + [
        ('7.txt',b'DELIVERY ORDER\nConsignee: UNRELATED COMPANY\nGross Weight: 9999 KG'),
        ('8.txt',b'MEETING AGENDA\nStaff lunch schedule\nLocation: Meeting room A'),
    ])
    b, job = process(cid)
    assert not job['errors']
    assert {d['type'] for d in b['documents']} == {'Invoice','Packing List','Booking','Contract','Purchase Order','C/O'}
    assert {d['type'] for d in b['other_files']} == {'Delivery Order','Other'}
    assert all(d['collection_reason'] and d['pages'] for d in b['other_files'])
    others = {d['id'] for d in b['other_files']}
    assert not any(r['document_id'] in others for r in b['records'])
    assert not any(any(s.get('id') in others for s in c['detail'].get('sources',[])) for c in b['checks'])
    assert not any(c['key'] in ['classification:'+id for id in others] for c in b['checks'])
    assert all(r['value'].get('text') != 'UNRELATED COMPANY' for r in b['records'])
    cases = client.get('/api/cases').json()
    assert next(c for c in cases if c['id']==cid)['document_count'] == 6
    for d in b['other_files']:
        assert client.get('/api/documents/'+d['id']+'/original').status_code == 200
        assert client.get('/api/documents/'+d['id']+'/pages/1').status_code == 200
    r = client.post('/api/cases/'+cid+'/export',headers=H,json={'mode':'Draft'})
    assert r.status_code == 200,r.text
    wb = load_workbook(io.BytesIO(client.get(r.json()['download']).content))
    values = [str(v) for ws in [wb['THONG_TIN_CHUNG_TU'],wb['DOI_CHIEU_CHUNG_TU']] for row in ws.values for v in row]
    assert not any('UNRELATED COMPANY' in v or '9999' in v for v in values)
    wb.close()
    # An excluded file is not repeatedly sent through OCR/AI on the next run.
    b, job = process(cid)
    assert len(b['other_files']) == 2 and job['total'] == 6


def test_openai_routes_other_and_manual_correction_is_reversible(monkeypatch):
    cid = create()
    upload(cid,[('1.txt',b'INTERNAL NOTE\nInvoice No: ABC-01')])
    monkeypatch.setattr(ai,'key',lambda:'test-key')
    monkeypatch.setattr(ai,'analyze',lambda *args: (SimpleNamespace(document_type='Other',classification_evidence='INTERNAL NOTE'),[],{'rejected':[]}))
    from test_reference_files import process as run_process
    b, job = run_process(cid,'openai')
    assert not job['errors']
    assert not b['documents'] and len(b['other_files']) == 1
    d = b['other_files'][0]
    assert d['classification_evidence'] == 'INTERNAL NOTE'
    bad = client.patch('/api/documents/'+d['id']+'/collection',headers=H,json={'collection':'document','document_type':'B/L'})
    assert bad.status_code == 422 and bundle(cid)['other_files']
    r = client.patch('/api/documents/'+d['id']+'/collection',headers=H,json={'collection':'document','document_type':'Invoice','reason':'Staff checked original'})
    assert r.status_code == 200,r.text
    assert r.json()['documents'][0]['type_verified']
    b,job = run_process(cid,'openai')
    assert not job['errors'] and not b['other_files']
    assert b['documents'][0]['type'] == 'Invoice' and b['documents'][0]['error']
    assert not b['records']  # Conflicting machine classification is not silently accepted.


def test_unreadable_files_still_require_attention(monkeypatch):
    cid = create()
    upload(cid,[('1.txt',b'Unreadable example')])
    def fail(*args): raise ValueError('Unreadable test input')
    monkeypatch.setattr(reader,'read_document',fail)
    b,job = process(cid)
    assert job['errors'] and not b['other_files']
    assert b['documents'][0]['status'] == 'error'


def test_combined_invoice_packing_list_is_still_a_main_document():
    cid = create()
    upload(cid,[('1.txt',b'COMMERCIAL INVOICE & PACKING LIST\nInvoice No: INV-01\nPacking List No: PL-01')])
    b,job = process(cid)
    assert not job['errors'] and not b['other_files']
    assert b['documents'][0]['type'] == 'Invoice & Packing List'
