import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend import reader,source_locator,db


def test_joined_quantity_unit_highlights_exact_original_word():
    words=[word('42240SETS',.1,90,'OCR'),word('19,560KGS',.5,90,'OCR')]
    assert [b['text'] for b in source_locator.locate(words,'42240','42240SETS')]==['42240SETS']
    assert [b['text'] for b in source_locator.locate(words,'19,560','19,560KGS')]==['19,560KGS']
    assert not source_locator.locate(words,'4224O','42240SETS')
    assert not source_locator.locate([word('REF42240SETS',.1,90,'OCR')],'42240','')
from backend.app import app,add_record
from fixtures import pdf

def word(text,x,conf=None,layer='PDF text'):
    return {'text':text,'x':x,'y':.2,'w':.03,'h':.02,'confidence':conf,'layer':layer}

def test_literal_number_does_not_match_ocr_substitutions():
    words=[word('I200',.1),word('1200',.3),word('12.00',.5)]
    boxes=source_locator.locate(words,'1200','1200 PCS')
    assert len(boxes)==1 and boxes[0]['x']==.3
    assert source_locator.locate(words,'999','')==[]

def test_repeated_values_are_explicitly_ambiguous():
    words=[word('TOTAL',.1),word('100',.2),word('OTHER',.4),word('100',.5)]
    boxes=source_locator.locate(words,'100','')
    assert len(boxes)==2 and all(b['ambiguous'] for b in boxes)

def test_only_literal_low_confidence_words_are_flagged():
    boxes=source_locator.locate([word('MSCU6639870',.1,35,'OCR'),word('OTHER',.5,10,'OCR')],
        {'container_number':'MSCU6639870'},'MSCU6639870')
    assert len(boxes)==1 and boxes[0]['confidence']==35 and boxes[0]['attribute']=='container_number'

def test_pdf_boxes_match_rendered_orientation_and_page(tmp_path):
    path=tmp_path/'invoice.pdf';path.write_bytes(pdf('COMMERCIAL INVOICE\nInvoice No: TEST-908\nTotal: 23540.00 USD'))
    boxes=source_locator.locate(source_locator.layout(path,1,'PDF text'),'TEST-908','Invoice No: TEST-908')
    assert boxes and all(0<=b['x']<1 and 0<=b['y']<1 and b['confidence'] is None for b in boxes)
    with pytest.raises((IndexError,ValueError)):source_locator.layout(path,2,'PDF text')

def test_source_endpoint_uses_original_raw_and_rejects_reference(tmp_path):
    client=TestClient(app);h={'X-UI-Smart':'local'}
    cid=client.post('/api/cases',headers=h,json={'name':'TEST source'}).json()['case']['id']
    result=client.post(f'/api/cases/{cid}/documents',headers=h,files=[('files',('x.pdf',pdf('Invoice No: TEST-908')))]).json()
    did=result['results'][0]['id']
    db.execute('INSERT INTO pages VALUES (?,?,?,?,?,?,?)',(db.uid(),did,1,'Invoice No: TEST-908','PDF text','','[]'))
    with db.connect() as c:
        add_record(c,cid,did,{'kind':'field','key':'invoice_number','raw':'TEST-908','value':{'text':'MANUALLY-EDITED'},'page':1,'evidence':'Invoice No: TEST-908','method':'OpenAI'})
    rid=db.one('SELECT id FROM records WHERE document_id=?',(did,))['id']
    result=client.get(f'/api/records/{rid}/source')
    assert result.status_code==200,result.text
    assert result.json()['raw']=='TEST-908' and result.json()['boxes']
    client.patch(f'/api/documents/{did}/collection',headers=h,json={'collection':'reference'})
    assert client.get(f'/api/records/{rid}/source').status_code==409

def test_small_image_enlargement_is_bounded():
    im=Image.new('RGB',(500,700),'white')
    out=reader.prepare_ocr_image(im)
    assert out.size==(1600,2240) and im.size==(500,700)
