import re
from decimal import Decimal, InvalidOperation
from datetime import datetime

UNITS = {
    'KGS': 'KG', 'KILOGRAMS': 'KG', 'KILOGRAM': 'KG', 'KG': 'KG',
    'MT': 'MT', 'TONNES': 'MT', 'TONNE': 'MT',
    'LBS': 'LB', 'LB': 'LB',
    'PCS': 'PCS', 'PIECES': 'PCS', 'PIECE': 'PCS',
    'CARTONS': 'CTN', 'CTNS': 'CTN', 'CARTON': 'CTN', 'CTN': 'CTN',
    'PALLETS': 'PLT', 'PALLET': 'PLT',
    'PKGS': 'PKG', 'PACKAGES': 'PKG', 'PACKAGE': 'PKG',
    'SETS': 'SET', 'CBM': 'CBM', 'M3': 'CBM',
}

def decimal_text(raw):
    s = str(raw).strip().replace(' ', '')
    if not re.fullmatch(r'[+-]?\d[\d.,]*', s):
        return None
    if ',' in s and '.' in s:
        dec = ',' if s.rfind(',') > s.rfind('.') else '.'
        group = '.' if dec == ',' else ','
        left, right = s.rsplit(dec, 1)
        if not re.fullmatch(r'[+-]?\d{1,3}(?:' + re.escape(group) + r'\d{3})+', left) and group in left:
            return None
        s = left.replace(group, '') + '.' + right
    elif ',' in s:
        if re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})+', s):
            # one separator is ambiguous (1,000 can be 1.000). Never silently choose.
            if s.count(',') == 1:
                return None
            s = s.replace(',', '')
        else:
            s = s.replace(',', '.') if s.count(',') == 1 else ''
    elif s.count('.') > 1:
        if re.fullmatch(r'[+-]?\d{1,3}(?:\.\d{3})+', s):
            s = s.replace('.', '')
        else:
            return None
    try:
        v = Decimal(s)
        return format(v, 'f') if v.is_finite() else None
    except InvalidOperation:
        return None

def normalize(raw, kind='text'):
    raw = str(raw).strip()
    result = {'text': raw, 'number': None, 'unit': None, 'warning': None}
    if kind in ['number', 'weight', 'quantity']:
        m = re.search(r'([+-]?\d[\d.,]*(?:[ ]\d{3})*)', raw)
        if not m:
            result['warning'] = 'Không xác định được giá trị số'
            return result
        num = decimal_text(m.group(1))
        unit = raw[m.end():].strip().upper().rstrip('.')
        unit = UNITS.get(unit, unit or None)
        if kind == 'weight' and unit == 'MT' and num is not None:
            num = format(Decimal(num) * 1000, 'f')
            unit = 'KG'
        elif kind == 'weight' and unit == 'LB' and num is not None:
            num = format(Decimal(num) * Decimal('0.45359237'), 'f')
            unit = 'KG'
        result.update(number=num, unit=unit)
        if num is None:
            result['warning'] = 'Dấu phân cách số chưa rõ. Nhập số không có dấu nhóm nghìn để xác minh.'
        elif kind in ['weight', 'quantity'] and unit is None:
            result['warning'] = 'Thiếu đơn vị; chưa thể so sánh chắc chắn.'
    elif kind == 'currency':
        result['text'] = raw.upper()
    elif kind == 'date':
        found = None
        matched_fmt = None
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y']:
            try:
                found = datetime.strptime(raw, fmt).date().isoformat()
                matched_fmt = fmt
                break
            except ValueError:
                pass
        if found:
            result['text'] = found
            if matched_fmt in ['%d/%m/%Y', '%d-%m-%Y']:
                parts = re.split(r'[/-]', raw)
                if len(parts) == 3:
                    first, second = int(parts[0]), int(parts[1])
                    if 1 <= first <= 12 and 1 <= second <= 12 and first != second:
                        result['warning'] = 'Ngày dạng dd/mm và mm/dd có thể mơ hồ (đang đọc theo dd/mm/yyyy). Hãy đối chiếu bản gốc và lưu dạng YYYY-MM-DD.'
        else:
            result['warning'] = 'Định dạng ngày chưa rõ, cần xác minh (khuyên dùng YYYY-MM-DD).'
    return result

def comparable(value):
    if value.get('warning'):
        return None
    if value.get('number') is not None:
        return (Decimal(value['number']), value.get('unit'))
    return re.sub(r'\s+', ' ', value.get('text', '')).casefold().strip()
