"""Conservative page grouping. A suggestion never confirms a document type."""
from .extraction import classify


def suggest(pages):
    groups = []
    for page in pages:
        kind, _ = classify([page])
        # Unknown headings can be continuation pages; staff must review the ranges.
        if groups and (kind == 'Other' or kind == groups[-1]['type']):
            groups[-1]['end'] = page['number']
        else:
            groups.append({'start': page['number'], 'end': page['number'], 'type': kind})
    return groups


def is_mixed(pages):
    kinds={g['type'] for g in suggest(pages)}-{'Other'}
    # A common two-part commercial packet can be read with page-specific provenance.
    return len(kinds)>1 and not kinds.issubset({'Invoice','Packing List','Invoice & Packing List'})


def validate_ranges(groups, total):
    if not 2 <= len(groups) <= 30:
        raise ValueError('Cần từ 2 đến 30 chứng từ sau khi tách.')
    cursor = 1
    for group in groups:
        if group.start != cursor or group.end < group.start or group.end > total:
            raise ValueError('Các khoảng trang phải liên tiếp, đúng thứ tự, không trùng hoặc bỏ sót trang.')
        cursor = group.end + 1
    if cursor != total + 1:
        raise ValueError('Phải phân bổ hết các trang của PDF gốc.')
