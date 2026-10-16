"""Regression checks for unchanged inputs, changed prompts, and staff resolutions."""
from types import SimpleNamespace
import time
import pytest
from fastapi.testclient import TestClient
from backend import ai, app, db, consistency
from backend import reader, pipeline
from test_shipment_consistency import document,record
from backend.normalize import normalize

PAGES=[{'number':1,'text':'COMMERCIAL INVOICE\nInvoice No: REP-901','method':'PDF text','quality':'','tables':[]}]


def test_equivalent_packets_with_new_ids_reuse_review_but_changed_source_misses(monkeypatch):
    calls=[]
    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_parsed=kwargs['text_format'].model_validate({'issues':[]}),usage=None)
    monkeypatch.setattr(ai,'OpenAI',lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    monkeypatch.setattr(ai,'key',lambda:'synthetic-not-a-key')
    db.execute('DELETE FROM ai_cache')
    for n in range(5):
        cid=db.uid()
        db.execute('INSERT INTO cases(id,name,customer,mode,status,requirements,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
                   (cid,'repeat','test','FCL','Draft','{}',db.now(),db.now()))
        doc={**document('doc'+str(n),'Invoice'),'hash':'a'*64,'name':'same.pdf'}
        row=record('row'+str(n),doc['id'],'invoice_number',normalize('TEST-100'))
        row['evidence']='Invoice No: TEST-100'
        assert not consistency.run_ai_review(cid,[doc],[row],[],True)
        assert not consistency.run_ai_review(cid,[doc],[row],[],True)
    assert len(calls)==1
    row['value']=normalize('TEST-101')
    assert not consistency.run_ai_review(cid,[doc],[row],[],True)
    assert len(calls)==2

@pytest.fixture
def fake_ai(monkeypatch):
    calls=[]
    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_parsed=ai.DocumentResult(document_type='Invoice',classification_evidence='COMMERCIAL INVOICE',
            fields=[ai.FieldResult(field_id='invoice_number',raw_value='REP-901',source_page=1,evidence_text='Invoice No: REP-901')],items=[],containers=[]),
            usage=SimpleNamespace(input_tokens=1,output_tokens=1),model='gpt-4.1-mini-test-snapshot')
    monkeypatch.setattr(ai,'OpenAI',lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    monkeypatch.setattr(ai,'_key','synthetic-not-a-key')
    monkeypatch.setattr(ai,'_model','gpt-4.1-mini')
    db.execute('DELETE FROM ai_cache')
    return calls

def test_changed_guidance_must_miss_extraction_cache(fake_ai,monkeypatch):
    doc={'type':'Other','hash':'a'*64}
    ai.analyze(None,doc,PAGES)
    monkeypatch.setattr(ai,'EXAMPLES',ai.EXAMPLES+'\nUpdated source pointer guidance.')
    ai.analyze(None,doc,PAGES)
    assert len(fake_ai)==2, 'Different actual system prompts incorrectly shared the same cache entry'

def test_changed_schema_must_miss_extraction_cache(fake_ai,monkeypatch):
    doc={'type':'Other','hash':'a'*64}
    ai.analyze(None,doc,PAGES)
    original=ai.DocumentResult.model_json_schema
    monkeypatch.setattr(ai.DocumentResult,'model_json_schema',classmethod(lambda cls,**kw:{**original(**kw),'description':'Updated extraction schema'}))
    ai.analyze(None,doc,PAGES)
    assert len(fake_ai)==2

def test_unconfirmed_type_is_not_prompt_context_and_file_identity_is_bound(fake_ai):
    ai.analyze(None,{'type':'Other','hash':'a'*64},PAGES)
    ai.analyze(None,{'type':'Invoice','hash':'a'*64},PAGES)
    assert len(fake_ai)==1
    assert '"selected_type": null' in fake_ai[0]['input'][0]['content']
    ai.analyze(None,{'type':'Invoice','type_verified':True,'hash':'a'*64},PAGES)
    assert len(fake_ai)==2
    ai.analyze(None,{'type':'Invoice','type_verified':True,'hash':'b'*64},PAGES)
    assert len(fake_ai)==3

def test_cold_and_warm_extraction_equal_five_times(fake_ai):
    doc={'type':'Other','hash':'a'*64}
    result,records,info=ai.analyze(None,doc,PAGES)
    for _ in range(5):
        again,rows,meta=ai.analyze(None,doc,PAGES)
        assert again==result and rows==records and meta['rejected']==info['rejected']
        assert meta['source']=='cache'
    assert len(fake_ai)==1

def process(client,cid,did=None,mode='local'):
    route='/api/documents/'+did if did else '/api/cases/'+cid
    response=client.post(route+'/process',json={'mode':mode,'allow_external':mode=='openai'});assert response.status_code==200
    for _ in range(500):
        job=client.get('/api/jobs/'+response.json()['id']).json()
        if job['status']!='running':break
        time.sleep(.01)
    assert job['status']=='completed' and not job['errors']
    return client.get('/api/cases/'+cid).json()

def test_reprocessing_preserves_source_ids_and_existing_check_resolution():
    client=TestClient(app.app,headers={'X-UI-Smart':'local'})
    cid=client.post('/api/cases',json={'name':'Repeatability regression'}).json()['case']['id']
    client.post('/api/cases/'+cid+'/documents',files={'files':('invoice.txt',PAGES[0]['text'].encode(),'text/plain')})
    first=process(client,cid);did=first['documents'][0]['id']
    before={r['id']:(r['raw'],r['value'],r['status']) for r in first['records']}
    db.execute("UPDATE checks SET resolution='Staff reviewed original source' WHERE case_id=? AND key='field:invoice_number'",(cid,))
    for _ in range(5):
        again=process(client,cid,did)
        assert {r['id']:(r['raw'],r['value'],r['status']) for r in again['records']}==before
        check=next(x for x in again['checks'] if x['key']=='field:invoice_number')
        assert check['resolution']=='Staff reviewed original source'

def test_unchanged_packet_does_not_repeat_ai_review(monkeypatch):
    client=TestClient(app.app,headers={'X-UI-Smart':'local'})
    cid=client.post('/api/cases',json={'name':'Packet repeatability regression'}).json()['case']['id']
    calls=[]
    def parse(**kw):
        calls.append(kw)
        return SimpleNamespace(output_parsed=kw['text_format'](issues=[],description_assessments=[],contextual_assessments={}),usage=SimpleNamespace(input_tokens=1,output_tokens=1))
    monkeypatch.setattr(ai,'OpenAI',lambda **kw:SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    monkeypatch.setattr(ai,'_key','synthetic-not-a-key')
    assert not consistency.run_ai_review(cid,[],[],reuse=True)
    for _ in range(5):assert not consistency.run_ai_review(cid,[],[],reuse=True)
    assert len(calls)==1,'Identical packet was sent for another stochastic model judgment'

@pytest.mark.parametrize('scanned',[False,True])
def test_five_fresh_pdf_uploads_and_reprocess_match_pages_cache_sqlite(fake_ai,monkeypatch,scanned):
    from fixtures import pdf,scan
    if scanned and not reader.ocr_status()['ready']:pytest.skip('Real OCR unavailable in this environment')
    blob=(scan if scanned else pdf)(PAGES[0]['text'])
    reads=[];original=reader.read_document
    def read(*args,**kwargs):
        pages=original(*args,**kwargs);reads.append(pages);return pages
    monkeypatch.setattr(reader,'read_document',read)
    monkeypatch.setattr(consistency,'run_ai_review',lambda *args,**kwargs:'')
    client=TestClient(app.app,headers={'X-UI-Smart':'local'})
    baseline=None
    for _ in range(5):
        cid=client.post('/api/cases',json={'name':'PDF repeatability regression'}).json()['case']['id']
        client.post('/api/cases/'+cid+'/documents',files={'files':('invoice.pdf',blob,'application/pdf')})
        first=process(client,cid,mode='openai');did=first['documents'][0]['id']
        again=process(client,cid,did,mode='openai')
        assert [(r['id'],r['raw'],r['value'],r['status']) for r in first['records']]==[(r['id'],r['raw'],r['value'],r['status']) for r in again['records']]
        pages=db.rows('SELECT number,text,method,quality,table_json FROM pages WHERE document_id=? ORDER BY number',(did,))
        values=[(r['key'],r['raw'],r['value'],r['page'],r['evidence'],r['status']) for r in again['records']]
        if baseline is None:baseline=(pages,values)
        assert (pages,values)==baseline
        from backend.validation import unpack
        assert [(unpack(r)['raw'],unpack(r)['value']) for r in db.rows('SELECT * FROM records WHERE document_id=? ORDER BY rowid',(did,))]==[(r['raw'],r['value']) for r in again['records']]
    assert len(reads)==5 and len(fake_ai)==1

def test_changed_reader_version_refreshes_saved_pages(monkeypatch):
    client=TestClient(app.app,headers={'X-UI-Smart':'local'})
    cid=client.post('/api/cases',json={'name':'Reader version regression'}).json()['case']['id']
    client.post('/api/cases/'+cid+'/documents',files={'files':('invoice.txt',PAGES[0]['text'].encode(),'text/plain')})
    first=process(client,cid);did=first['documents'][0]['id']
    old=db.one('SELECT reader_signature FROM documents WHERE id=?',(did,))['reader_signature']
    fingerprint=pipeline.fingerprint;reads=[];read=reader.read_document
    monkeypatch.setattr(pipeline,'fingerprint',lambda scope='extraction':'updated-reader-version' if scope=='reader' else fingerprint(scope))
    monkeypatch.setattr(reader,'read_document',lambda *args,**kw:(reads.append(args[0]) or read(*args,**kw)))
    stale=client.get('/api/cases/'+cid).json()
    assert stale['documents'][0]['needs_reprocess']
    assert any('đọc lại bằng phiên bản hiện tại' in b for b in stale['blockers'])
    saved=next(c for c in stale['checks'] if c['key']=='field:invoice_number')
    assert saved['result']=='Needs Verification' and saved['detail']['stale_source']
    process(client,cid,did)
    assert len(reads)==1
    assert db.one('SELECT reader_signature FROM documents WHERE id=?',(did,))['reader_signature']!=old
    process(client,cid,did);assert len(reads)==1
    assert not client.get('/api/cases/'+cid).json()['documents'][0]['needs_reprocess']


def test_stale_machine_discrepancy_is_warning_without_mutating_saved_review():
    import copy
    checks=[{'key':'field:vessel','result':'Mismatch','resolution':'Prior staff note',
             'detail':{'reason':'Old OCR differs','category':'difference','sources':[{'id':'r'}]}}]
    before=copy.deepcopy(checks)
    viewed=app.stale_reading_checks(checks,[{'id':'d','needs_reprocess':True}],[{'id':'r','document_id':'d'}])
    assert checks==before
    assert viewed[0]['result']=='Needs Verification'
    assert viewed[0]['detail']['category']=='stale_reading'
    assert viewed[0]['detail']['previous_resolution']=='Prior staff note'
    assert not viewed[0]['resolution']


def test_stale_reader_blocks_reviewed_export_even_when_other_blockers_are_empty(monkeypatch):
    client=TestClient(app.app,headers={'X-UI-Smart':'local'})
    cid=client.post('/api/cases',json={'name':'Stale approval gate'}).json()['case']['id']
    client.post('/api/cases/'+cid+'/documents',files={'files':('invoice.txt',PAGES[0]['text'].encode(),'text/plain')})
    first=process(client,cid)
    db.execute('UPDATE documents SET reader_signature=? WHERE id=?',('obsolete-reader',first['documents'][0]['id']))
    db.execute("UPDATE cases SET status='Reviewed',reviewed_at=? WHERE id=?",(db.now(),cid))
    monkeypatch.setattr(app.validation,'blockers',lambda *args:[])
    assert client.post('/api/cases/'+cid+'/review').status_code==409
    assert client.post('/api/cases/'+cid+'/export',json={'mode':'Reviewed'}).status_code==409

def test_changed_machine_value_replaces_stale_row_but_keeps_manual_record():
    client=TestClient(app.app,headers={'X-UI-Smart':'local'})
    cid=client.post('/api/cases',json={'name':'Replacement regression'}).json()['case']['id']
    client.post('/api/cases/'+cid+'/documents',files={'files':('invoice.txt',PAGES[0]['text'].encode(),'text/plain')})
    first=process(client,cid);did=first['documents'][0]['id'];row=first['records'][0]
    machine={k:row[k] for k in ['kind','key','page','raw','value','evidence','method']}
    db.execute("UPDATE records SET method='Manual edit',status='verified' WHERE id=?",(row['id'],))
    changed={**machine,'raw':'REP-902','value':{**machine['value'],'text':'REP-902'},'evidence':'Invoice No: REP-902'}
    with db.connect() as c:app.replace_extracted_records(c,cid,did,[changed])
    with db.connect() as c:app.replace_extracted_records(c,cid,did,[changed])
    rows=db.rows('SELECT * FROM records WHERE document_id=? ORDER BY rowid',(did,))
    assert len(rows)==2
    assert rows[0]['id']==row['id'] and rows[0]['method']=='Manual edit' and rows[0]['status']=='verified'
    with db.connect() as c:app.replace_extracted_records(c,cid,did,[])
    assert [r['id'] for r in db.rows('SELECT * FROM records WHERE document_id=?',(did,))]==[row['id']]
