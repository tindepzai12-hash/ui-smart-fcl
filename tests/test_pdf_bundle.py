import io, zipfile
from pathlib import Path
import pytest
from pypdf import PdfReader, PdfWriter
from backend import db, pdf_bundle, reader, extraction
from backend.app import JOBS
from test_core import client, H, new, upload, process
from fixtures import INVOICE, PACKING, BL, pdf


def packet():
    writer = PdfWriter()
    for text in [INVOICE, PACKING, BL]:
        writer.add_page(PdfReader(io.BytesIO(pdf(text))).pages[0])
    buffer = io.BytesIO(); writer.write(buffer)
    return buffer.getvalue()


def prepare():
    case = new(); data = packet()
    upload(case, [('packet.pdf', data)])
    result, job = process(case)
    assert len(job['errors']) == 1 and 'Tách' in job['errors'][0]['error']
    doc = result['documents'][0]
    assert doc['mixed_pdf'] and len(doc['split_suggestion']) == 3
    assert not result['records'], 'Never extract a mixed packet under one document type'
    return case, doc, data


def split(doc, groups=None):
    return client.post('/api/documents/'+doc['id']+'/split', headers=H, json={'groups':groups or doc['split_suggestion']})


def test_split_preserves_original_and_separate_roles_backup_excel(tmp_path):
    case, doc, data = prepare()
    assert client.patch('/api/documents/'+doc['id']+'/classification', headers=H, json={'type':'Invoice'}).status_code == 409
    response = split(doc); assert response.status_code == 200, response.text
    result = response.json()
    assert len(result['documents']) == 3
    assert [d['type'] for d in result['documents']] == ['Invoice','Packing List','B/L']
    assert all(not d['type_verified'] for d in result['documents'])
    assert all(r['status'] == 'pending' for r in result['records'])
    assert len([r for r in result['records'] if r['kind'] == 'item']) == 2
    for index, child in enumerate(result['documents'], 1):
        assert child['source']['start_page'] == child['source']['end_page'] == index
        assert len(child['pages']) == 1
        records = [r for r in result['records'] if r['document_id'] == child['id']]
        assert all(r['page'] == 1 for r in records)
    original = result['documents'][0]['source']
    assert client.get('/api/sources/'+original['id']+'/original').content == data
    assert upload(case, [('reupload.pdf',data)]).json()['results'][0]['status'] == 'duplicate'
    exported = client.post('/api/cases/'+case+'/export', headers=H, json={'mode':'Draft'}).json()
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(client.get(exported['download']).content))
    assert 'SHA-256' in str(list(wb['NGUON_VA_LICH_SU'].values)); wb.close()
    backup = client.post('/api/backup', headers=H).json()
    backup_bytes = client.get(backup['download']).content
    with zipfile.ZipFile(io.BytesIO(backup_bytes)) as z:
        path = Path(db.one('SELECT path FROM bundle_sources WHERE id=?',(original['id'],))['path'])
        assert z.read('files/'+path.name) == data
    from scripts.restore import restore
    import sqlite3
    archive = tmp_path/'split-backup.zip'; archive.write_bytes(backup_bytes)
    destination = db.ROOT/'tmp'/('restore-split-'+case)
    restore(archive,destination,check_server=False)
    with sqlite3.connect(destination/'smart.sqlite') as restored:
        restored_path = Path(restored.execute('SELECT path FROM bundle_sources WHERE id=?',(original['id'],)).fetchone()[0])
        assert restored_path.is_relative_to(destination) and restored_path.read_bytes() == data
    assert client.post('/api/cases/'+case+'/export', headers=H, json={'mode':'Reviewed'}).status_code == 409
    assert client.delete('/api/cases/'+case, headers=H).status_code == 200
    assert not path.exists()


@pytest.mark.parametrize('groups', [
    [{'start':1,'end':2,'type':'Invoice'},{'start':2,'end':3,'type':'B/L'}],
    [{'start':1,'end':1,'type':'Invoice'},{'start':3,'end':3,'type':'B/L'}],
    [{'start':1,'end':1,'type':'Invoice'},{'start':2,'end':2,'type':'Packing List'}],
])
def test_split_rejects_overlap_missing_or_unallocated_pages(groups):
    _, doc, data = prepare()
    assert split(doc, groups).status_code == 422
    assert db.one('SELECT id FROM documents WHERE id=?',(doc['id'],))
    assert Path(db.one('SELECT path FROM documents WHERE id=?',(doc['id'],))['path']).read_bytes() == data


def test_split_cannot_discard_verified_or_edited_records():
    case, doc, _ = prepare()
    response = client.post('/api/cases/'+case+'/records', headers=H, json={'kind':'field','key':'invoice_number','value':'MANUAL','document_id':doc['id'],'page':1,'note':'Manual data retained'})
    assert response.status_code == 200
    assert split(doc).status_code == 409


