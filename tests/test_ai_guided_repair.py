from types import SimpleNamespace
import pytest
from backend import ai
from backend.db import uid


PAGES = [{'number': 1, 'text': 'COMMERCIAL INVOICE\nInvoice No: R-801\nAMOUNT (EUR)\nTOTAL: 84,000.00'}]


def result(fields):
    return ai.DocumentResult.model_validate({'document_type': 'Invoice', 'classification_evidence': 'COMMERCIAL INVOICE',
                                           'fields': fields, 'items': [], 'containers': []})


def field(key, value, line):
    return dict(field_id=key, raw_value=value, source_page=1, evidence_text='', evidence_start_line=line)


def test_repair_accepts_literal_evidence_without_replacing_valid_field():
    first = result([field('invoice_number', 'R-801', 2), field('invoice_total', '999.00', 4)])
    second = result([field('invoice_number', 'COMMERCIAL', 1), field('invoice_total', '84,000.00', 4), field('currency', 'EUR', 3)])
    targets = {'fields': ['invoice_number', 'invoice_total', 'currency'], 'items': False, 'containers': False}
    merged = ai.merge_supported_repair(first, second, PAGES, targets)
    records, rejected = ai.validated_subset(merged, PAGES)
    assert not rejected
    assert {r['key']: r['raw'] for r in records} == {'invoice_number': 'R-801', 'invoice_total': '84,000.00', 'currency': 'EUR'}
    second.fields[1].raw_value = '777.00'
    _, rejected = ai.validated_subset(ai.merge_supported_repair(first, second, PAGES, targets), PAGES)
    assert rejected  # Invented repair does not replace the rejected first reading.


def test_repair_cannot_change_classification_or_add_unrequested_field():
    first = result([field('invoice_number', 'R-801', 2)])
    second = result([field('invoice_number', 'COMMERCIAL', 1)])
    merged = ai.merge_supported_repair(first, second, PAGES, {'fields': ['currency'], 'items': False, 'containers': False})
    assert len(merged.fields) == 1
    second.document_type = 'B/L'
    with pytest.raises(ValueError, match='đổi loại'):
        ai.merge_supported_repair(first, second, PAGES, {'fields': [], 'items': False, 'containers': False})


def test_repair_row_can_fill_missing_cell_but_not_change_existing_quantity():
    pages = [{'number': 1, 'text': 'INVOICE\nBolts 10 100.00\nEUR\nBolts 11 110.00'}]
    first = ai.DocumentResult(document_type='Invoice', classification_evidence='INVOICE', fields=[], containers=[],
        items=[ai.ItemResult(line_number='1', description='Bolts', quantity='10', source_page=1, evidence_text='Bolts 10 100.00')])
    second = ai.DocumentResult.model_validate(first.model_dump())
    second.items[0].currency = 'EUR'
    second.items[0].cell_evidence = [ai.CellEvidence(attribute='currency', evidence_text='EUR')]
    targets = {'fields': [], 'items': True, 'containers': False}
    merged = ai.merge_supported_repair(first, second, pages, targets)
    assert len(merged.items) == 1 and merged.items[0].currency == 'EUR'
    second.items[0].quantity = '11'; second.items[0].evidence_text = 'Bolts 11 110.00'
    merged = ai.merge_supported_repair(first, second, pages, targets)
    assert merged.items[0].quantity == '10' and merged.items[0].currency is None


def test_one_bounded_repair_and_cache_uses_only_supported_result(monkeypatch):
    calls = []
    first = result([field('invoice_number', 'R-801', 2), field('invoice_total', '999.00', 4)])
    second = result([field('invoice_total', '84,000.00', 4), field('currency', 'EUR', 3)])
    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_parsed=first if len(calls) == 1 else second,
                               usage=SimpleNamespace(input_tokens=30, output_tokens=20))
    monkeypatch.setattr(ai, 'OpenAI', lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    ai.configure('synthetic-secret', 'gpt-4.1-mini')
    try:
        pages = [{'number': 1, 'text': PAGES[0]['text']+'\n'+uid()}]
        _, records, meta = ai.analyze(None, {'type': 'Invoice'}, pages)
        assert len(calls) == 2 and not meta['rejected']
        assert all(c['temperature'] == 0 and c['store'] is False for c in calls)
        assert 'One bounded correction pass' in calls[1]['input'][0]['content']
        _, cached, meta = ai.analyze(None, {'type': 'Invoice'}, pages)
        assert len(calls) == 2 and meta['source'] == 'cache' and cached == records
    finally:
        ai.remove()


def test_failed_repair_keeps_supported_initial_data_and_does_not_cache(monkeypatch):
    calls = []
    first = result([field('invoice_number', 'R-801', 2)])
    def parse(**kwargs):
        calls.append(kwargs)
        if len(calls) % 2 == 0:
            raise RuntimeError('synthetic transport failure')
        return SimpleNamespace(output_parsed=first, usage=SimpleNamespace(input_tokens=30, output_tokens=20))
    monkeypatch.setattr(ai, 'OpenAI', lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    ai.configure('synthetic-secret', 'gpt-4.1-mini')
    try:
        pages = [{'number': 1, 'text': PAGES[0]['text']+'\n'+uid()}]
        _, records, meta = ai.analyze(None, {'type': 'Invoice'}, pages)
        assert len(calls) == 2 and [r['raw'] for r in records] == ['R-801']
        assert meta['rejected'] and 'synthetic transport failure' not in str(meta)
        ai.analyze(None, {'type': 'Invoice'}, pages)
        assert len(calls) == 4
    finally:
        ai.remove()


def test_repair_diagnostics_resolve_bad_currency_pointer_without_supplying_an_answer():
    pages=[{'number':1,'text':'COMMERCIAL INVOICE\nAmount (EUR)\nTOTAL US$120.00'}]
    candidate=field('currency','EUR',3)
    first=result([candidate])
    diagnostics=ai.repair_diagnostics(first,pages,['fields[1] currency: unsupported quote'])
    assert diagnostics[0]['failed_candidate']['raw_value']=='EUR'
    assert diagnostics[0]['resolved_source_quote']=='TOTAL US$120.00'
    assert 'Amount (EUR)' not in str(diagnostics)  # No expected correction injected.


def test_payment_sentence_cannot_enter_incoterms_despite_literal_evidence():
    pages=[{'number':1,'text':'COMMERCIAL INVOICE\nTT 100% after copy documents\nCIF Example Port'}]
    first=result([field('incoterms','TT 100% after copy documents',2)])
    with pytest.raises(ValueError,match='Incoterms'):
        ai.validate_result(first,pages)
    first.fields[0]=ai.FieldResult(**field('incoterms','CIF Example Port',3))
    assert ai.validate_result(first,pages)[0]['raw']=='CIF Example Port'
