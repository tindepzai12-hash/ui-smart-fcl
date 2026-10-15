import re, unicodedata
from .dictionary import FIELDS, supports
from .normalize import normalize,decimal_text

CLASS_RULES=[('Booking',r'booking\s+(?:confirmation|confirm|note|acknowledge?ment)|^booking$|xác nhận đặt chỗ'),('Packing List',r'packing\s+list'),('Sea Waybill',r'sea\s+waybill'),('B/L',r'bill\s+of\s+lading'),('AWB',r'air\s+waybill'),('C/O',r'certificate\s+of\s+origin'),('Arrival Notice',r'arrival\s+notice|notice of arrival'),('Delivery Order',r'delivery\s+order'),('Freight Invoice',r'freight\s+invoice'),('Invoice',r'commercial\s+invoice|^invoice$'),('Purchase Order',r'purchase\s+order'),('Contract',r'(?:sales?|purchase)\s+contract|(?:sales?|purchase)\s+agreement|^contract$|hợp\s+đồng(?:\s+mua\s+bán)?'),('Insurance',r'insurance\s+certificate'),('Import Permit',r'import\s+permit|import license'),('Phytosanitary Certificate',r'phytosanitary\s+certificate'),('Inspection Certificate',r'inspection\s+certificate')]

def classify(pages):
    if len(pages)>1:
        parts=[classify([p]) for p in pages]
        kinds={k for k,_ in parts}-{'Other'}
        if kinds=={'Invoice','Packing List'}:
            return 'Invoice & Packing List',next(q for k,q in parts if k=='Packing List')
    # Only document headings, never a contract's list of required attachments or a B/L reference label.
    lines=[line.strip() for p in pages[:1] for line in p['text'].splitlines() if line.strip()]
    # A contract continuation lists required attachments; those names are not
    # document headings. A new document with a real title above the clauses
    # still follows the ordinary classification path.
    if lines and re.match(r'(?i)^ARTICLE\s+\d+\b',lines[0]):
        return 'Other','Trang điều khoản tiếp nối; giữ cùng chứng từ trước.'
    source='\n'.join(lines)
    waybill=re.search(r'(?im)\bWAYBILL\s*$',source)
    if waybill and re.search(r'(?i)NON\s+NEGOTIABLE',source) and re.search(r'(?i)PORT\s+OF\s+LOADING',source):
        return 'Sea Waybill',waybill.group(0).strip()
    for line in lines:
        if len(line) > 100 or re.search(r'(?i)required|original signed|detailed|shipped on board|^\d+[.)]|^\[',line):
            continue
        if re.search(r'(?i)\binvoice\s*(?:&|and|/)\s*packing\s+list\b',line):
            return 'Invoice & Packing List',line
        for kind,pattern in CLASS_RULES:
            match=re.search(pattern,line,re.I)
            if not match:continue
            # Allow a short carrier/company prefix, not mentions embedded in narrative sentences.
            prefix=line[:match.start()].strip()
            suffix=line[match.end():].strip(' :–—-')
            if len(prefix.split()) <= 4 and not suffix and ':' not in prefix:
                return kind,line
    # A carrier's arrival notice often has its title embedded in a logo/raster stamp.
    text='\n'.join(lines)
    # OCR can preserve a Vietnamese word while dropping only its accents.
    # Match complete business headings after accent folding, but retain the
    # exact original line as evidence; do not repair numbers or fuzzy-match titles.
    for kind,pattern in [
        ('Customs Release',r'^du dieu kien qua khu vuc giam sat hai quan$'),
        ('Customs Declaration',r'^to khai hang hoa (?:xuat|nhap) khau(?:\s*\(thong quan\))?$'),
        ('Warehouse Receipt',r'^(?:yeu cau|phieu) nhap kho$'),
    ]:
        for line in lines:
            folded=''.join(c for c in unicodedata.normalize('NFD',line.casefold().replace('đ','d')) if not unicodedata.combining(c))
            if re.fullmatch(pattern,re.sub(r'\s+',' ',folded).strip()):return kind,line
    arrival=re.search(r'(?im)^.*(?:est\.?\s*arrival\s*date|estimated\s*time\s*of\s*arrival)\s*:\s*[^\n]+',text)
    if arrival and re.search(r'(?i)free\s*time\s*until',text):
        return 'Arrival Notice',arrival.group(0).strip()
    # Some carrier forms have no standalone title: the printed number heading and
    # carriage terms jointly identify a bill. A B/L reference alone is insufficient.
    bill_heading=re.search(r'(?im)\bBILL\s+OF\s+LADING\s+(?:NO\.?|NUMBER)\s*[:：]?\s*$',text)
    if bill_heading and re.search(r'(?i)FOR\s+COMBINED\s+TRANSPORT\s+SHIPMENT',text) and re.search(r'(?i)IN\s+WITNESS|RECEIVED\s+by\s+the\s+Carrier',text):
        return 'B/L',bill_heading.group(0).strip()
    return 'Other','Không có tiêu đề đủ rõ; chọn loại chứng từ thủ công.'

