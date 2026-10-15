"""Deterministic checks. Compare like roles/units/scopes; never infer customs legality."""
import json
import re
from decimal import Decimal
from .dictionary import FIELDS, supports, commercial_profile, REVIEW_GROUPS, REVIEW_FIELDS, DOCUMENT_LABELS
from .normalize import comparable, decimal_text, normalize
from .db import uid, encode

def unpack(record):
    r = dict(record)
    r['value'] = json.loads(r.pop('value_json'))
    r['raw'] = json.loads(r.pop('raw_json'))
    return r

def container_number(value):
    return re.sub(r'\s+', '', str(value or '')).upper()

def required(rule):
    # A legacy/incomplete waiver without a reason must not silently relax review.
    return rule.get('required', True) or len(str(rule.get('note', '')).strip()) < 3

def build_checks(case, documents, records):
    checks = []
    active = [r for r in records if r['status'] != 'rejected']
    docs = {d['id']: d for d in documents}

    def add(key, result, reason, sources=None, severity='warning'):
        checks.append({
            'key': key,
            'result': result,
            'severity': severity if result not in ['Matched', 'Not Applicable'] else 'info',
            'detail': {'reason': reason, 'sources': sources or []},
        })

    requirements = json.loads(case['requirements']) if isinstance(case['requirements'], str) else case['requirements']
    commercial = commercial_profile(requirements, case['mode'])
    if commercial:
        active = [r for r in active if r['kind'] != 'container' and (r['kind'] != 'field' or r['key'] in REVIEW_FIELDS)]
    for kind, rule in requirements.items():
        matching_docs = [d for d in documents if supports(d['type'],kind) or (kind == 'B/L' and d['type'] == 'Sea Waybill')]
        found = len(matching_docs) > 0
        doc_sources = [{'id': d['id'], 'document': d['name'], 'type': d['type'], 'value': {'text': d['type']}, 'page': 1} for d in matching_docs]
        note_text = rule.get('note', '')
        if found:
            reason = f'Đã có chứng từ {kind} trong hồ sơ ({note_text}).'
        elif required(rule):
            reason = f'Thiếu tệp chứng từ {kind} theo checklist ({note_text}). Tải bổ sung tệp hoặc chuyển sang Không bắt buộc kèm lý do nếu lô hàng miễn chứng từ này.'
        else:
            reason = f'Miễn tệp chứng từ {kind} theo cấu hình checklist ({note_text}).'
        add('document:' + kind, 'Matched' if found else 'Missing' if required(rule) else 'Not Applicable', reason, doc_sources, severity='error')

    for d in documents:
        doc_source = [{'id': d['id'], 'document': d['name'], 'type': d['type'], 'value': {'text': d['name']}, 'page': 1}]
        if d.get('extraction_required'):
            add('extraction:' + d['id'], 'Needs Verification', 'Đã đổi loại tài liệu. Đọc lại tệp này để trích xuất theo loại vừa chọn.', doc_source, severity='error')
        if d['status'] == 'needs_split':
            add('reading:' + d['id'], 'Needs Verification', 'Đã đọc nội dung. Tách bộ PDF thành từng chứng từ trước khi xác nhận loại và đối chiếu.', doc_source)
        elif d['status'] != 'read':
            add('reading:' + d['id'], 'Needs Verification', d.get('error') or f"Tài liệu {d['name']} chưa đọc xong. Hãy bấm Đọc & trích xuất hoặc thử lại.", doc_source, severity='error')
        elif d.get('error'):
            add('reading:' + d['id'], 'Needs Verification', d['error'], doc_source, severity='error')
        if not d['type_verified']:
            add('classification:' + d['id'], 'Needs Verification', 'Nhân viên cần xác nhận loại: ' + d['name'], doc_source)
        if case['mode'] == 'FCL' and d['type'] == 'AWB':
            add('transport:' + d['id'], 'Needs Verification', 'Hồ sơ FCL có AWB; kiểm tra chứng từ nhầm hoặc đổi nghiệp vụ.', doc_source)

    fields = {}
    for r in active:
        if r['kind'] == 'field':
            fields.setdefault(r['key'], []).append(r)

    inv_rule = requirements.get('Invoice', {'required': True, 'note': ''})
    pl_rule = requirements.get('Packing List', {'required': True, 'note': ''})
    transport_kind = 'AWB' if case['mode'] == 'AIR' else 'B/L'
    transport_rule = requirements.get(transport_kind, {'required': True, 'note': ''})

    # Core working data: distinguish document checklist exemption from working field requirement.
    core_specs = [] if commercial else [
        ('invoice_number', 'Invoice', inv_rule),
        ('invoice_date', 'Invoice', inv_rule),
        ('currency', 'Invoice', inv_rule),
        ('invoice_total', 'Invoice', inv_rule),
        ('awb_number' if case['mode'] == 'AIR' else 'bl_number', transport_kind, transport_rule),
    ]
    if commercial:
        for group in REVIEW_GROUPS:
            kind = group['type']
            matching = [d for d in documents if supports(d['type'], kind)]
            rule = requirements.get(kind, {'required': False, 'note': 'Ngoài phạm vi'})
            if kind == 'C/O' and not matching:
                continue
            keys = list(group['required_fields'])
            if kind == 'Contract':
                keys = (['contract_number'] if not matching or any(d['type']=='Contract' for d in matching) else []) + (['po_number'] if any(d['type']=='Purchase Order' for d in matching) else [])
            for key in keys:
                field_docs = [d for d in matching if kind != 'Contract' or d['type'] == ('Purchase Order' if key == 'po_number' else 'Contract')]
                missing_docs=[d for d in field_docs if not any(r['document_id']==d['id'] for r in fields.get(key,[]))]
                if not field_docs or missing_docs:
                    add('missing:' + key, 'Missing' if required(rule) or matching else 'Needs Verification',
                        f"Chưa có {FIELDS[key]['label']} có nguồn từ {group['label']}" + (': '+', '.join(d['name'] for d in missing_docs) if missing_docs else '') + '. Kiểm bản gốc và bổ sung; không tự đoán.', severity='error')
    for key, doc_kind, rule in core_specs:
        if not fields.get(key):
            if required(rule):
                add(
                    'missing:' + key,
                    'Missing',
                    f"Chưa có {FIELDS[key]['label']}. Bổ sung từ chứng từ, nhập thủ công có căn cứ, hoặc tắt yêu cầu {doc_kind} trong Checklist nếu lô hàng chưa có/miễn chứng từ gốc.",
                    severity='error',
                )
            else:
                add(
                    'missing:' + key,
                    'Needs Verification',
                    f"Chưa có {FIELDS[key]['label']} (chứng từ {doc_kind} đã đặt Không bắt buộc: {rule.get('note', '')}). Nhập thủ công nếu có nguồn khác hoặc bấm Ghi lý do xử lý để xác nhận miễn dữ liệu này.",
                    severity='warning',
                )

    if not any(r['kind'] == 'item' and (not r.get('document_id') or any(supports(docs.get(r['document_id'],{}).get('type'),t) for t in ['Invoice','Packing List'])) for r in active):
        if required(inv_rule) or required(pl_rule):
            add('missing:items', 'Missing', 'Chưa có dòng hàng độc lập. Thêm dòng hàng hoặc kiểm tra bảng gốc.', severity='error')
        else:
            add('missing:items', 'Needs Verification', 'Chưa có dòng hàng độc lập (Invoice & Packing List đều đang đặt Không bắt buộc). Thêm dòng hàng hoặc ghi nhận lý do.', severity='warning')

    if case['mode'] == 'FCL' and not commercial and not any(r['kind'] == 'container' for r in active):
        if required(transport_rule) or required(pl_rule):
            add('missing:containers', 'Missing', 'Chưa có container. Bổ sung theo chứng từ vận tải.', severity='error')
        else:
            add('missing:containers', 'Needs Verification', 'Chưa có container (B/L & Packing List đều đang đặt Không bắt buộc). Bổ sung thủ công hoặc ghi nhận lý do.', severity='warning')

    for key, group in fields.items():
        sources = [{
            'id': r['id'],
            'document': docs.get(r['document_id'], {}).get('name', 'Nhập tay'),
            'type': docs.get(r['document_id'], {}).get('type', 'Manual'),
            'value': r['value'],
            'page': r['page'],
        } for r in group]
        values = [comparable(r['value']) for r in group]
        if any(v is None for v in values):
            result = 'Needs Verification'
            reason = 'Có đơn vị/số/ngày chưa rõ. Giữ nguyên giá trị gốc.'
        elif len(group) == 1:
            result = 'Not Yet Checked'
            reason = 'Chỉ có một nguồn; cần nhân viên kiểm tra bản gốc.'
        elif len(set(values)) > 1:
            # Same field across multiple independent invoices cannot automatically be a conflict.
            doc_types = [s['type'] for s in sources]
            if commercial and 'Booking' in doc_types:
                result = 'Needs Verification'
                reason = 'Booking là kế hoạch đặt chỗ. Giá trị khác nguồn thương mại/đóng gói cần kiểm phạm vi và phiên bản; chưa kết luận chứng từ sai.'
            elif commercial and any(t in ['Contract','Purchase Order'] for t in doc_types) and key in ['goods_quantity','packages','gross_weight','net_weight']:
                result = 'Needs Verification'
                reason = 'Hợp đồng/PO có thể bao gồm nhiều đợt giao. Kiểm phạm vi lô trước khi so với Invoice/Packing List.'
            elif key.startswith('invoice_') and doc_types.count('Invoice') > 1:
                result = 'Needs Verification'
                reason = 'Nhiều hóa đơn; xác minh quan hệ chứng từ trước khi đối chiếu.'
            elif key in ['gross_weight', 'packages'] and (doc_types.count('Packing List') > 1 or doc_types.count('B/L') > 1):
                result = 'Needs Verification'
                reason = 'Có nhiều chứng từ tổng lô; cần xác định phạm vi/quan hệ vận đơn.'
            elif key in ['goods_quantity', 'packages'] and len({r['value'].get('unit') for r in group}) > 1:
                result = 'Needs Verification'
                reason = 'Khác đơn vị/bao bì; không thể kết luận sai lệch.'
            else:
                result = 'Mismatch'
                reason = 'Giá trị sau chuẩn hóa khác nhau ở cùng chỉ tiêu/role; kiểm tra phạm vi lô hàng.'
        else:
            result = 'Matched'
            reason = 'Các nguồn cùng trường/role khớp sau chuẩn hóa.'
        add('field:' + key, result, reason, sources)

    # Invoice arithmetic is per document, never across all invoices.
    for d in documents:
        if not supports(d['type'],'Invoice'):
            continue
        items = [r for r in active if r['kind'] == 'item' and r['document_id'] == d['id']]
        totals = [r for r in fields.get('invoice_total', []) if r['document_id'] == d['id']]
        for r in items:
            v = r['value']
            nums = [decimal_text(v.get(k, '')) for k in ['quantity', 'unit_price', 'line_amount']]
            item_desc = v.get('description') or ('Dòng ' + str(v.get('line_number', '?')))
            item_summary = f"{item_desc}: {v.get('quantity', '?')} {v.get('unit', '')} × {v.get('unit_price', '?')} = {v.get('line_amount', '?')} {v.get('currency', '')}".strip()
            item_sources = [{'id': r['id'], 'document': d['name'], 'type': 'Invoice', 'value': {'text': item_summary}, 'page': r['page']}]
            if all(n is not None for n in nums):
                good = Decimal(nums[0]) * Decimal(nums[1]) == Decimal(nums[2])
                add('arithmetic:' + r['id'], 'Matched' if good else 'Mismatch', f"Kiểm tra số lượng × đơn giá = thành tiền ({item_desc}; không tự điều chỉnh thuế/chiết khấu).", item_sources)
            else:
                add('arithmetic:' + r['id'], 'Needs Verification', f"Thiếu số lượng/đơn giá/thành tiền ở dòng hàng ({item_desc}) để kiểm tra số học.", item_sources)
        amounts = [decimal_text(r['value'].get('line_amount', '')) for r in items]
        if items and totals and all(v is not None for v in amounts) and totals[0]['value'].get('number') is not None:
            sum_val = sum((Decimal(v) for v in amounts), Decimal(0))
            inv_val = Decimal(totals[0]['value']['number'])
            same = sum_val == inv_val
            total_sources = [
                {'id': totals[0]['id'], 'document': d['name'], 'type': 'Invoice', 'value': {'text': f"Tổng các dòng: {format(sum_val, 'f')} vs Tổng hóa đơn: {format(inv_val, 'f')}"}, 'page': totals[0]['page']}
            ]
            add('total:' + d['id'], 'Matched' if same else 'Mismatch', f"Tổng dòng hàng ({format(sum_val, 'f')}) so với tổng Invoice {d['name']} ({format(inv_val, 'f')}); phụ phí/chiết khấu cần được nhân viên giải thích.", total_sources)

    # Containers compared by number, not by list order. Separate records retained in exports.
    containers = {}
    for r in active:
        if r['kind'] == 'container':
            number = container_number(r['value'].get('container_number'))
            containers.setdefault(number, []).append(r)
    for number, group in containers.items():
        seals = {r['value'].get('seal_number', '').strip().upper() for r in group if r['value'].get('seal_number')}
        types = {r['value'].get('container_type', '').strip().upper() for r in group if r['value'].get('container_type')}
        cont_sources = [{
            'id': r['id'],
            'document': docs.get(r['document_id'], {}).get('name', 'Nhập tay'),
            'value': r['value'],
            'page': r['page'],
        } for r in group]
        if not number:
            c_res = 'Needs Verification'
            c_reason = 'Bản ghi container chưa có số định danh; bổ sung từ chứng từ gốc.'
        elif len(seals) > 1 or len(types) > 1:
            c_res = 'Mismatch'
            c_reason = f'Sai lệch thông tin seal/loại của container vật lý {number} giữa các chứng từ nguồn.'
        elif len(group) > 1 and seals:
            c_res = 'Matched'
            c_reason = f'Container vật lý {number} khớp số seal ({", ".join(sorted(seals))}) trên {len(group)} bản ghi nguồn.'
        else:
            c_res = 'Needs Verification'
            c_reason = f'Container {number} mới có 1 nguồn hoặc thiếu số seal; cần đối chiếu chứng từ vận tải.'
        add('container:' + number, c_res, c_reason, cont_sources)
        weights = [normalize(r['value']['gross_weight'], 'weight') for r in group if r['value'].get('gross_weight')]
        if weights:
            values = [comparable(w) for w in weights]
            unclear = any(w['warning'] or w['unit'] != 'KG' for w in weights)
            weight_result = 'Needs Verification' if unclear or len(weights) < 2 else 'Matched' if len(set(values)) == 1 else 'Mismatch'
            add('container-weight:' + number, weight_result,
                f'Trọng lượng riêng container {number}: đối chiếu {len(weights)} nguồn có ghi trọng lượng và đơn vị; không lấy tổng trọng lượng lô để chia đều cho container.', cont_sources)
    return checks

