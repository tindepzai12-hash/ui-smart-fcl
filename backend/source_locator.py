"""Locate literal source values. OCR confidence is not a probability of correctness."""
import io, re, threading, hashlib, json
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageOps
from . import reader, db

_lock = threading.RLock()
LAYOUT_VERSION = 'bounded-gray-1600-sparse-v2'

def diagnostic_token(entry):
    return hashlib.sha256(json.dumps({k:v for k,v in entry.items() if k!='review'},sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def quote_boxes(words,evidence):
    """Highlight literal context fragments, never an invented position/value."""
    quote=tokens(evidence);out=[]
    for layer in dict.fromkeys(w['layer'] for w in words):
        stream=[(t,i) for i,w in enumerate(words) if w['layer']==layer for t in tokens(w['text'])]
        for start in range(len(stream)-2):
            phrase=[t[0] for t in stream[start:start+3]]
            if any(quote[j:j+3]==phrase for j in range(len(quote)-2)):
                for i in dict.fromkeys(t[1] for t in stream[start:start+3]):
                    if not any(b['layer']==layer and b['x']==words[i]['x'] and b['y']==words[i]['y'] for b in out):
                        out.append({**words[i],'attribute':'source_context','evidence_only':True})
    return out

def tokens(text):
    out=[]
    for token in re.findall(r'\w+', str(text).casefold(), re.UNICODE):
        # OCR often joins a quantity to its printed unit (42240SETS). Keep
        # numeric characters exact and leave alphanumeric reference codes intact.
        joined=re.fullmatch(r'(\d+)(kgs|kgm|kg|mt|lbs|lb|pcs|pce|sets|set|bags|ctn|drums|cbm)',token)
        out.extend(joined.groups() if joined else [token])
    return out


def vessel_context_boxes(words):
    """Only the name cell under Ocean vessel, never a neighbouring TEL/FAX."""
    boxes=[]
    for label in words:
        if tokens(label['text'])!=['vessel']:continue
        if not any(tokens(w['text']) in [['ocean'],['occan']] and w['layer']==label['layer']
                   and 0<label['x']-w['x']<.12 and abs(w['y']-label['y'])<.015 for w in words):continue
        region=[w for w in words if w['layer']==label['layer'] and label['y']+label['h']<=w['y']<label['y']+label['h']+.035
                and label['x']-.08<=w['x'] and w['x']+w['w']<=label['x']+.08]
        # Preserve the actual OCR spelling; this fallback locates context only.
        names=[w for w in region if re.fullmatch(r'[A-Za-z][A-Za-z.-]*',w['text'])]
        if names:
            first=min(w['y'] for w in names)
            boxes.extend({**w,'attribute':'vessel_cell','evidence_only':True} for w in names if abs(w['y']-first)<.012)
    return boxes


def bound_reader_boxes(record,page):
    """Reuse coordinates from extraction instead of locating a second name.

    A repeated vessel name elsewhere (e.g. a footer) is not the labelled cell.
    Metadata must still refer to literal source text and bounded coordinates.
    """
    if record.get('key')!='vessel':return []
    boxes=[];values=set()
    for raw in re.findall(r'<source-cell>(.*?)</source-cell>',page.get('quality','')):
        try:
            cell=json.loads(raw)
            if cell.get('key')!='vessel' or 'Ocean vessel: '+cell['value'] not in page['text']:continue
            words=cell['words']
            if ' '.join(w['text'] for w in words)!=cell['value']:continue
            if not all(0<=w['x']<1 and 0<=w['y']<1 and 0<w['w']<=1-w['x'] and 0<w['h']<=1-w['y'] for w in words):continue
            values.add(cell['value'])
            for w in words:
                if any(abs(b['x']-w['x'])<.002 and abs(b['y']-w['y'])<.002 for b in boxes):continue
                boxes.append({**w,'layer':'OCR labelled cell','attribute':'vessel','ambiguous':False,
                              'evidence_only':cell['value']!=record['raw']})
        except (ValueError,KeyError,TypeError):continue
    if len(values)>1:
        boxes=[{**b,'ambiguous':True} for b in boxes]
    return boxes

def ocr_words(image, psm=3):
    status = reader.ocr_status()
    if not status['ready']:
        raise ValueError('Chưa có OCR để định vị trên ảnh. Vẫn có thể xem bản gốc và câu trích dẫn.')
    reader.pytesseract.pytesseract.tesseract_cmd = status['cmd']
    if image.width*image.height>35_000_000:
        raise ValueError('Ảnh quá lớn để định vị OCR an toàn. Dùng bản scan nhỏ hơn.')
    # The source viewer needs coordinates, not another extraction pipeline.
    # Keep one bounded grayscale image; full-page RGB copies exhausted Free RAM.
    with ImageOps.exif_transpose(image) as oriented:
        gray = oriented.convert('L')
    try:
        gray.thumbnail((1600,1600), Image.Resampling.LANCZOS)
        with ImageOps.autocontrast(gray) as prepared:
            data = reader.pytesseract.image_to_data(prepared,
                # Start with the lighter Latin/numeric locator. Vietnamese
                # segmentation remains available on literal-match failure.
                lang='eng+vie' if psm==3 and 'vie' in status['languages'] else 'eng', config=f'--psm {psm}',
                output_type=reader.pytesseract.Output.DICT, timeout=18 if psm==11 else 8)
        width,height=gray.size
    finally:
        gray.close()
    words=[]
    for i,text in enumerate(data['text']):
        if not text.strip(): continue
        conf=float(data['conf'][i])
        words.append({'text':text, 'x':data['left'][i]/width, 'y':data['top'][i]/height,
            'w':data['width'][i]/width, 'h':data['height'][i]/height,
            'confidence':conf if conf >= 0 else None, 'layer':'OCR'})
    return words

@lru_cache(maxsize=32)
def _layout(path, stamp, size, number, method):
    ext=Path(path).suffix.lower()
    words=[]; image=None
    if ext=='.pdf':
        if reader.fitz is not None:
            with reader.fitz.open(path) as pdf:
                page=pdf[number-1]
                # Text coordinates are unrotated; transform to the rendered page's orientation.
                for w in page.get_text('words',sort=True):
                    rect=reader.fitz.Rect(w[:4])*page.rotation_matrix
                    words.append({'text':w[4], 'x':rect.x0/page.rect.width,'y':rect.y0/page.rect.height,
                        'w':rect.width/page.rect.width,'h':rect.height/page.rect.height,'confidence':None,'layer':'PDF text'})
        else:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                page=pdf.pages[number-1]
                words=[{'text':w['text'],'x':w['x0']/page.width,'y':w['top']/page.height,
                    'w':(w['x1']-w['x0'])/page.width,'h':(w['bottom']-w['top'])/page.height,
                    'confidence':None,'layer':'PDF text'} for w in page.extract_words()]
        if not words or 'OCR' in method:
            if reader.fitz is not None:
                with reader.fitz.open(path) as pdf:
                    page=pdf[number-1]
                    scale=min(200/72,1600/max(page.rect.width,page.rect.height))
                    pix=page.get_pixmap(matrix=reader.fitz.Matrix(scale,scale),colorspace=reader.fitz.csGRAY,alpha=False)
                    image=Image.frombytes('L',(pix.width,pix.height),pix.samples)
                    del pix
            else:
                image=Image.open(io.BytesIO(reader.render_pdf_page_png(path,number,150/72)))
    elif ext in {'.jpg','.jpeg','.png','.tif','.tiff'}:
        with Image.open(path) as original:
            original.seek(number-1)
            image=ImageOps.exif_transpose(original.copy())
    else:
        return []
    if image is not None:
        try:
            fallback=method.endswith('|full-fallback')
            words += [{**w,'layer':'OCR' if fallback else 'OCR sparse'} for w in ocr_words(image,3 if fallback else 11)]
        finally:
            image.close()
            reader.release_reader_memory()
    return words

@lru_cache(maxsize=64)
def _file_hash(path,stamp,size):
    with open(path,'rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def layout(path, number, method):
    stat=Path(path).stat()
    fingerprint=_file_hash(str(path),stat.st_mtime_ns,stat.st_size)
    key=hashlib.sha256(json.dumps([LAYOUT_VERSION,fingerprint,number,method]).encode()).hexdigest()
    folder=db.DATA/'source-layouts'
    cache=folder/(key+'.json')
    def cached():
        try:
            value=json.loads(cache.read_text(encoding='utf-8'))
            if isinstance(value,list) and all(isinstance(w,dict) and {'text','x','y','w','h','layer','confidence'}<=w.keys() for w in value):return value
        except (OSError,ValueError):pass
        return None
    value=cached()
    if value is not None:return value
    # Never queue several full-page OCR requests behind a global indefinite lock.
    if not _lock.acquire(timeout=1):
        raise ValueError('Máy chủ đang định vị trang khác. Bản gốc vẫn xem được; bấm Thử định vị lại sau vài giây.')
    try:
        value=cached()
        if value is not None:return value
        value=_layout(str(path),stat.st_mtime_ns,stat.st_size,number,method)
        try:
            folder.mkdir(exist_ok=True)
            temp=folder/(key+'.'+db.uid()+'.tmp')
            temp.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
            temp.replace(cache)
        except OSError:
            pass  # The in-memory layout remains usable if disk caching fails.
        return value
    finally:
        _lock.release()

def locate(words, raw, evidence):
    """Match exact word tokens; never fuzzy-repair digits (0/O, 1/I, etc.)."""
    values=raw if isinstance(raw,dict) else {'value':raw}
    result=[]
    for attribute,value in values.items():
        if attribute in {'line_number','scope','warning'} or value is None: continue
        needle=tokens(value)
        if not needle: continue
        candidates=[]
        for layer in dict.fromkeys(w['layer'] for w in words):
            stream=[]
            for index,w in enumerate(words):
                if w['layer']==layer:
                    stream.extend((token,index) for token in tokens(w['text']))
            for start in range(len(stream)-len(needle)+1):
                if [t[0] for t in stream[start:start+len(needle)]] != needle: continue
                indices=list(dict.fromkeys(t[1] for t in stream[start:start+len(needle)]))
                chosen=[words[i] for i in indices]
                # Nearby context ranks repeated values. Ties are exposed, never silently guessed.
                context={t[0] for t in stream[max(0,start-12):start+len(needle)+12]}
                score=len(context & set(tokens(evidence)))
                candidates.append((score,chosen))
        if not candidates: continue
        best=max(c[0] for c in candidates)
        selected=[c[1] for c in candidates if c[0]==best][:12]
        for chosen in selected:
            for w in chosen:
                box={**w,'attribute':attribute,'ambiguous':len(selected)>1}
                if not any(b['attribute']==attribute and abs(b['x']-box['x'])<.002 and abs(b['y']-box['y'])<.002 for b in result):
                    result.append(box)
    return result

def inspect(doc, record, page):
    method=page['method'] + (' sparse' if '[OCR sparse layer' in page['text'] else '')
    boxes=bound_reader_boxes(record,page); message='';retryable=False
    if boxes and any(b['evidence_only'] for b in boxes):message='Đánh dấu đúng ô tên tàu đã đọc; giá trị máy đọc cũ khác chữ trên ô này. Kiểm tra ký tự trước khi sửa.'
    try:
        words=[] if boxes else layout(doc['path'],page['number'],method)
        parts=record.get('value',{}).get('source_parts',[])
        if parts:
            for index,part in enumerate(parts):
                if part.get('page')==page['number']:
                    boxes.extend(locate(words,{'description_part_'+str(index+1):part['text']},record['evidence']))
            if boxes:message=record.get('value',{}).get('normalization_note') or 'Từng phần của giá trị đã được đánh dấu trên ô nguồn.'
        elif not boxes:
            boxes=locate(words,record['raw'],record['evidence'])
        if not boxes and record.get('key')=='vessel':
            boxes=vessel_context_boxes(words)
            if boxes:message='Đánh dấu ô tên tàu dưới nhãn Ocean vessel. Chữ trên ảnh chưa khớp giá trị máy đọc; kiểm tra ô này, không dùng dòng điện thoại.'
        if not boxes and record['evidence'] and record.get('key')!='vessel':
            raw=record['raw']
            candidate=' '.join(str(v) for k,v in raw.items() if v is not None and k not in {'line_number','scope'}) if isinstance(raw,dict) else str(raw)
            # A rejected value can combine distant cells. Highlight only its
            # literal fragments, not every word in a page-wide evidence quote.
            boxes=quote_boxes(words,candidate)
            if not boxes and len(tokens(record['evidence']))<=100:
                boxes=quote_boxes(words,record['evidence'])
            if not boxes and 0<len(tokens(record['evidence']))<=12:
                boxes=locate(words,{'source_evidence':record['evidence']},record['evidence'])
                boxes=[{**b,'evidence_only':True} for b in boxes]
            if boxes:message='Đánh dấu đoạn trích dẫn để kiểm tra ngữ cảnh; chưa chứng minh giá trị AI đúng.'
        if not boxes and 'OCR' in method:
            # Only pay for a second segmentation when the requested source was
            # not found. Keep this distinct layer and cache it across records.
            sparse=layout(doc['path'],page['number'],method+'|full-fallback')
            boxes=locate(sparse,record['raw'],record['evidence'])
            if not boxes and record.get('key')=='vessel':
                boxes=vessel_context_boxes(sparse)
                if boxes:message='Đánh dấu ô tên tàu; chữ trên ảnh chưa khớp giá trị máy đọc.'
            if not boxes and record.get('key')!='vessel' and 0<len(tokens(record['evidence']))<=100:
                boxes=quote_boxes(sparse,record['evidence'])
                if boxes:message='Đánh dấu đoạn trích dẫn để kiểm tra ngữ cảnh; chưa chứng minh giá trị AI đúng.'
    except (ValueError, RuntimeError, IndexError, OSError) as exc:
        message=str(exc)[:300]
        retryable=True
    low=[b for b in boxes if b['confidence'] is not None and b['confidence']<70]
    if not boxes and not message:
        message='Chưa định vị chắc chắn giá trị trên ảnh. Xem câu trích dẫn và toàn trang; hệ thống không đoán vị trí.'
    if record['method']=='Manual':
        message='Dữ liệu nhập/sửa thủ công: vùng đánh dấu chỉ là vị trí chữ khớp, cần tự kiểm tra căn cứ.'
    elif record['method'].startswith('Manual'):
        message='Giá trị đã được hiệu chỉnh. Vùng khoanh dựa vào chữ máy đọc gốc, không tự chứng minh bản sửa đúng.'
    return {'document_id':doc['id'],'name':doc['name'],'ext':doc['ext'],'page':page['number'],
        'method':page['method'],'quality':reader.quality_note(page['quality']),'text':page['text'],
        'raw':record['raw'],'evidence':record['evidence'],'boxes':boxes,'low_confidence_words':low,
        'ambiguous':any(b.get('ambiguous',False) for b in boxes),'message':message,'retryable':retryable,
        'confidence_note':'Độ tin cậy OCR chỉ phản ánh khả năng nhận chữ, không xác nhận giá trị đúng nghiệp vụ.'}
