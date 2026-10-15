import pytest
from backend import ai

TEXT = ('Tờ khai hàng hóa xuất khẩu (thông quan)\n'
        'Mô tả hàng hóa BLUE STEEL BICYCLE CARRIER\n'
        '  MADE IN VIET NAM\nSố lượng (1) 600 PCE\nTrị giá 3918 USD\n'
        'Mô tả hàng hóa SILVER ALLOY BICYCLE BRACKET\n'
        '  MADE IN VIET NAM\nSố lượng (1) 600 PCE')
FIRST = 'BLUE STEEL BICYCLE CARRIER MADE IN VIET NAM'
SECOND = 'SILVER ALLOY BICYCLE BRACKET MADE IN VIET NAM'

def result(value, quote=TEXT, page=1, key='cargo_description'):
    return ai.DocumentResult(document_type='Customs Declaration', classification_evidence='Tờ khai hàng hóa xuất khẩu',
        fields=[ai.FieldResult(field_id=key,raw_value=value,source_page=page,evidence_text=quote)],items=[],containers=[])

def test_disjoint_labelled_descriptions_keep_both_source_parts():
    rows = ai.validate_result(result(FIRST+'; '+SECOND),[{'number':1,'text':TEXT}])
    assert len(rows)==1
    assert [p['text'] for p in rows[0]['value']['source_parts']]==[FIRST,SECOND]
    assert rows[0]['page']==1 and rows[0]['evidence']==TEXT
    assert 'kiểm chứng riêng' in rows[0]['value']['normalization_note']

@pytest.mark.parametrize('value',[
    FIRST+'; '+SECOND.replace('SILVER','GOLD'),
    SECOND+'; '+FIRST,
    FIRST+'; '+FIRST,
    FIRST+'; '+SECOND+'; MADE UP GOODS',
    FIRST+'; '+SECOND.replace('BRACKET','BRACKET999'),
])
def test_compound_description_cannot_invent_reorder_or_duplicate_source(value):
    with pytest.raises(ValueError,match='bằng chứng'):
        ai.validate_result(result(value),[{'number':1,'text':TEXT}])

def test_compound_evidence_must_be_real_same_page_labelled_cells():
    for quote,page in [(TEXT,2),(TEXT.replace('STEEL','BRASS'),1)]:
        with pytest.raises(ValueError,match='bằng chứng'):
            ai.validate_result(result(FIRST+'; '+SECOND,quote,page),[{'number':1,'text':TEXT}])
    unrelated=TEXT.replace('Mô tả hàng hóa','Notes')
    with pytest.raises(ValueError,match='bằng chứng'):
        ai.validate_result(result(FIRST+'; '+SECOND,unrelated),[{'number':1,'text':unrelated}])

def test_numeric_values_never_use_compound_description_exception():
    value=ai.FieldResult(field_id='gross_weight',raw_value='3918; 600',source_page=1,evidence_text=TEXT)
    assert not ai.labelled_cargo_parts(value,TEXT,[{'number':1,'text':TEXT}])
    with pytest.raises(ValueError,match='bằng chứng'):
        ai.validate_result(result('3918; 600',key='gross_weight'),[{'number':1,'text':TEXT}])

def test_partial_pointer_is_rebound_only_when_every_labelled_component_is_proven():
    candidate=result(FIRST+'; '+SECOND,quote='Mô tả hàng hóa BLUE STEEL BICYCLE CARRIER\n  MADE IN VIET NAM')
    page={'number':1,'text':TEXT}
    grounded=ai.ground_source_format(candidate,[page])
    assert len(ai.validate_result(grounded,[page])[0]['value']['source_parts'])==2
    assert candidate.fields[0].evidence_text!=TEXT
    candidate.fields[0].raw_value=FIRST+'; '+SECOND.replace('SILVER','GOLD')
    with pytest.raises(ValueError,match='bằng chứng'):
        ai.validate_result(ai.ground_source_format(candidate,[page]),[page])

def test_declaration_invoice_total_requires_own_total_label_and_keeps_separator_warning():
    for label in ['Tổng trị giá hóa đơn','Total Invoice Value']:
        quote=label+' FOB - USD - 4.242'
        candidate=result('4.242',quote=quote,key='invoice_total')
        candidate.fields[0].unit='USD';candidate.fields[0].unit_evidence=quote
        page={'number':1,'text':'Tờ khai hàng hóa xuất khẩu\n'+quote}
        rows=ai.validate_result(candidate,[page])
        assert rows[0]['value']['number'] is None and rows[0]['value']['warning']
    for label in ['Trị giá hóa đơn','Tổng trị giá tính thuế']:
        quote=label+' 4.242 USD';candidate=result('4.242',quote=quote,key='invoice_total')
        with pytest.raises(ValueError,match='nhãn tổng'):
            ai.validate_result(candidate,[{'number':1,'text':'Tờ khai hàng hóa xuất khẩu\n'+quote}])