def persist_checks(c, case, docs, records):
    old = {r['key']: dict(r) for r in c.execute('SELECT * FROM checks WHERE case_id=?', (case['id'],))}
    checks = build_checks(case, docs, records)
    c.execute('DELETE FROM checks WHERE case_id=?', (case['id'],))
    for check in checks:
        prior = old.get(check['key'])
        detail = encode(check['detail'])
        # A resolution becomes stale when evidence/value changes.
        resolution = prior['resolution'] if prior and prior['detail_json'] == detail and prior['result'] == check['result'] else ''
        c.execute('INSERT INTO checks VALUES (?,?,?,?,?,?,?)', (uid(), case['id'], check['key'], check['result'], check['severity'], detail, resolution))
    return checks

def human_check_label(key, docs_map=None):
    docs_map = docs_map or {}
    if key.startswith('document:'):
        sub=key.split(':',1)[1]
        return 'Checklist chứng từ · ' + ('Hợp đồng / Đơn đặt hàng' if sub=='Contract' else DOCUMENT_LABELS.get(sub,sub))
    if key.startswith('reading:'):
        doc_id = key.split(':', 1)[1]
        return 'Đọc tài liệu · ' + docs_map.get(doc_id, {}).get('name', doc_id)
    if key.startswith('classification:'):
        doc_id = key.split(':', 1)[1]
        return 'Xác nhận phân loại · ' + docs_map.get(doc_id, {}).get('name', doc_id)
    if key.startswith('transport:'):
        doc_id = key.split(':', 1)[1]
        return 'Cảnh báo phương thức vận tải · ' + docs_map.get(doc_id, {}).get('name', doc_id)
    if key.startswith('missing:'):
        sub = key.split(':', 1)[1]
        if sub == 'items':
            return 'Dữ liệu bắt buộc · Danh sách dòng hàng'
        if sub == 'containers':
            return 'Dữ liệu bắt buộc · Danh sách container'
        return 'Dữ liệu bắt buộc · ' + FIELDS.get(sub, {}).get('label', sub)
    if key.startswith('field:'):
        sub = key.split(':', 1)[1]
        return FIELDS.get(sub, {}).get('label', sub)
    if key.startswith('arithmetic:'):
        return 'Nhân số lượng × đơn giá dòng hàng'
    if key.startswith('total:'):
        doc_id = key.split(':', 1)[1]
        return 'Tổng thành tiền dòng hàng vs Tổng hóa đơn · ' + docs_map.get(doc_id, {}).get('name', '')
    if key.startswith('container:'):
        return 'Đối chiếu container vật lý · ' + key.split(':', 1)[1]
    if key.startswith('container-weight:'):
        return 'Trọng lượng riêng container · ' + key.split(':', 1)[1]
    return key

def blockers(case, docs, records, checks):
    result = []
    docs_map = {d['id']: d for d in docs}
    if not docs:
        result.append('Chưa có chứng từ')
    if not any(r['status'] != 'rejected' for r in records):
        result.append('Chưa có dữ liệu để xác minh')
    pending = [r for r in records if r['status'] not in ['verified', 'rejected']]
    if pending:
        result.append(f'{len(pending)} bản ghi chưa được xác minh')
    if any(d['status'] != 'read' or not d['type_verified'] for d in docs):
        result.append('Còn tài liệu chưa đọc hoặc chưa xác nhận loại')
    for check in checks:
        if check['result'] in ['Missing', 'Mismatch', 'Needs Verification'] and not check.get('resolution'):
            result.append(f"{human_check_label(check['key'], docs_map)}: chưa xử lý")
    return result
