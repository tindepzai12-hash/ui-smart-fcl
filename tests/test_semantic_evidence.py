import pytest
from PIL import Image
from backend import ai, extraction, reader
from backend.dictionary import supports
from backend.normalize import normalize, decimal_text
from backend.validation import build_checks


def document(kind, text, **parts):
    return ai.DocumentResult.model_validate(dict(document_type=kind, classification_evidence=text,
        fields=[],items=[],containers=[],**parts))


def test_titles_outweigh_references_and_misleading_filename():
    assert extraction.classify([{'text':'SALES CONTRACT\nARTICLE 4: DOCUMENTS REQUIRED\n1. CLEAN SHIPPED ON BOARD OCEAN BILL OF LADING\n2. ORIGINAL SIGNED COMMERCIAL INVOICE'}])[0]=='Contract'
    assert extraction.classify([{'text':'ACME DELIVERY ORDER\nArrival Date: MAR 05 2025\nB/L No: X-01'}])[0]=='Delivery Order'
    assert extraction.classify([{'text':'B/L No: X-01\nEst. Arrival Date: MAR 05 2025\nFree Time Until: 2025/03/10'}])[0]=='Arrival Notice'
    assert extraction.classify([{'text':'COMMERCIAL INVOICE & PACKING LIST\nQuantity: 100'}])[0]=='Invoice & Packing List'


def test_classification_cannot_use_valid_but_unrelated_quote():
    pages=[{'number':1,'text':'ACME DELIVERY ORDER\nB/L No: X-01'}]
    data=document('B/L','B/L No: X-01')
    with pytest.raises(ValueError,match='mâu thuẫn'):ai.validate_result(data,pages)


def test_literal_container_row_is_not_a_bill_number():
    pages=[{'number':1,'text':'BILL OF LADING\nABCU1234567 20DC SEAL99'}]
    data=document('B/L','BILL OF LADING')
    data.fields=[ai.FieldResult(field_id='bl_number',raw_value='ABCU1234567 20DC SEAL99',source_page=1,evidence_text='ABCU1234567 20DC SEAL99')]
    with pytest.raises(ValueError,match='định danh'):ai.validate_result(data,pages)
    data.fields[0].raw_value='ABCU1234567'
    with pytest.raises(ValueError,match='container'):ai.validate_result(data,pages)


def test_separate_table_header_evidence_is_valid_but_invented_unit_is_not():
    pages=[{'number':1,'text':'INVOICE\nQUANTITY (SET)\nAMOUNT (USD)\nBolts 20.000 23 46,000.00'}]
    data=document('Invoice','INVOICE')
    data.items=[ai.ItemResult(line_number='1',description='Bolts',quantity='20.000',unit='SET',currency='USD',source_page=1,
        evidence_text='Bolts 20.000 23 46,000.00',cell_evidence=[ai.CellEvidence(attribute='unit',evidence_text='QUANTITY (SET)'),ai.CellEvidence(attribute='currency',evidence_text='AMOUNT (USD)')])]
    records=ai.validate_result(data,pages)
    assert records[0]['raw']['quantity']=='20.000' and records[0]['value']['warning']
    assert '[unit] QUANTITY (SET)' in records[0]['evidence']
    data.items[0].unit='PCS'
    with pytest.raises(ValueError,match='unit'):ai.validate_result(data,pages)


def test_unit_cell_must_be_on_same_page():
    data=document('B/L','BILL OF LADING')
    data.fields=[ai.FieldResult(field_id='gross_weight',raw_value='5,580.000',unit='KGM',unit_evidence='KGM',source_page=1,evidence_text='5,580.000')]
    pages=[{'number':1,'text':'BILL OF LADING\n5,580.000\nKGM'}]
    records=ai.validate_result(data,pages)
    assert records[0]['raw']=='5,580.000' and records[0]['value']['unit']=='KG'
    pages[0]['text']='BILL OF LADING\n5,580.000';pages.append({'number':2,'text':'KGM'})
    with pytest.raises(ValueError,match='Đơn vị'):ai.validate_result(data,pages)


def test_issue_date_cannot_be_an_eta_even_with_literal_evidence():
    data=document('B/L','BILL OF LADING')
    data.fields=[ai.FieldResult(field_id='eta',raw_value='JAN 26 2025',source_page=1,evidence_text='Est. Issued Date: JAN 26 2025')]
    pages=[{'number':1,'text':'BILL OF LADING\nEst. Issued Date: JAN 26 2025'}]
    with pytest.raises(ValueError,match='Ngày đến'):ai.validate_result(data,pages)
    data.fields[0].raw_value='MAR 05 2025';data.fields[0].evidence_text='ETA: MAR 05 2025'
    pages[0]['text']+='\nETA: MAR 05 2025'
    assert ai.validate_result(data,pages)[0]['value']['text']=='2025-03-05'


def test_schema_prevents_guessed_field_ids():
    with pytest.raises(ValueError):
        ai.FieldResult(field_id='total_amount',raw_value='100.00',source_page=1,evidence_text='100.00')


def test_party_company_names_must_not_be_combined_across_columns():
    data=document('Delivery Order','DELIVERY ORDER')
    data.fields=[ai.FieldResult(field_id='notify_party',raw_value='ACME COMPANY LIMITED OTHER COMPANY LIMITED',source_page=1,evidence_text='ACME COMPANY LIMITED OTHER COMPANY LIMITED')]
    pages=[{'number':1,'text':'DELIVERY ORDER\nACME COMPANY LIMITED OTHER COMPANY LIMITED'}]
    with pytest.raises(ValueError,match='hai công ty'):ai.validate_result(data,pages)


