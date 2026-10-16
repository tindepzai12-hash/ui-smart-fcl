from backend import consistency, validation
from backend.normalize import normalize
from backend.dictionary import default_requirements
from test_shipment_consistency import document, record


def test_review_suggestions_and_number_formats_are_not_counted_as_proven_mismatches(monkeypatch):
    monkeypatch.setattr(consistency.db,'one',lambda *args:None)
    checks=[{'key':'field:'+key,'result':result,'detail':{'sources':[], 'category':'difference'}}
            for key,result in [('volume','Mismatch'),('gross_weight','Needs Verification'),('port_loading','Needs Verification')]]
    report=consistency.report({'id':'case'},[],[],checks)
    assert report['mismatch_count']==1
    assert report['open_count']==3
    assert len(report['issues'])==3  # No silent staff approval or warning deletion.


def test_explicit_contract_any_port_option_is_not_a_conflict():
    docs=[document('c','Contract'),document('b','B/L'),document('i','Invoice'),document('p','Packing List')]
    texts=['Any of Port CHINA','QINZHOU, CHINA','QINZHOU.CHINA','QINZHOU,CHINA']
    rows=[record(str(n),d['id'],'port_loading',normalize(t)) for n,(d,t) in enumerate(zip(docs,texts))]
    assert validation.contract_port_option_compatible(rows,docs)
    assert 'port_loading' not in consistency.contextual_candidates(docs,rows)
    checks=validation.build_checks({'mode':'FCL','requirements':default_requirements()},docs,rows)
    assert next(c for c in checks if c['key']=='field:port_loading')['result']=='Not Yet Checked'
    rows[-1]['value']=normalize('SHANGHAI, CHINA')
    assert not validation.contract_port_option_compatible(rows,docs)
    rows[-1]['value']=normalize('QINZHOU, VIETNAM')
    assert not validation.contract_port_option_compatible(rows,docs)
    rows[-1]['value']=normalize('QINZHOU,CHINA')
    docs[0]['type']='B/L'
    assert not validation.contract_port_option_compatible(rows,docs)
