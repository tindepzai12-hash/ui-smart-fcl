"""Source-column regressions found in the user's packet; no private files committed."""
import copy
import pytest
from backend import ai, validation
from backend.dictionary import FIELDS,default_requirements,COMPARISON_TYPES,REVIEW_GROUPS
from backend.normalize import normalize
from test_shipment_consistency import document,record


def grid_page(packages='140',volume='410.72'):
    table=[['Item','Description of goods','No.of\nbdl','pcs/bdl','Total\npcs','Quantity\n(M3)','Net Weight\n(KGS)','GW Weight\n(KGS)'],
           ['Total:','',''+packages,'','8720',volume,'','']]
    return {'number':1,'text':'PACKING LIST\n'+ '\n'.join(' | '.join(row) for row in table),'tables':[table]}


def test_printed_totals_bind_to_packages_pieces_and_volume_not_first_row():
    page=grid_page()
    recovered=ai.packing_summary_fields([page])
    assert {k:(v[0].raw_value,v[0].unit.upper()) for k,v in recovered.items()}=={
        'packages':('140','BDL'),'goods_quantity':('8720','PCS'),'volume':('410.72','M3')}
    assert not recovered.get('gross_weight')  # stamp-obscured total stays absent
    data=ai.DocumentResult(document_type='Packing List',classification_evidence='PACKING LIST',
        fields=[ai.FieldResult(field_id='packages',raw_value='672',unit='BDL',unit_evidence='bdl',source_page=1,evidence_text='672')],items=[],containers=[])
    grounded=ai.ground_source_format(data,[page])
    rows=ai.validate_result(grounded,[page])
    assert next(r for r in rows if r['key']=='packages')['value']['number']=='140'
    assert not [r for r in rows if r['key']=='gross_weight']


def test_no_total_label_means_no_guessed_summary():
    page=grid_page();page['tables'][0][1][0]='1'
    assert not ai.packing_summary_fields([page])


def test_blank_weight_total_cannot_be_replaced_by_first_row_weight():
    page=grid_page();page['text']+='\n19000 KG'
    result=ai.DocumentResult(document_type='Packing List',classification_evidence='PACKING LIST',
        fields=[ai.FieldResult(field_id='gross_weight',raw_value='19000',unit='KG',unit_evidence='KG',source_page=1,evidence_text='19000 KG')],items=[],containers=[])
    with pytest.raises(ValueError,match='Ô tổng trọng lượng'):
        ai.validate_result(result,[page])


def test_cubic_metres_cannot_be_pieces_when_source_has_both_columns():
    page=grid_page();page['text']+='\n27.28 M3'
    result=ai.DocumentResult(document_type='Packing List',classification_evidence='PACKING LIST',
        fields=[ai.FieldResult(field_id='goods_quantity',raw_value='27.28',unit='M3',unit_evidence='M3',source_page=1,evidence_text='27.28 M3')],items=[],containers=[])
    with pytest.raises(ValueError):ai.validate_result(result,[page])


def test_faint_grid_with_merged_total_label_preserves_numeric_column_roles(monkeypatch):
    from backend import reader
    from PIL import Image,ImageDraw
    monkeypatch.setattr(reader,'ocr_status',lambda:{'ready':True,'cmd':'tesseract','languages':['eng']})
    cells=iter(['Item','Description of goods','Bundles','Total pcs','Quantity (M3)',
                'Total:','140','8720','410.72'])
    monkeypatch.setattr(reader.pytesseract,'image_to_string',lambda *a,**kw:next(cells))
    with Image.new('L',(1000,1000),255) as image:
        draw=ImageDraw.Draw(image)
        for y in [350,450,550]:draw.line((50,y,950,y),fill=230,width=2)
        for x in [50,200,500,650,800,950]:draw.line((x,350,x,450),fill=230,width=2)
        for x in [50,500,650,800,950]:draw.line((x,450,x,550),fill=230,width=2)
        diagnostics=[];table=reader.ocr_grid_totals(image,diagnostics)
        assert table==[[['Item','Description of goods','Bundles','Total pcs','Quantity (M3)'],['Total:','','140','8720','410.72']]]
        assert any('threshold=245' in s for s in diagnostics)


@pytest.mark.parametrize('unit',['BE','BDL','BUNDLE','BUNDLES'])
def test_documented_bundle_units(unit):
    assert normalize('120 '+unit,'quantity')['unit']=='BDL'