def test_port_discharge_cannot_use_place_of_issue():
    data=document('B/L','BILL OF LADING')
    data.fields=[ai.FieldResult(field_id='port_discharge',raw_value='NAGOYA, JAPAN',source_page=1,evidence_text='Place of issue: NAGOYA, JAPAN')]
    with pytest.raises(ValueError,match='Cảng dỡ'):
        ai.validate_result(data,[{'number':1,'text':'BILL OF LADING\nPlace of issue: NAGOYA, JAPAN'}])


def test_combined_page_satisfies_both_checklist_entries_without_duplicate_source():
    case={'mode':'FCL','requirements':{'Invoice':{'required':True,'note':'Required'},'Packing List':{'required':True,'note':'Required'}}}
    docs=[{'id':'1','name':'combined.pdf','type':'Invoice & Packing List','status':'read','type_verified':False}]
    checks=build_checks(case,docs,[])
    assert all(c['result']=='Matched' for c in checks if c['key'].startswith('document:'))
    assert any(c['key']=='classification:1' and c['result']=='Needs Verification' for c in checks)
    assert supports(docs[0]['type'],'Invoice') and supports(docs[0]['type'],'Packing List')


def test_hybrid_preserves_original_identifiers_when_ocr_disagrees(monkeypatch):
    monkeypatch.setattr(reader,'ocr_status',lambda:{'ready':True})
    monkeypatch.setattr(reader,'ocr',lambda *a,**k:('DELIVERY ORDER\nOrder No: O123','OCR needs review',[]))
    text,method,quality,tables=reader.hybrid_text('Order No: 0123',Image.new('RGB',(10,10)),[])
    assert text.startswith('Order No: 0123') and 'Order No: O123' in text
    assert method=='PDF text + OCR' and quality
    assert decimal_text('20.000') is None
    assert normalize('MAR 05 2025','date')['text']=='2025-03-05'


def test_sparse_ocr_keeps_both_readings_without_correcting_source(monkeypatch):
    readings={3:'BILL OF LADING\nGross weight: 5.580.000',11:'BILL OF LADING\n5,580.000\nKGM\n28.00 CBM'}
    monkeypatch.setattr(reader,'ocr',lambda image,include_tables=False,psm=3:(readings[psm],'OCR needs review',[]))
    text,method,quality,tables=reader.read_pdf_image(Image.new('RGB',(100,100),'gray'))
    assert '5.580.000' in text and '5,580.000' in text and '28.00 CBM' in text
    assert method=='OCR' and 'OCR bổ sung' in quality


def test_amount_currency_unit_has_its_own_evidence_and_raw_is_preserved():
    data=document('Invoice','INVOICE')
    data.fields=[ai.FieldResult(field_id='invoice_total',raw_value='46,000.00',unit='USD',unit_evidence='AMOUNT (USD)',source_page=1,evidence_text='TOTAL: 46,000.00')]
    records=ai.validate_result(data,[{'number':1,'text':'INVOICE\nAMOUNT (USD)\nTOTAL: 46,000.00'}])
    assert records[0]['raw']=='46,000.00' and records[0]['value']['unit']=='USD'


def test_line_pointers_resolve_real_source_but_do_not_allow_invented_values():
    pages=[{'number':1,'text':'INVOICE\nInvoice No: A-001\nTOTAL: 100.00'}]
    data=document('Invoice','INVOICE')
    data.fields=[ai.FieldResult(field_id='invoice_total',raw_value='100.00',source_page=1,evidence_text='',evidence_start_line=3,evidence_end_line=3)]
    assert ai.validate_result(data,pages)[0]['evidence']=='TOTAL: 100.00'
    data.fields[0].raw_value='999.00'
    with pytest.raises(ValueError,match='bằng chứng'):ai.validate_result(data,pages)
    data.fields[0].evidence_start_line=4
    with pytest.raises(ValueError,match='dòng'):ai.validate_result(data,pages)


def test_currency_can_be_promoted_only_from_validated_agreeing_row_headers():
    pages=[{'number':1,'text':'INVOICE\nAmount (USD)\nBolts 10\nAmount (EUR)\nNuts 20'}]
    data=document('Invoice','INVOICE')
    data.items=[ai.ItemResult(line_number='1',description='Bolts',quantity='10',currency='USD',source_page=1,evidence_text='',evidence_start_line=3,
      cell_evidence=[ai.CellEvidence(attribute='currency',evidence_text='',start_line=2)])]
    records,rejected=ai.validated_subset(data,pages)
    assert not rejected and next(r for r in records if r['key']=='currency')['raw']=='USD'
    data.items.append(ai.ItemResult(line_number='2',description='Nuts',quantity='20',currency='EUR',source_page=1,evidence_text='',evidence_start_line=5,
      cell_evidence=[ai.CellEvidence(attribute='currency',evidence_text='',start_line=4)]))
    records,rejected=ai.validated_subset(data,pages)
    assert not rejected and not any(r['key']=='currency' for r in records)


def test_voyage_number_cannot_be_a_booking_reference():
    data=document('B/L','BILL OF LADING')
    data.fields=[ai.FieldResult(field_id='booking',raw_value='S043',source_page=1,evidence_text='Voyage: S043')]
    with pytest.raises(ValueError,match='Booking'):
        ai.validate_result(data,[{'number':1,'text':'BILL OF LADING\nVoyage: S043'}])
