import copy,json
from types import SimpleNamespace
from backend import ai,consistency,db,validation
from backend.normalize import normalize,source_number_convention
from test_shipment_consistency import document,record
from backend.dictionary import default_requirements


def test_money_convention_is_proven_in_own_document_not_chosen_to_match():
    value=normalize('4.242 USD','number')
    pages=[{'number':3,'text':'Trị giá hóa đơn 3.918  Đơn giá hóa đơn 6,53 - USD - PCE\nĐơn giá hóa đơn 0,54 - USD - PCE'}]
    actual=source_number_convention(value,'invoice_total','Customs Declaration',pages)
    assert actual['number']=='4242' and not actual['warning']
    assert actual['text']=='4.242 USD' and actual['normalization_evidence'][0]['page']==3
    # A genuinely different printed total is not rewritten to agree.
    assert source_number_convention(normalize('4.243 USD','number'),'invoice_total','Customs Declaration',pages)['number']=='4243'
    assert source_number_convention(value,'invoice_total','Invoice',pages)==value
    assert source_number_convention(value,'invoice_total','Customs Declaration',[{'number':1,'text':'Total 4.242 USD'}])==value
    assert source_number_convention(value,'invoice_total','Customs Declaration',pages+[{'number':4,'text':'Đơn giá hóa đơn 6.53 USD'}])==value


def test_contextual_money_validation_preserves_raw_and_does_not_hide_gross():
    pages=[{'number':1,'text':'Tờ khai hàng hóa xuất khẩu\nTổng trị giá hóa đơn FOB - USD - 4.242 - A'},
           {'number':3,'text':'Đơn giá hóa đơn 6,53 - USD - PCE'}]
    data=ai.DocumentResult(document_type='Customs Declaration',classification_evidence='Tờ khai hàng hóa xuất khẩu',
        fields=[ai.FieldResult(field_id='invoice_total',raw_value='4.242',unit='USD',unit_evidence='USD',source_page=1,evidence_text=pages[0]['text'])],items=[],containers=[])
    result=ai.validate_result(data,pages)[0]
    assert result['raw']=='4.242' and result['value']['number']=='4242'
    docs=[document('inv','Invoice'),document('decl','Customs Declaration')]
    rows=[record('a','inv','invoice_total',normalize('4,242.00 USD','number')),
          record('b','decl','invoice_total',result['value']),
          record('g1','inv','gross_weight',normalize('489.00 KG','weight')),
          record('g2','decl','gross_weight',normalize('515,08 KGM','weight'))]
    checks=validation.build_checks({'mode':'FCL','requirements':default_requirements()},docs,rows)
    assert next(c for c in checks if c['key']=='field:invoice_total')['result']=='Matched'
    assert next(c for c in checks if c['key']=='field:gross_weight')['result']=='Mismatch'
    rows[1]['value']=source_number_convention(normalize('4.243 USD','number'),'invoice_total','Customs Declaration',pages)
    assert next(c for c in validation.build_checks({'mode':'FCL','requirements':default_requirements()},docs,rows) if c['key']=='field:invoice_total')['result']=='Mismatch'


def test_ai_semantics_can_accept_category_without_silencing_other_differences(monkeypatch):
    docs=[document('decl','Customs Declaration'),document('warehouse','Warehouse Receipt')]
    rows=[record('a','decl','cargo_description',normalize('Baga xe đạp 97ST21155; Thanh nối baga xe đạp 97ST99963')),
          record('b','warehouse','cargo_description',normalize('Phụ tùng xe đạp')),
          record('g1','decl','gross_weight',normalize('515.08 KG','weight')),
          record('g2','warehouse','gross_weight',normalize('489.00 KG','weight'))]
    original=copy.deepcopy(rows);saved={}
    def execute(sql,args):
        if 'packet_reviews' in sql:saved.update(case_id=args[0],signature=args[1],payload=args[2],error=args[3])
    monkeypatch.setattr(db,'execute',execute)
    monkeypatch.setattr(db,'one',lambda *args:saved or None)
    monkeypatch.setattr(ai,'key',lambda:'mock')
    response={'issues':[], 'description_assessments':[{'record_ids':['a','b'],'relation':'compatible',
        'reason':'Baga và thanh nối baga là phụ tùng xe đạp; nguồn kho ghi nhóm hàng, không xác nhận từng mã.'}]}
    def parse(**kwargs):return SimpleNamespace(output_parsed=kwargs['text_format'].model_validate(response),usage=None)
    monkeypatch.setattr(ai,'OpenAI',lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    assert not consistency.run_ai_review('test',docs,rows)
    checks=validation.build_checks({'id':'test','mode':'FCL','requirements':default_requirements()},docs,rows)
    assert next(c for c in checks if c['key']=='field:cargo_description')['result']=='Not Yet Checked'
    assert next(c for c in checks if c['key']=='field:gross_weight')['result']=='Mismatch'
    assert rows==original
    # No stale approval when a source changes.
    rows[1]['value']=normalize('Phụ tùng ô tô')
    assert consistency.description_assessment('test',docs,rows,rows[:2]) is None
    # Explicit contradictions stay in the difference queue.
    response['description_assessments'][0].update(relation='contradiction',reason='Nguồn ghi phụ tùng ô tô, khác nhóm xe đạp trên tờ khai.')
    assert not consistency.run_ai_review('test',docs,rows)
    checks=validation.build_checks({'id':'test','mode':'FCL','requirements':default_requirements()},docs,rows)
    issue=next(c for c in checks if c['key']=='field:cargo_description')
    assert issue['result']=='Needs Verification' and issue['detail']['category']=='difference'
    # Incomplete/invented IDs cannot suppress a warning.
    response['description_assessments'][0]['record_ids']=['a','invented']
    assert not consistency.run_ai_review('test',docs,rows)
    assert json.loads(saved['payload'])==[]