ITEM_ALIASES={'line_number':['item no','line','line no','item number','stt'],'product_code':['sku','product code','item code','model','mã hàng'],'description':['description','product description','description of goods','tên hàng'],'quantity':['quantity','qty','số lượng'],'unit':['unit','uom','đơn vị'],'unit_price':['unit price','price','đơn giá'],'line_amount':['line amount','amount','total','thành tiền'],'currency':['currency'],'origin':['country of origin','origin'],'hs_code':['hs code']}
CONT_ALIASES={'container_number':['container','container no','container number'],'seal_number':['seal','seal no','seal number'],'container_type':['type','container type'],'packages':['packages','package count'],'gross_weight':['gross weight'],'cbm':['cbm','volume'],'bl_number':['b/l no','bl number']}

def heading(s):return re.sub(r'[.:#]','',str(s)).strip().casefold()

def extract_tables(table,doc_type,page):
    output=[];mode=None;mapping={}
    for row in table:
        cells=[str(v or '').strip() for v in row]
        for kind,aliases,required in [('item',ITEM_ALIASES,{'description','quantity'}),('container',CONT_ALIASES,{'container_number'})]:
            proposed={idx:k for idx,cell in enumerate(cells) for k,labels in aliases.items() if heading(cell) in labels}
            if required.issubset(set(proposed.values())):mode=kind;mapping=proposed;break
        else:
            if mode and any(cells):
                values={key:cells[idx] if idx<len(cells) else '' for idx,key in mapping.items()}
                if mode=='item' and values.get('description') and decimal_text(values.get('quantity','')) is not None:
                    values.setdefault('line_number',str(len([o for o in output if o['kind']=='item'])+1))
                    if not re.fullmatch(r'\d+', values['line_number']):
                        values['warning']='Số thứ tự dòng chưa rõ; đối chiếu bảng gốc và sửa trước khi xác minh.'
                    for k in ['quantity','unit_price','line_amount']:
                        if k in values:
                            n=decimal_text(values[k])
                            if n is not None:values[k]=n
                            else:values['warning']='Có số chưa rõ định dạng; cần sửa trước khi xác minh.'
                    if not supports(doc_type,'Invoice'): values['scope']='booking' if doc_type=='Booking' else 'contract' if doc_type in ['Contract','Purchase Order'] else 'origin' if doc_type=='C/O' else 'packing'
                    output.append({'kind':'item','key':'goods_item','value':values,'raw':{key:cells[idx] if idx<len(cells) else '' for idx,key in mapping.items()},'page':page,'evidence':' | '.join(cells),'method':'Rules/table'})
                elif mode=='container' and re.fullmatch(r'[A-Z]{4}\d{7}',re.sub(r'\s','',values.get('container_number','')).upper()):
                    values['container_number']=re.sub(r'\s','',values['container_number']).upper()
                    output.append({'kind':'container','key':'container','value':values,'raw':values.copy(),'page':page,'evidence':' | '.join(cells),'method':'Rules/table'})
    return output

def extract(pages,doc_type):
    out=[];seen=set()
    for p in pages:
        text=p['text'].replace('\r','');number=p['number']
        for key,spec in FIELDS.items():
            if doc_type not in spec['documents'] or not spec['aliases']:continue
            alternatives='|'.join(re.escape(a)+r'\.?' for a in sorted(spec['aliases'],key=len,reverse=True))
            # Anchored labels prevent quantities in narrative and reference headings being consumed.
            pattern=r'(?im)^\s*(?:'+alternatives+r')\s*(?:[:：#=]\s*|\s+-\s+)([^\n]+)'
            for match in re.finditer(pattern,text):
                raw=match.group(1).strip()
                if not raw or len(raw)>500:continue
                token=(key,raw,number)
                if token in seen:continue
                seen.add(token);out.append({'kind':'field','key':key,'raw':raw,'value':normalize(raw,spec['type']),'page':number,'evidence':match.group(0).strip(),'method':'Rules'})
            # Party labels sometimes stand alone followed by the company name.
            if spec['type']=='text' and not any(o['key']==key for o in out):
                m=re.search(r'(?im)^\s*(?:'+alternatives+r')\s*[:：]?\s*\n([^\n:]{3,200})$',text)
                if m:out.append({'kind':'field','key':key,'raw':m.group(1).strip(),'value':normalize(m.group(1).strip()),'page':number,'evidence':m.group(0).strip(),'method':'Rules'})
        tables=p.get('tables') or []
        if not tables:
            lines=[re.split(r'\s*\|\s*',l) for l in text.splitlines() if '|' in l]
            if lines:tables=[lines]
        page_type=classify([p])[0] if doc_type=='Invoice & Packing List' else doc_type
        for table in tables:out.extend(extract_tables(table,page_type,number))
        if not any(o['kind']=='container' and o['page']==number for o in out):
            for m in re.finditer(r'(?im)^.*(?:container(?: no\.?| number)?\s*[:：]\s*)([A-Z]{4}\s*\d{7})[^\n]*',text):
                line=m.group(0);seal=re.search(r'seal(?: no\.?| number)?\s*[:：]\s*([A-Z0-9/-]+)',line,re.I)
                value={'container_number':re.sub(r'\s','',m.group(1)).upper(),'seal_number':seal.group(1) if seal else ''}
                out.append({'kind':'container','key':'container','value':value,'raw':value.copy(),'page':number,'evidence':line,'method':'Rules'})
    return out
