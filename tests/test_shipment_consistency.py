"""Shipment discrepancies must preserve both source values and their roles."""
import copy
from backend import consistency, validation, extraction, pdf_bundle
from backend.normalize import normalize
from backend.dictionary import default_requirements

def document(id,kind='Packing List'):
    return {'id':id,'name':id+'.pdf','type':kind,'status':'read','type_verified':False}

def record(id,doc,key,value,kind='field'):
    return {'id':id,'document_id':doc,'key':key,'value':value,'raw':value.get('text',value),
            'kind':kind,'status':'pending','evidence':'Source evidence '+id,'page':1,'method':'OpenAI text'}

def checks(docs,rows):
    return validation.build_checks({'mode':'FCL','requirements':default_requirements()},docs,rows)

def test_actual_gross_conflict_and_unknown_weight_do_not_mix():
    docs=[document('pl'),document('decl','Customs Declaration'),document('warehouse','Warehouse Receipt')]
    rows=[record('a','pl','gross_weight',normalize('489.00 KG','weight')),
          record('b','decl','gross_weight',normalize('515,08 KGM','weight')),
          record('c','warehouse','cargo_weight',normalize('515.080','weight'))]
    original=copy.deepcopy(rows)
    c=next(c for c in checks(docs,rows) if c['key']=='field:gross_weight')
    assert c['result']=='Mismatch'
    assert [s['value']['number'] for s in c['detail']['sources']]==['489.00','515.08']
    assert {s['id'] for s in c['detail']['sources']}=={'a','b'}
    assert rows==original

def test_two_packing_versions_differ_and_units_convert_without_verification():
    docs=[document('pl1'),document('pl2')]
    rows=[record('a','pl1','gross_weight',normalize('489 KG','weight')),
          record('b','pl2','gross_weight',normalize('0.4890 MT','weight'))]
    c=next(c for c in checks(docs,rows) if c['key']=='field:gross_weight')
    assert c['result']=='Matched'
    rows[1]['value']=normalize('515.08 KG','weight')
    assert next(c for c in checks(docs,rows) if c['key']=='field:gross_weight')['result']=='Mismatch'

def test_net_and_gross_not_compared_as_same_field_but_impossible_order_flagged():
    docs=[document('pl')]
    rows=[record('a','pl','gross_weight',normalize('489 KG','weight')),
          record('b','pl','net_weight',normalize('391.20 KG','weight'))]
    assert not consistency.additional_checks(docs,rows)
    rows[1]['value']=normalize('500 KG','weight')
    c=consistency.additional_checks(docs,rows)[0]
    assert c['result']=='Mismatch' and c['key']=='weight-order:pl'

def test_item_alignment_requires_code_and_same_currency_for_price():
    docs=[document('inv1','Invoice'),document('inv2','Invoice')]
    rows=[record('a','inv1','goods_item',{'product_code':'A1','quantity':'600','unit':'PCS','unit_price':'6.53','currency':'USD'},'item'),
          record('b','inv2','goods_item',{'product_code':'A1','quantity':'601','unit':'PCS','unit_price':'7.00','currency':'EUR'},'item')]
    keys={c['key'] for c in consistency.additional_checks(docs,rows)}
    assert 'item:A1:quantity' in keys and 'item:A1:currency' in keys
    assert 'item:A1:unit_price' not in keys
    rows[1]['value']['product_code']='B1'
    assert not consistency.additional_checks(docs,rows)

def test_ai_review_signature_changes_only_when_comparison_inputs_change():
    docs=[document('pl')];rows=[record('a','pl','gross_weight',normalize('489 KG','weight'))]
    old=consistency.signature(docs,rows)
    rows[0]['status']='verified'
    assert consistency.signature(docs,rows)==old
    rows[0]['value']=normalize('515.08 KG','weight')
    assert consistency.signature(docs,rows)!=old

def test_combined_pl_invoice_keeps_pages_and_is_not_forced_to_split():
    pages=[{'number':1,'text':'PACKING LIST\nNo: AB2507002\nGross Weight: 489.00 KGS'},
           {'number':2,'text':'COMMERCIAL INVOICE\nInvoice No: AB2507002\nTotal: 4242.00 USD'}]
    assert extraction.classify(pages)[0]=='Invoice & Packing List'
    assert not pdf_bundle.is_mixed(pages)

def test_supporting_document_titles_not_other():
    for title,kind in [('TỜ KHAI HÀNG HÓA XUẤT KHẨU','Customs Declaration'),
                       ('ĐỦ ĐIỀU KIỆN QUA KHU VỰC GIÁM SÁT HẢI QUAN','Customs Release'),
                       ('YÊU CẦU NHẬP KHO','Warehouse Receipt')]:
        assert extraction.classify([{'text':title}])[0]==kind

def test_printed_month_dates_compare_without_guessing_day_month_order():
    assert normalize('JUL. 07, 2025','date')['text']=='2025-07-07'
    assert not normalize('JUL. 07, 2025','date')['warning']
    assert normalize('01/07/2025','date')['warning']

