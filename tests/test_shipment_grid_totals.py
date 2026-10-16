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
