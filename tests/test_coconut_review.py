import pytest
from backend import ai,extraction,pdf_bundle,consistency
from backend.normalize import normalize,decimal_text
from backend.validation import comparison_values

@pytest.mark.parametrize('raw,expected',[('FEB 11th 2020','2020-02-11'),('Jan, 31st 2020','2020-01-31'),('18th February 2020','2020-02-18')])
def test_named_ordinal_dates(raw,expected):
    value=normalize(raw,'date')
    assert value['text']==expected and not value['warning']
    assert normalize('02/03/2020','date')['warning']
    assert normalize('FEB 31st 2020','date')['warning']
    assert decimal_text('19,560') is None  # No global separator guess.

def test_contract_attachment_list_is_not_a_second_document():
    pages=[{'number':1,'text':'CONTRACT\nNo: TPV 03/EX'},
           {'number':2,'text':'ARTICLE 2 : Term of payment\nBy L/C\nARTICLE 4: Full set of documents required:\n- Bill of Lading\n- Commercial Invoice\n- Packing List\n- Certificate of Origin'}]
    assert pdf_bundle.suggest(pages)==[{'start':1,'end':2,'type':'Contract'}]
    assert not pdf_bundle.is_mixed(pages)
    assert pdf_bundle.is_mixed([pages[0],{'number':2,'text':'COMMERCIAL INVOICE\nInvoice No: INV-1'}])

def test_contract_reference_can_contain_source_printed_spaces():
    page={'number':1,'text':'CONTRACT\nNo: TPV 03/EX'}
    model=ai.DocumentResult.model_validate({'document_type':'Contract','classification_evidence':'CONTRACT','fields':[{'field_id':'contract_number','raw_value':'TPV 03/EX','source_page':1,'evidence_text':'No: TPV 03/EX'}],'items':[],'containers':[]})
    rows,rejected=ai.validated_subset(ai.ground_source_format(model,[page]),[page])
    assert not rejected and rows[0]['value']['text']=='TPV 03/EX'

def rows(key,values):
    return [{'id':str(i),'document_id':str(i),'page':1,'kind':'field','key':key,'status':'pending','value':normalize(v)} for i,v in enumerate(values)]

def test_port_formatting_does_not_merge_different_countries_or_ports():
    group=rows('port_loading',['CAT LAI, VIETNAM','CAT LAI PORT,VIET NAM','CAT LAI'])
    assert len(set(comparison_values('port_loading',group,group)))==1
    for other in ['CAT LAI, THAILAND','HO CHI MINH CITY, VIETNAM','ANY PORT OF HOCHIMINH CITY, VIETNAM']:
        different=group+[rows('port_loading',[other])[0]]
        assert len(set(comparison_values('port_loading',different,different)))>1

def test_vessel_suffix_needs_an_explicit_independent_voyage():
    group=rows('vessel',['AMALIA C','AMALIA C 074B'])
    assert len(set(comparison_values('vessel',group,group)))==2
    voyage={**group[0],'id':'voyage','key':'voyage','value':normalize('074B')}
    assert len(set(comparison_values('vessel',group,group+[voyage])))==1
    assert group[1]['value']['text']=='AMALIA C 074B'
    changed=rows('vessel',['AMALIA C','AMALIA C 075B'])
    assert len(set(comparison_values('vessel',changed,changed+[voyage])))==2
    check={'detail':{'sources':[{'id':r['id']} for r in group]}}
    assert not consistency.semantic_difference(check,group+[voyage])

def result(kind,fields=None,items=None):
    return ai.DocumentResult.model_validate({'document_type':kind,'classification_evidence':{'C/O':'CERTIFICATE OF ORIGIN','Booking':'BOOKING NOTE','Invoice':'COMMERCIAL INVOICE'}[kind], 'fields':fields or [],'items':items or [],'containers':[]})

def test_empty_slots_and_equipment_are_not_actionable_fields():
    page={'number':1,'text':'BOOKING NOTE\nCảng D/C : TAICHUNG\nSố lượng container : 1X20DC'}
    fields=[{'field_id':k,'raw_value':v,'source_page':1,'evidence_text':e} for k,v,e in [('eta','',''),('packages','1X20DC','Số lượng container : 1X20DC'),('port_discharge','TAICHUNG','Cảng D/C : TAICHUNG')]]
    grounded=ai.ground_source_format(result('Booking',fields),[page]);records,rejected=ai.validated_subset(grounded,[page])
    assert not rejected and [r['key'] for r in records]==['port_discharge']

