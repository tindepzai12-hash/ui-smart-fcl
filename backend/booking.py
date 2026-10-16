"""Literal booking cells and milestones; no completion from another document."""
import re

ROUTE_LABELS={'port_loading':'PORT OF LOADING','port_discharge':'PORT OF DISCHARGE',
              'place_delivery':'FINAL DESTINATION'}
DATE_TIME=r'\d{1,2} [A-Za-z]{3,9} \d{4} \d{1,2}:\d{2}(?:\s*\([A-Z]{2,5}\))?'

def layout_text(page):
    return page.get('text','').split('[PDF content-order layer',1)[0].split('[OCR line layer',1)[0]

def route_cells(page,key):
    """Keep only the left column, excluding labelled dates in the right column."""
    label=ROUTE_LABELS.get(key)
    if not label:return []
    lines=layout_text(page).splitlines();out=[]
    for i,line in enumerate(lines):
        m=re.match(r'^\s*'+re.escape(label)+r'\s*:\s*(\S.*)',line,re.I)
        if not m:continue
        right=re.search(r'\s{2,}(?:ETA|ETD|LTD)\s*:',m.group(1),re.I)
        if not right:continue  # No proof of a multi-column layout.
        column_end=m.start(1)+right.start()+len(right.group(0))-len(right.group(0).lstrip())
        first=m.group(1)[:right.start()].strip()
        if not first:continue
        parts=[first];end=i
        for j in range(i+1,min(i+4,len(lines))):
            following=lines[j]
            if not following.strip():break
            indent=len(following)-len(following.lstrip())
            if indent<m.start(1) or indent>=column_end or ':' in following:break
            cell=following[:column_end].strip()
            if not cell or re.search(r'\s{2,}\S',cell):break
            parts.append(cell);end=j
        quote='\n'.join(lines[i:end+1])
        out.append({'value':' '.join(parts),'evidence':quote,
                    'parts':[{'text':part,'page':page['number'],'label':label} for part in parts]})
    return out

def route_parts(key,value,evidence,page):
    norm=lambda s:re.sub(r'\s+',' ',s).strip().casefold()
    cells=[c for c in route_cells(page,key) if norm(c['value'])==norm(value)
           and norm(c['evidence']) in norm(evidence)]
    return cells[0]['parts'] if len(cells)==1 else []

def milestones(page):
    """Dates stay attached to their printed event, even if two events share a date."""
    text=layout_text(page);out=[]
    rules={
        'final_eta':r'(?im)^\s*FINAL DESTINATION:[^\n]*?\bETA\s*:\s*('+DATE_TIME+r')',
        'cargo_available_at':r'(?im)^\s*ESTIMATED CARGO AVAILABILITY AT DESTINATION HUB\s*:\s*('+DATE_TIME+r')',
        'vgm_cut_off':r'(?i)\b(?:INTENDED\s+)?VGM CUT-OFF\s*:\s*('+DATE_TIME+r')',
        'cy_cut_off':r'(?i)\b(?:INTENDED\s+)?(?:FCL\s+)?CY CUT-OFF\s*:\s*('+DATE_TIME+r')',
        'si_cut_off':r'(?i)\b(?:INTENDED\s+)?(?:ESI|SI) CUT-OFF\s*:\s*('+DATE_TIME+r')',
    }
    for key,pattern in rules.items():
        for m in re.finditer(pattern,text):
            out.append({'key':key,'value':m.group(1),'evidence':m.group(0),'page':page['number']})
    return out
