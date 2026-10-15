import time
from types import SimpleNamespace
import pytest
from backend import ai, db, reader
from backend.app import bundle
from test_core import client, H, upload
from test_commercial import create


def output(kind, quote, fields=None):
    return ai.DocumentResult(document_type=kind,classification_evidence=quote,fields=fields or [],items=[],containers=[])


def field(key,value,quote):
    return ai.FieldResult(field_id=key,raw_value=value,source_page=1,evidence_text=quote)


def wait(job):
    assert job.status_code==200,job.text
    for _ in range(300):
        j=client.get('/api/jobs/'+job.json()['id']).json()
        if j['status']!='running': return j
        time.sleep(.01)
    raise AssertionError('job timeout')


def test_confirmed_type_changes_cache_and_extracts_only_source_supported_fields(monkeypatch):
    calls=[]
    text='Faded title\nInvoice No: Z-81\n'+db.uid()
    pages=[{'number':1,'text':text}]
    def parse(**kwargs):
        calls.append(kwargs)
        assert ai.NO_INFERENCE_POLICY in kwargs['input'][0]['content']
        result=output('Other','Faded title') if len(calls)==1 else output('Invoice','Invoice No: Z-81',[field('invoice_number','Z-81','Invoice No: Z-81')])
        return SimpleNamespace(output_parsed=result,usage=None)
    monkeypatch.setattr(ai,'OpenAI',lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    monkeypatch.setattr(ai,'key',lambda:'synthetic-test-key')
    assert ai.analyze(None,{'type':'Other'},pages)[0].document_type=='Other'
    result,records,meta=ai.analyze(None,{'type':'Invoice','type_verified':True},pages)
    assert len(calls)==2 and meta['source']=='api'
    assert result.document_type=='Invoice' and [r['raw'] for r in records]==['Z-81']
    ai.analyze(None,{'type':'Invoice','type_verified':True},pages)
    assert len(calls)==2  # cache is bound to policy and confirmed type


def test_wrong_manual_type_does_not_turn_generic_meeting_date_into_invoice(monkeypatch):
    pages=[{'number':1,'text':'STAFF MEETING\nDate: 2026-05-01\n'+db.uid()}]
    # Even if the model disobeys, backend must discard these fabricated business roles.
    candidate=output('Invoice','STAFF MEETING',[field('invoice_date','2026-05-01','Date: 2026-05-01')])
    monkeypatch.setattr(ai,'OpenAI',lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(parse=lambda **kwargs:SimpleNamespace(output_parsed=candidate,usage=None))))
    monkeypatch.setattr(ai,'key',lambda:'synthetic-test-key')
    result,records,_=ai.analyze(None,{'type':'Invoice','type_verified':True},pages)
    assert result.document_type=='Other' and not records


def test_literal_quantity_is_not_net_weight_and_missing_amount_is_not_calculated():
    pages=[{'number':1,'text':'COMMERCIAL INVOICE\nInvoice No: T-81\nQuantity: 20 KG\nUnit price: 3 USD'}]
    candidate=output('Invoice','COMMERCIAL INVOICE',[
        field('invoice_number','T-81','Invoice No: T-81'),
        field('net_weight','20 KG','Quantity: 20 KG'),
        field('invoice_total','60','Quantity: 20 KG\nUnit price: 3 USD')])
    records,rejected=ai.validated_subset(candidate,pages)
    assert [r['key'] for r in records]==['invoice_number'] and len(rejected)==2


def test_selected_document_processing_requires_consent_and_does_not_read_siblings(monkeypatch):
    cid=create();upload(cid,[('1.txt',b'Invoice No: T-1'),('2.txt',b'Invoice No: T-2')])
    first,second=bundle(cid)['documents']
    r=client.patch('/api/documents/'+first['id']+'/classification',headers=H,json={'type':'Invoice'})
    assert r.status_code==200 and r.json()['documents'][0]['extraction_required']
    assert any(c['key']=='extraction:'+first['id'] for c in r.json()['checks'])
    monkeypatch.setattr(ai,'key',lambda:'synthetic-test-key')
    assert client.post('/api/documents/'+first['id']+'/process',headers=H,json={'mode':'openai'}).status_code==422
    seen=[];original=reader.read_document
    def read(path,*args):
        seen.append(str(path));assert second['id'] not in str(path)
        return original(path,*args)
    monkeypatch.setattr(reader,'read_document',read)
    j=wait(client.post('/api/documents/'+first['id']+'/process',headers=H,json={'mode':'local'}))
    assert not j['errors'] and j['total']==1 and len(seen)==1
    b=bundle(cid)
    assert not b['documents'][0]['extraction_required'] and b['documents'][1]['status']=='uploaded'
    assert [r['raw'] for r in b['records']]==['T-1']


def test_restored_document_requires_new_extraction_and_other_files_cannot_be_read_directly():
    cid=create();upload(cid,[('1.txt',b'Invoice No: T-9')]);d=bundle(cid)['documents'][0]
    client.patch('/api/documents/'+d['id']+'/collection',headers=H,json={'collection':'reference'})
    assert client.post('/api/documents/'+d['id']+'/process',headers=H,json={}).status_code==409
    restored=client.patch('/api/documents/'+d['id']+'/collection',headers=H,json={'collection':'document','document_type':'Invoice'}).json()
    assert restored['documents'][0]['extraction_required'] and restored['documents'][0]['type_verified']
    j=wait(client.post('/api/documents/'+d['id']+'/process',headers=H,json={'mode':'local'}))
    assert not j['errors'] and bundle(cid)['records'][0]['raw']=='T-9'