def test_actual_volume_difference_cannot_be_hidden_by_decimal_ambiguity():
    docs=[document('pl','Packing List'),document('inv','Invoice'),document('sc','Contract')]
    rows=[record('p','pl','volume',normalize('390.61 M3','quantity')),
          record('i','inv','volume',normalize('390.340 M3','quantity')),
          record('s','sc','volume',normalize('390.340 M3','quantity'))]
    original=copy.deepcopy(rows)
    check=next(c for c in validation.build_checks({'mode':'FCL','requirements':default_requirements()},docs,rows) if c['key']=='field:volume')
    assert check['result']=='Mismatch'
    assert rows==original and rows[1]['value']['number'] is None
    rows[0]['value']=normalize('390.34 M3','quantity')
    assert not validation.volume_conflict(rows,{d['id']:d for d in docs})
    # Planned/contract-only disagreement isn't proof about an actual shipment.
    docs[0]['type']='Booking'
    assert not validation.volume_conflict(rows,{d['id']:d for d in docs})


def test_customs_spaced_form_marker_is_not_part_of_invoice_identifier():
    docs={d['id']:d for d in [document('decl','Customs Declaration'),document('inv','Invoice')]}
    rows=[record('a','decl','invoice_number',normalize('A - CODE-700')),
          record('b','inv','invoice_number',normalize('CODE-700'))]
    rows[0]['evidence']='Số hóa đơn: A - CODE-700'
    assert len(set(validation.comparison_values('invoice_number',rows,rows,docs)))==1
    rows[0]['value']=normalize('A-CODE-700')
    assert len(set(validation.comparison_values('invoice_number',rows,rows,docs)))==2
    rows[0]['value']=normalize('A - CODE-700');rows[0]['evidence']='Unlabelled reference'
    assert len(set(validation.comparison_values('invoice_number',rows,rows,docs)))==2


def test_bl_and_customs_are_supported_and_bl_has_separate_checklist_group():
    assert {'B/L','Customs Declaration','Customs Release'}<=set(COMPARISON_TYPES)
    assert any(g['type']=='B/L' for g in REVIEW_GROUPS)
    assert not default_requirements()['B/L']['required']
    assert {'Invoice','Contract','Purchase Order'}<=set(FIELDS['volume']['documents'])


def test_labelled_container_count_cannot_become_packages():
    pages=[{'number':1,'text':'Tờ khai hàng hóa nhập khẩu\nSố lượng container 10\nSố lượng kiện 120 BE','tables':[]}]
    result=ai.DocumentResult(document_type='Customs Declaration',classification_evidence='Tờ khai hàng hóa nhập khẩu',
        fields=[ai.FieldResult(field_id='packages',raw_value='10',source_page=1,evidence_text='Số lượng container 10'),
                ai.FieldResult(field_id='packages',raw_value='120',unit='BE',unit_evidence='BE',source_page=1,evidence_text='Số lượng kiện 120 BE')],items=[],containers=[])
    grounded=ai.ground_source_format(result,pages)
    assert [(f.raw_value,f.unit) for f in grounded.fields]==[('120','BE')]


def test_transport_weight_and_measurement_are_bound_to_their_own_units():
    page={'number':1,'text':'BILL OF LADING\nGross weight / Measurement\n123 ,456.000\nKGS\n376.2200\nCBM\n(140 BUNDLE(S))',
          'tables':[[['SOURCE_LABEL','SOURCE_VALUE','SOURCE_UNIT'],['Gross weight','123 ,456.000','KGS'],['Measurement','376.2200','CBM']]]}
    result=ai.DocumentResult(document_type='B/L',classification_evidence='BILL OF LADING',fields=[
        ai.FieldResult(field_id='gross_weight',raw_value='376.2200',unit='KGS',unit_evidence='KGS',source_page=1,evidence_text='376.2200'),
        ai.FieldResult(field_id='packages',raw_value='10',unit='CTRS',unit_evidence='CTRS',source_page=1,evidence_text='10 CTRS')],items=[],containers=[])
    rows=ai.validate_result(ai.ground_source_format(result,[page]),[page])
    values={r['key']:r['value'] for r in rows}
    assert values['gross_weight']['number']=='123456.000'
    assert values['gross_weight']['text']=='123 ,456.000 KGS'
    assert values['volume']['number']=='376.2200' and values['volume']['unit']=='CBM'
    assert values['packages']['number']=='140' and values['packages']['unit']=='BDL'


def test_measurement_crop_requires_both_printed_labels_and_distinct_units(monkeypatch):
    from backend import reader
    from PIL import Image
    data={'text':['Gross','weight'],'left':[750,810],'top':[100,100],'height':[20,20],'conf':[90,90]}
    monkeypatch.setattr(reader.pytesseract,'image_to_string',lambda *a,**kw:'Gross weight /\nMeasurement\n123 ,456.000\nKGS\n376.2200\nCBM')
    with Image.new('L',(1000,1500),255) as image:
        text,tables=reader.ocr_measurement_cell(image,data,'eng')
        assert tables[0][1]==['Gross weight','123 ,456.000','KGS']
        assert '123 ,456.000' in text
        monkeypatch.setattr(reader.pytesseract,'image_to_string',lambda *a,**kw:'Gross weight /\n123456 KGS')
        assert reader.ocr_measurement_cell(image,data,'eng')==('',[])