def test_split_transaction_rolls_back_if_child_write_fails(monkeypatch):
    import backend.app as module
    case, doc, _ = prepare()
    def fail(*_): raise ValueError('Injected write failure')
    monkeypatch.setattr(module, 'add_record', fail)
    before = set((db.DATA/'files').glob('*'))
    assert split(doc).status_code == 422
    assert db.one('SELECT id FROM documents WHERE id=?',(doc['id'],))
    assert not db.one('SELECT id FROM bundle_sources WHERE case_id=?',(case,))
    assert set((db.DATA/'files').glob('*')) == before


def test_page_grouping_continuations_and_cloud_concurrency(monkeypatch):
    groups = pdf_bundle.suggest([{'number':1,'text':INVOICE},{'number':2,'text':'Continuation without heading'},{'number':3,'text':PACKING}])
    assert groups[0]['end'] == 2 and groups[1]['type'] == 'Packing List'
    case = new(); other = new()
    upload(case, [('invoice.txt',INVOICE.encode())])
    monkeypatch.setenv('UI_SMART_CLOUD','1')
    JOBS['test-busy'] = {'case_id':other, 'status':'running'}
    try:
        assert client.post('/api/cases/'+case+'/process',headers=H,json={}).status_code == 409
        assert client.get('/api/cases/'+other).json()['active_job']['status'] == 'running'
    finally: JOBS.pop('test-busy',None)


def test_six_page_packets_are_real_text_and_real_scan():
    paths = [db.ROOT/'samples/fcl-text.pdf', db.ROOT/'samples/fcl-scan.pdf']
    expected = ['Invoice','Packing List','B/L','Arrival Notice','Delivery Order','C/O']
    for index, path in enumerate(paths):
        raw = PdfReader(path)
        assert len(raw.pages) == 6
        assert all(bool(p.extract_text().strip()) == (index == 0) for p in raw.pages)
        pages = reader.read_document(path)
        assert [g['type'] for g in pdf_bundle.suggest(pages)] == expected
        assert all(p['method'] == ('PDF text' if index == 0 else 'OCR') for p in pages)
        records = extraction.extract([pages[0]],'Invoice')
        items = [r for r in records if r['kind']=='item']
        assert len(items) == 2
        assert [r['value']['product_code'] for r in items] == ['00128','00456']
        from decimal import Decimal
        assert [Decimal(r['value']['line_amount']) for r in items] == [Decimal('15300'),Decimal('8240')]
        assert any(r['key']=='invoice_number' and 'INV-000287-26' in str(r['value']) for r in records)


@pytest.mark.parametrize('name',['fcl-text.pdf','fcl-scan.pdf'])
def test_complete_six_document_workflow(name):
    case = new()
    upload(case, [(name,(db.ROOT/'samples'/name).read_bytes())])
    result, job = process(case)
    assert len(job['errors']) == 1 and not result['records']
    response = split(result['documents'][0]); assert response.status_code == 200, response.text
    result = response.json()
    assert len(result['documents']) == 6
    assert len([r for r in result['records'] if r['kind']=='item']) == 4
    containers = [r for r in result['records'] if r['kind']=='container']
    assert len(containers) == 4
    assert {r['value']['container_number'] for r in containers} == {'MSCU6639870'}
    assert {r['value']['seal_number'] for r in containers} == {'MA26101408'}
    from decimal import Decimal
    weights = [r['value'] for r in result['records'] if r['key']=='gross_weight']
    assert len(weights) == 2 and all(Decimal(v['number']) == 5200 and v['unit']=='KG' for v in weights)
    for doc in result['documents']:
        assert client.patch('/api/documents/'+doc['id']+'/classification',headers=H,json={'type':doc['type']}).status_code == 200
    from backend.app import bundle
    for record in bundle(case)['records']:
        if record['value'].get('warning'):
            # This known raster fixture has one noisy row label. Simulate staff correction,
            # retaining the OCR raw value and evidence rather than accepting it silently.
            assert record['kind'] == 'item' and record['value']['product_code'] == '00456'
            value = dict(record['value']) # UI sends the original warning; backend must recompute it.
            value['line_number'] = '2'
            edited = client.patch('/api/records/'+record['id'],headers=H,json={'value':value,'version':record['version'],'note':'Synthetic QA: compared row 2 against original scan'})
            assert edited.status_code == 200
            record = next(r for r in edited.json()['records'] if r['id']==record['id'])
        verified = client.post('/api/records/'+record['id']+'/verify',headers=H,json={'status':'verified','version':record['version'],'note':'Synthetic QA only: compared every field against expected fixture'})
        assert verified.status_code == 200, verified.text
    result = bundle(case)
    assert not result['blockers'], result['blockers']
    assert client.post('/api/cases/'+case+'/review',headers=H).status_code == 200
    exported = client.post('/api/cases/'+case+'/export',headers=H,json={'mode':'Reviewed'})
    assert exported.status_code == 200, exported.text