def test_origin_declaration_number_and_certification_date_not_invoice_date():
    text='CERTIFICATE OF ORIGIN\n2. Consignee\nPURESUN\nNUMBER : 200218-03/02\n3. Means of transport\nNUMBER OF INVOICE\nNO: TPV03-02/EX\nDATE: FEB 11th 2020\nTRUONG PHU VINH here by certifies that above mention goods are of\nVietNamese origin.\n\nBENTRE VIETNAM FEB 18th 2020'
    fields=[{'field_id':'co_number','raw_value':'200218-03/02','source_page':1,'evidence_text':'NUMBER : 200218-03/02'}, {'field_id':'co_date','raw_value':'FEB 11th 2020','source_page':1,'evidence_text':'DATE: FEB 11th 2020'}]
    page={'number':1,'text':text}
    grounded=ai.ground_source_format(result('C/O',fields),[page]);records,rejected=ai.validated_subset(grounded,[page])
    assert not rejected
    assert next(r for r in records if r['key']=='co_date')['value']['text']=='2020-02-18'
    bad=result('C/O',[{**fields[0],'raw_value':'TPV03-02/EX','evidence_text':'NO: TPV03-02/EX'}])
    with pytest.raises(ValueError):ai.validate_result(bad,[page])

def test_joined_quantity_and_prefixed_currency_rebind_only_literal_item_cells():
    page={'number':1,'text':'COMMERCIAL INVOICE\nQUANTITY UNIT PRICE AMOUNT\nCOCONUT SAP 16,200KG USD 0.60/KG USD 9,720'}
    item={'line_number':'1','description':'COCONUT SAP','quantity':'16,200','unit':'KG','unit_price':'0.60','line_amount':'9,720','currency':'USD','source_page':1,'evidence_text':page['text'].splitlines()[2], 'cell_evidence':[{'attribute':'unit','evidence_text':'UNIT'},{'attribute':'currency','evidence_text':'AMOUNT'}]}
    grounded=ai.ground_source_format(result('Invoice',items=[item]),[page]);records,rejected=ai.validated_subset(grounded,[page])
    assert not rejected and any(r['kind']=='item' for r in records)
    # A price-unit suffix is not a quantity unit when the quantity has none.
    no_unit={**page,'text':page['text'].replace('16,200KG','16,200')}
    item['evidence_text']=no_unit['text'].splitlines()[2]
    grounded=ai.ground_source_format(result('Invoice',items=[item]),[no_unit])
    with pytest.raises(ValueError):ai.validate_result(grounded,[no_unit])

def test_packing_commodity_comes_from_unique_quantity_bound_cell():
    page={'number':1,'text':'PACKING LIST\nCOCONUT SAP AND EXTRACT\n(CLASS A)\nORIGIN OF VIETNAM\n120 DRUMS',
          'tables':[[['DESCRIPTION OF GOODS','NUMBER OF CASKS'],['COCONUT SAP AND EXTRACT\n(CLASS A)\nORIGIN OF VIETNAM','120 DRUMS']]]}
    item={'line_number':'1','description':'(CLASS A) ORIGIN OF VIETNAM','quantity':'120','unit':'DRUMS','source_page':1,'evidence_text':page['text']}
    model=ai.DocumentResult.model_validate({'document_type':'Packing List','classification_evidence':'PACKING LIST','fields':[],'items':[item],'containers':[]})
    grounded=ai.ground_source_format(model,[page]);records,rejected=ai.validated_subset(grounded,[page])
    assert not rejected and records[0]['value']['description']=='COCONUT SAP AND EXTRACT\n(CLASS A)'
    ambiguous={**page,'tables':[[*page['tables'][0],['ANOTHER COMMODITY','120 DRUMS']]],'text':page['text']+'\nANOTHER COMMODITY'}
    grounded=ai.ground_source_format(model,[ambiguous])
    assert grounded.items[0].description==item['description']  # Do not choose a row by count alone.