def test_each_accepted_source_part_has_independent_original_highlight(monkeypatch):
    from backend import source_locator
    words=[{'text':t,'layer':'PDF text','x':i/100,'y':.2,'w':.01,'h':.01,'confidence':None}
           for i,t in enumerate(TEXT.split())]
    monkeypatch.setattr(source_locator,'layout',lambda *args:words)
    record=ai.validate_result(result(FIRST+'; '+SECOND),[{'number':1,'text':TEXT}])[0]
    located=source_locator.inspect({'path':'unused','name':'customs.pdf','ext':'.pdf','id':'doc'},
                                  record,{'number':1,'method':'PDF text','quality':'','text':TEXT})
    assert {b['attribute'] for b in located['boxes']}=={'description_part_1','description_part_2'}
    assert not any('600'==b['text'] or '3918'==b['text'] for b in located['boxes'])

def test_multiline_price_currency_is_bound_to_printed_table_header_only():
    header='UNIT PRICE\nFOB EXAMPLE\nUSD'
    page={'number':1,'text':'INVOICE\n'+header+'\nPART-A BLUE STEEL CARRIER 600 PCS 6.53 3918.00',
          'tables':[[['Item No.','Description','Quantity','Unit',header,'Amount'],
                     ['PART-A','BLUE STEEL CARRIER','600','PCS','6.53','3918.00']]]}
    candidate=ai.DocumentResult(document_type='Invoice',classification_evidence='INVOICE',containers=[],
        fields=[ai.FieldResult(field_id='currency',raw_value='USD',source_page=1,evidence_text='wrong pointer')],
        items=[ai.ItemResult(line_number='1',product_code='PART-A',description='BLUE STEEL CARRIER',quantity='600',
                            unit='PCS',unit_price='6.53',line_amount='3918.00',currency='USD',source_page=1,evidence_text='INVOICE')])
    rows,rejected=ai.validated_subset(ai.ground_source_format(candidate,[page]),[page])
    assert not rejected and len(rows)==2 and all('USD' in r['evidence'] for r in rows)
    for bad in [{**page,'text':page['text'].replace(header,'USD\nSeller address')},
                {**page,'text':page['text']+'\nAlternative EUR'}]:
        grounded=ai.ground_source_format(candidate,[bad])
        with pytest.raises(ValueError,match='bằng chứng'):
            ai.validate_result(grounded,[bad])

def test_quantity_unit_pointer_can_use_unit_next_to_same_printed_total():
    page={'number':1,'text':'PACKING LIST\nSAY TOTAL: (1,200) PCS IN 56 CARTONS\nCARTON'}
    candidate=ai.DocumentResult(document_type='Packing List',classification_evidence='PACKING LIST',items=[],containers=[],
        fields=[ai.FieldResult(field_id='goods_quantity',raw_value='1,200',unit='PCS',source_page=1,
                              evidence_text='SAY TOTAL: (1,200) PCS IN 56 CARTONS',unit_evidence='CARTON')])
    grounded=ai.ground_source_format(candidate,[page]);rows=ai.validate_result(grounded,[page])
    assert rows[0]['value']['number']=='1200' and rows[0]['value']['unit']=='PCS'
    candidate.fields[0].unit='CTN'
    with pytest.raises(ValueError,match='Đơn vị'):
        ai.validate_result(ai.ground_source_format(candidate,[page]),[page])

def test_warehouse_unprinted_unit_is_omitted_without_losing_literal_number():
    page={'number':1,'text':'YÊU CẦU NHẬP KHO\nWeight Volume\n515.080 7.380'}
    candidate=ai.DocumentResult(document_type='Warehouse Receipt',classification_evidence='YÊU CẦU NHẬP KHO',items=[],containers=[],
        fields=[ai.FieldResult(field_id=k,raw_value=v,unit=u,source_page=1,evidence_text='515.080 7.380',unit_evidence='Weight Volume')
                for k,v,u in [('cargo_weight','515.080','KGS'),('volume','7.380','CBM')]])
    rows=ai.validate_result(ai.ground_source_format(candidate,[page]),[page])
    assert len(rows)==2 and all(r['value']['unit'] is None and r['value']['warning'] for r in rows)
    assert candidate.fields[0].unit=='KGS'  # Original model candidate is not mutated.
