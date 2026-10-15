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
