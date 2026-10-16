import copy
from backend.validation import field_comparable, build_checks
from backend.normalize import normalize
from backend.dictionary import default_requirements
from test_shipment_consistency import document, record


def test_translated_business_name_preserves_name_activity_and_legal_form():
    a=normalize('CÔNG TY TNHH MỘT THÀNH VIÊN THƯƠNG MẠI DỊCH VỤ MINH HẢI')
    b=normalize('MINH HAI TRADING & SERVICE CO., LTD')
    original=copy.deepcopy((a,b))
    assert field_comparable('importer',a)==field_comparable('importer',b)
    assert (a,b)==original
    for other in ['HAI MINH TRADING & SERVICE CO., LTD',
                  'MINH HAI TRADING & SERVICE JSC',
                  'MINH HAI MANUFACTURING CO., LTD',
                  'MINH HAI TRADING CO., LTD',
                  'MINH HAI TRADING & SERVICE CO., LTD BRANCH 2']:
        assert field_comparable('importer',a)!=field_comparable('importer',normalize(other))
    assert field_comparable('importer_tax_id',normalize('1234567890'))!=field_comparable('importer_tax_id',normalize('1234567891'))


def test_translated_party_does_not_hide_actual_volume_difference():
    docs=[document('decl','Customs Declaration'),document('co','C/O'),document('inv','Invoice'),document('pl','Packing List')]
    rows=[record('a','decl','importer',normalize('Công ty TNHH Thương mại Dịch vụ Minh Hải')),
          record('b','co','importer',normalize('MINH HAI TRADING & SERVICE CO LTD')),
          record('i','inv','volume',normalize('390.340 M3','quantity')),
          record('p','pl','volume',normalize('390.61 M3','quantity'))]
    original=copy.deepcopy(rows)
    checks=build_checks({'mode':'FCL','requirements':default_requirements()},docs,rows)
    assert next(c for c in checks if c['key']=='field:importer')['result']=='Matched'
    assert next(c for c in checks if c['key']=='field:volume')['result']=='Mismatch'
    assert rows==original