def test_generic_and_detailed_descriptions_are_not_declared_wrong_by_wording():
    docs=[document('pl'),document('inv','Invoice')]
    rows=[record('a','pl','cargo_description',normalize('Bicycle components')),
          record('b','inv','cargo_description',normalize('Aluminum alloy carrier'))]
    assert next(c for c in checks(docs,rows) if c['key']=='field:cargo_description')['result']=='Needs Verification'

def test_ai_cannot_invent_sources_mix_weight_roles_or_merge_different_item_codes(monkeypatch):
    import json
    from types import SimpleNamespace
    from backend import ai,db
    docs=[document('pl'),document('decl','Customs Declaration')]
    rows=[record('a','pl','gross_weight',normalize('489 KG','weight')),
          record('b','decl','gross_weight',normalize('515.08 KG','weight')),
          record('n','decl','net_weight',normalize('391.20 KG','weight')),
          record('i','pl','goods_item',{'product_code':'A1'},'item'),
          record('j','decl','goods_item',{'product_code':'B1'},'item')]
    issues=[{'field_id':'gross_weight','record_ids':['a','invented'],'reason':'An invented source'},
            {'field_id':'gross_weight','record_ids':['a','n'],'reason':'Cross-role comparison'},
            {'field_id':'goods_item','record_ids':['i','j'],'reason':'Different product codes'},
            {'field_id':'gross_weight','record_ids':['a','b'],'reason':'Hai giá trị gross khác nhau trên nguồn.'}]
    captured=[]
    monkeypatch.setattr(db,'execute',lambda sql,args:captured.append((sql,args)))
    monkeypatch.setattr(ai,'key',lambda:'synthetic-not-real')
    def parse(**kwargs):
        assert 'AI_SHIPMENT' not in kwargs['input'][0]['content'] or 'Never' in kwargs['input'][0]['content']
        return SimpleNamespace(output_parsed=kwargs['text_format'].model_validate({'issues':issues}),usage=SimpleNamespace(input_tokens=1,output_tokens=1))
    monkeypatch.setattr(ai,'OpenAI',lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    assert consistency.run_ai_review('test',docs,rows)==''
    saved=json.loads(captured[-1][1][2])
    assert len(saved)==1
    assert [s['id'] for s in saved[0]['detail']['sources']]==['a','b']
    assert saved[0]['detail']['sources'][0]['value']==rows[0]['value']

def test_declaration_line_quantities_not_allowed_as_shipment_total():
    from backend.dictionary import FIELDS
    assert 'Customs Declaration' not in FIELDS['goods_quantity']['documents']
    assert normalize('515.08 Kilogam','weight')['unit']=='KG'
    assert normalize('515.08 unknown','weight')['warning']

def test_combined_packing_rows_do_not_enter_invoice_arithmetic():
    docs=[document('combined','Invoice & Packing List')]
    rows=[record('pl','combined','goods_item',{'description':'CARRIER','quantity':'600','unit':'PCS','scope':'packing'},'item'),
          record('inv','combined','goods_item',{'description':'CARRIER','quantity':'600','unit':'PCS','unit_price':'6.53','line_amount':'3918.00'},'item'),
          record('total','combined','invoice_total',normalize('3918.00 USD','number'))]
    cs=checks(docs,rows)
    assert not any(c['key']=='arithmetic:pl' for c in cs)
    assert next(c for c in cs if c['key']=='total:combined')['result']=='Matched'

def test_different_item_readings_on_two_pages_of_one_pdf_are_compared():
    docs=[document('two-pl')]
    a=record('a','two-pl','goods_item',{'product_code':'A1','quantity':'600','unit':'PCS','scope':'packing'},'item')
    b=record('b','two-pl','goods_item',{'product_code':'A1','quantity':'601','unit':'PCS','scope':'packing'},'item');b['page']=2
    assert consistency.additional_checks(docs,[a,b])[0]['result']=='Mismatch'

def test_printed_packing_footer_recovers_aligned_net_and_package_totals():
    from backend import ai
    text='PACKING LIST\nCTN\nDescription\nNet Wt. (kgs)\nGross Wt. (kgs)\nCARRIER 360.00 450.00\n56 391.20 489.00\nTare Weight (kgs):\nTotal (kgs): 489.00'
    pages=[{'number':1,'text':text,'tables':[[['CTN','Description','Net Wt. (kgs)','Gross Wt. (kgs)'],
            ['50','CARRIER','360.00','450.00'],['56','','391.20','489.00'],['Tare Weight (kgs):','','',''],['Total (kgs):','','','489.00']]]}]
    result=ai.DocumentResult.model_validate({'document_type':'Packing List','classification_evidence':'PACKING LIST','fields':[],'items':[],'containers':[]})
    grounded=ai.ground_source_format(result,pages)
    fields={f.field_id:f for f in grounded.fields}
    assert fields['net_weight'].raw_value=='391.20' and fields['gross_weight'].raw_value=='489.00'
    assert fields['packages'].raw_value=='56' and fields['packages'].unit=='CTN'
    pages[0]['tables'][0][2][1]='Another product'
    assert not ai.ground_source_format(result,pages).fields
