from types import SimpleNamespace
import pytest
from backend import ai
from test_core import client,H,new,upload,process


def result():
    return ai.DocumentResult.model_validate({'document_type':'Invoice','classification_evidence':'COMMERCIAL INVOICE',
      'fields':[{'field_id':'invoice_number','raw_value':'A-001','source_page':1,'evidence_text':'Invoice No: A-001'},
                {'field_id':'invoice_total','raw_value':'99999','source_page':1,'evidence_text':'Amount: 120.00'}],
      'items':[],'containers':[]})


PAGES=[{'number':1,'text':'Commercial   Invoice\nInvoice No: A-001\nAmount: 120.00'}]


def test_valid_values_survive_but_invented_values_never_persist():
    records,rejected=ai.validated_subset(result(),PAGES)
    assert [r['raw'] for r in records]==['A-001']
    assert len(rejected)==1 and all(r['method']=='OpenAI' for r in records)


def test_missing_classification_quote_cannot_be_bypassed():
    data=result().model_dump();data['classification_evidence']='MISSING TITLE'
    with pytest.raises(ValueError,match='Phân loại AI'):
        ai.validated_subset(ai.DocumentResult.model_validate(data),PAGES)

def test_global_invoice_currency_and_row_unit_require_literal_cell_evidence():
    text='COMMERCIAL INVOICE\nBolts\n10\nPCS\n12.00\n120.00\nCurrency for all line amounts: USD.'
    data={'document_type':'Invoice','classification_evidence':'COMMERCIAL INVOICE','fields':[],
          'items':[{'line_number':'1','description':'Bolts','quantity':'10','unit':'PCS','unit_price':'12.00','line_amount':'120.00','currency':'USD',
                    'source_page':1,'evidence_text':'Bolts 10 PCS 12.00 120.00',
                    'cell_evidence':[{'attribute':'unit','evidence_text':'','start_line':4,'end_line':4},
                                     {'attribute':'currency','evidence_text':'','start_line':7,'end_line':7}]}],'containers':[]}
    pages=[{'number':1,'text':text}]
    records,rejected=ai.validated_subset(ai.DocumentResult.model_validate(data),pages)
    assert not rejected and records[0]['value']['unit']=='PCS' and records[0]['value']['currency']=='USD'
    data['items'][0]['cell_evidence'][1]['start_line']=4
    data['items'][0]['cell_evidence'][1]['end_line']=4
    with pytest.raises(ValueError,match='Không có giá trị AI'):
        ai.validated_subset(ai.DocumentResult.model_validate(data),pages)


def test_non_invoice_items_do_not_enter_invoice_scope():
    data={'document_type':'Packing List','classification_evidence':'PACKING LIST','fields':[],
          'items':[{'line_number':'1','description':'Bolts','quantity':'10','source_page':1,'evidence_text':'Bolts 10'}],'containers':[]}
    records,rejected=ai.validated_subset(ai.DocumentResult.model_validate(data),[{'number':1,'text':'PACKING LIST\nBolts 10'}])
    assert not rejected and records[0]['value']['scope']=='packing'
    assert 'scope' not in records[0]['raw']


def test_partial_ai_rejection_is_visible_and_blocks_reviewed(monkeypatch):
    ai.configure('synthetic-secret','gpt-4.1-mini')
    monkeypatch.setattr(ai,'OpenAI',lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(parse=lambda **kwargs:
        SimpleNamespace(output_parsed=result(),usage=SimpleNamespace(input_tokens=20,output_tokens=20)))))
    try:
        case=new();upload(case,[('unique.txt',(PAGES[0]['text']+'\n'+case).encode())])
        bundle,job=process(case,'openai')
        assert not job['errors'] and len(job['warnings'])==1
        assert [r['raw'] for r in bundle['records']]==['A-001']
        assert bundle['documents'][0]['status']=='read' and bundle['documents'][0]['error']
        assert any(c['key'].startswith('reading:') and c['result']=='Needs Verification' for c in bundle['checks'])
        assert all(r['status']=='pending' for r in bundle['records'])
        assert client.post('/api/cases/'+case+'/export',headers=H,json={'mode':'Reviewed'}).status_code==409
    finally:ai.remove()
