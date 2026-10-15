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


def test_origin_needs_its_own_business_label_for_fields_and_items():
    text='COMMERCIAL INVOICE\nInvoice No: TEST-91\nSeller address: Example City, CHINA\nBLUE BOLTS 20\nCountry of Origin: VIETNAM'
    pages=[{'number':1,'text':text}]
    candidate=output('Invoice','COMMERCIAL INVOICE',[field('invoice_number','TEST-91','Invoice No: TEST-91'),
        field('origin','CHINA','Seller address: Example City, CHINA')])
    candidate.items=[ai.ItemResult(line_number='1',description='BLUE BOLTS',quantity='20',origin='CHINA',source_page=1,
        evidence_text='BLUE BOLTS 20',cell_evidence=[ai.CellEvidence(attribute='origin',evidence_text='Seller address: Example City, CHINA')])]
    records,rejected=ai.validated_subset(candidate,pages)
    assert [r['key'] for r in records]==['invoice_number'] and len(rejected)==2
    candidate.fields[1]=field('origin','VIETNAM','Country of Origin: VIETNAM')
    candidate.items[0].origin='VIETNAM';candidate.items[0].cell_evidence[0].evidence_text='Country of Origin: VIETNAM'
    records,rejected=ai.validated_subset(candidate,pages)
    assert not rejected and records[-1]['raw']['origin']=='VIETNAM'
    assert not ai.origin_supported('CHINA','Seller address: Example City, CHINA\nCountry of Origin: VIETNAM')


def test_bounded_repair_can_add_a_proven_quantity_unit_but_cannot_change_value():
    pages=[{'number':1,'text':'COMMERCIAL INVOICE\nQuantity\n(KGS)\nBLUE BOLTS 21000'}]
    first=output('Invoice','COMMERCIAL INVOICE',[field('goods_quantity','21000','BLUE BOLTS 21000')])
    first.items=[ai.ItemResult(line_number='1',description='BLUE BOLTS',quantity='21000',source_page=1,evidence_text='BLUE BOLTS 21000')]
    records,rejected=ai.validated_subset(first,pages)
    targets=ai.repair_targets(first,records,rejected,pages)
    assert targets['items'] and 'goods_quantity' in targets['fields']
    second=first.model_copy(deep=True)
    second.fields[0].unit='KGS';second.fields[0].unit_evidence='(KGS)'
    second.items[0].unit='KGS';second.items[0].cell_evidence=[ai.CellEvidence(attribute='unit',evidence_text='(KGS)')]
    merged=ai.merge_supported_repair(first,second,pages,targets)
    checked,_=ai.validated_subset(merged,pages)
    assert checked[0]['value']['unit']=='KG' and checked[1]['raw']['unit']=='KGS'
    # A literal alternative number exists, but a repair cannot replace the accepted one.
    pages[0]['text']+='\nOther value: 100'
    second.fields[0].raw_value='100';second.fields[0].evidence_text='Other value: 100'
    merged=ai.merge_supported_repair(first,second,pages,targets)
    assert merged.fields[0].raw_value=='21000' and merged.fields[0].unit is None


def test_package_count_cannot_be_packing_list_number():
    pages=[{'number':1,'text':'PACKING LIST\nInvoice No: INV-9\nTOTAL PACKAGES:840BAGS\nPacking List No: PL-9'}]
    candidate=output('Packing List','PACKING LIST',[field('invoice_number','INV-9','Invoice No: INV-9'),
        field('packing_number','840BAGS','TOTAL PACKAGES:840BAGS')])
    records,rejected=ai.validated_subset(candidate,pages)
    assert [r['key'] for r in records]==['invoice_number'] and len(rejected)==1
    candidate.fields[1]=field('packing_number','PL-9','Packing List No: PL-9')
    records,rejected=ai.validated_subset(candidate,pages)
    assert not rejected and records[-1]['raw']=='PL-9'


def test_commercial_comparison_preserves_real_differences_and_explains_unit_conversion():
    from backend.validation import build_checks,field_comparable
    from backend.dictionary import default_requirements
    from backend.normalize import normalize
    assert field_comparable('buyer',normalize('EXAMPLE CO.,LTD.'))==field_comparable('buyer',normalize('example co.,ltd'))
    assert field_comparable('buyer',normalize('EXAMPLE CO.,LTD.'))!=field_comparable('buyer',normalize('OTHER CO.,LTD.'))
    assert field_comparable('seller_address',normalize('ADD: Example road, CITY'))==field_comparable('seller_address',normalize('example Road, city'))
    assert normalize('04,Aug., 2026','date')['text']=='2026-08-04'
    assert normalize('04,Aug., 2026','date')['warning'] is None
    docs=[{'id':'i','name':'invoice','type':'Invoice','status':'read','type_verified':True},
          {'id':'c','name':'contract','type':'Contract','status':'read','type_verified':True}]
    records=[]
    for did,kind,quantity,port in [('i','Invoice','21000 KGS','Example Port'),('c','Contract','21.0 MT','Alternative/Example Port')]:
        for key,raw,typ in [('goods_quantity',quantity,'quantity'),('port_loading',port,'text')]:
            records.append({'id':did+key,'document_id':did,'kind':'field','key':key,'value':normalize(raw,typ),'status':'pending','page':1})
    checks=build_checks({'mode':'FCL','requirements':default_requirements()},docs,records)
    quantity=next(c for c in checks if c['key']=='field:goods_quantity')
    assert quantity['result']=='Matched' and '1 MT = 1000 KG' in quantity['detail']['reason']
    assert next(c for c in checks if c['key']=='field:port_loading')['result']=='Needs Verification'
    records[-2]['value']=normalize('22.0 MT','quantity')
    checks=build_checks({'mode':'FCL','requirements':default_requirements()},docs,records)
    assert next(c for c in checks if c['key']=='field:goods_quantity')['result']=='Needs Verification'
