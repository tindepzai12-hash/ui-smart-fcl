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


def test_wrong_vessel_reading_highlights_name_cell_not_phones(monkeypatch):
    ocean={**word('Ocean',.07,90,'OCR'),'y':.6,'h':.01}
    vessel={**word('vessel',.12,90,'OCR'),'y':.6,'h':.01}
    name={**word('TESTJADE',.07,90,'OCR'),'y':.62,'w':.08}
    phones=[{**word(t,.5+i*.07,90,'OCR'),'y':.6} for i,t in enumerate(['TEL','39203000','FAX','39203070'])]
    monkeypatch.setattr(source_locator,'layout',lambda *a:[ocean,vessel,name,*phones])
    result=source_locator.inspect({'id':'d','path':'unused','name':'bill.pdf','ext':'.pdf'},
        {'key':'vessel','raw':'TESTIADE','evidence':'Ocean vessel TEL 39203000 FAX 39203070 TESTIADE','method':'OpenAI'},
        {'number':1,'method':'OCR','quality':'','text':'Ocean vessel TESTJADE'})
    assert [b['text'] for b in result['boxes']]==['TESTJADE']
    assert all(b['evidence_only'] for b in result['boxes'])
    assert 'chưa khớp' in result['message']


def test_bound_reader_cell_skips_slow_relocation_and_repeated_footer_name(monkeypatch):
    import json
    value=word('TESTJADE',.1,35,'OCR');value['y']=.37
    cell={'key':'vessel','value':'TESTJADE','words':[value]}
    page={'number':1,'method':'OCR','quality':'quality <source-cell>'+json.dumps(cell)+'</source-cell>',
          'text':'Ocean vessel: TESTJADE\nRepeated footer TESTJADE'}
    def unexpected(*a):raise AssertionError('Bound source must not repeat full-page OCR')
    monkeypatch.setattr(source_locator,'layout',unexpected)
    record={'key':'vessel','raw':'TESTJADE','evidence':'Ocean vessel: TESTJADE','method':'OpenAI'}
    result=source_locator.inspect({'id':'d','path':'unused','name':'bill.pdf','ext':'.pdf'},record,page)
    assert len(result['boxes'])==1 and result['boxes'][0]['y']==.37
    assert result['quality']=='quality'
    assert not result['boxes'][0]['evidence_only']
    record['raw']='TESTIADE'
    result=source_locator.inspect({'id':'d','path':'unused','name':'bill.pdf','ext':'.pdf'},record,page)
    assert result['boxes'][0]['evidence_only']
    # Foreign values or unbounded coordinates are never trusted as positions.
    cell['words'][0]['x']=1.2
    page['quality']='<source-cell>'+json.dumps(cell)+'</source-cell>'
    assert not source_locator.bound_reader_boxes(record,page)

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

def test_layout_reuses_coordinates_across_record_and_process_cache_misses(tmp_path,monkeypatch):
    path=tmp_path/'scan.png';Image.new('L',(500,700),255).save(path)
    monkeypatch.setattr(db,'DATA',tmp_path)
    calls=[]
    def read(image,psm=3):
        calls.append((image.mode,image.size,psm))
        return [word('1200',.3,90,'OCR')]
    monkeypatch.setattr(source_locator,'ocr_words',read)
    first=source_locator.layout(path,1,'OCR')
    source_locator._layout.cache_clear()
    for _ in range(5):assert source_locator.layout(path,1,'OCR')==first
    assert len(calls)==1
    # A different file or locator version must not reuse old positions.
    Image.new('L',(501,700),255).save(path)
    source_locator.layout(path,1,'OCR')
    assert len(calls)==2
    monkeypatch.setattr(source_locator,'LAYOUT_VERSION','next')
    source_locator._layout.cache_clear()
    source_locator.layout(path,1,'OCR')
    assert len(calls)==3

def test_scan_uses_one_segmentation_when_value_matches(tmp_path,monkeypatch):
    path=tmp_path/'scan.png';Image.new('L',(100,100),255).save(path)
    monkeypatch.setattr(db,'DATA',tmp_path)
    calls=[]
    monkeypatch.setattr(source_locator,'ocr_words',lambda im,psm=3:(calls.append(psm) or [word('1200',.2,90,'OCR')]))
    value=source_locator.inspect({'id':'d','path':str(path),'name':'scan.png','ext':'.png'},
        {'raw':'1200','evidence':'Total 1200','method':'OpenAI'},
        {'number':1,'method':'OCR','quality':'','text':'Total 1200'})
    assert value['boxes'] and calls==[11] and not value['retryable']

def test_timeout_returns_retryable_source_without_invented_boxes(tmp_path,monkeypatch):
    path=tmp_path/'scan.png';Image.new('L',(100,100),255).save(path)
    monkeypatch.setattr(db,'DATA',tmp_path)
    def timeout(*args):raise RuntimeError('Tesseract process timeout')
    monkeypatch.setattr(source_locator,'ocr_words',timeout)
    value=source_locator.inspect({'id':'d','path':str(path),'name':'scan.png','ext':'.png'},
        {'raw':'1200','evidence':'Total 1200','method':'OpenAI'},
        {'number':1,'method':'OCR','quality':'','text':'Total 1200'})
    assert value['retryable'] and not value['boxes']
    assert not list((tmp_path/'source-layouts').glob('*.json'))

def test_source_ocr_is_grayscale_bounded_and_has_short_timeout(monkeypatch):
    monkeypatch.setattr(reader,'ocr_status',lambda:{'ready':True,'cmd':'tesseract','languages':['eng']})
    seen={}
    def read(image,**kwargs):
        seen.update(mode=image.mode,size=image.size,timeout=kwargs['timeout'])
        return {'text':['1200'],'conf':['90'],'left':[10],'top':[20],'width':[30],'height':[10]}
    monkeypatch.setattr(reader.pytesseract,'image_to_data',read)
    with Image.new('RGB',(2400,3600),'white') as image:
        rows=source_locator.ocr_words(image)
        assert image.size==(2400,3600)
    assert seen=={'mode':'L','size':(1067,1600),'timeout':8}
    assert rows[0]['y']==.0125
