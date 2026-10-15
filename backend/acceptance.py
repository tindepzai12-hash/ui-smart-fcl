"""Accept readable extracted data without pretending it was checked by a person."""
import re
from .normalize import decimal_text

def printed_number(value):
    # The characters are readable even when a numeric separator convention
    # cannot be proved. Export the literal string, never guess a numeric value.
    return bool(re.fullmatch(r'\d{1,3}(?:[,.]\d{3})+(?:\s+[A-Za-z]{2,8})?',str(value).strip()))

def readable(record):
    value=record['value']
    if record['kind']=='field':
        from .dictionary import FIELDS
        if record['key'] in ['cargo_weight','declared_weight','volume'] and not value.get('unit'):
            # A generic optional measurement can be stored exactly as printed.
            # It is never assigned a unit or compared with a unit-bearing total.
            return decimal_text(value.get('text','')) is not None or printed_number(value.get('text',''))
        if FIELDS.get(record['key'],{}).get('type') in ['weight','quantity'] and not value.get('unit'):return False
        if not str(value.get('text','')).strip() and value.get('number') is None:return False
        return (not value.get('warning')
                or (str(value['warning']).startswith('Dấu phân cách số') and printed_number(value.get('text','')))
                or (str(value['warning']).startswith('Ngày dạng dd/mm') and bool(re.fullmatch(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',value.get('text','')))))
    if record['kind']=='item':
        if not value.get('description') or not value.get('quantity') or not value.get('unit'):return False
        keys=['quantity']+(['unit_price','line_amount'] if value.get('scope','invoice')=='invoice' else [])
        if value.get('scope','invoice')=='invoice' and not value.get('currency'):return False
        return all(value.get(k) and (decimal_text(value[k]) is not None or printed_number(value[k])) for k in keys) and (
            not value.get('warning') or str(value['warning']).startswith(('Số lượng có dấu phân cách','Có số chưa rõ định dạng')))
    return False

def apply(c,case_id):
    from . import db,validation
    changed=[]
    for row in c.execute("SELECT r.* FROM records r JOIN documents d ON d.id=r.document_id WHERE r.case_id=? AND r.status='pending' AND r.method='OpenAI' AND d.status='read' AND d.extraction_required=0 AND d.collection='document'",(case_id,)).fetchall():
        record=validation.unpack(row)
        if record['evidence'].strip() and readable(record):
            c.execute("UPDATE records SET status='auto_accepted',note=?,version=version+1 WHERE id=?",('AI đã nhận từ bằng chứng nguồn; không yêu cầu kiểm lại từng ô.',record['id']))
            changed.append(record['id'])
    if changed:db.audit(c,case_id,'Tự nhận dữ liệu AI có nguồn',after=changed,actor='Hệ thống')
