"""Locate literal source values. OCR confidence is not a probability of correctness."""
import io, re, threading
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageOps
from . import reader

_lock = threading.RLock()

def tokens(text):
    return re.findall(r'\w+', str(text).casefold(), re.UNICODE)

def ocr_words(image, psm=3):
    status = reader.ocr_status()
    if not status['ready']:
        raise ValueError('Chưa có OCR để định vị trên ảnh. Vẫn có thể xem bản gốc và câu trích dẫn.')
    reader.pytesseract.pytesseract.tesseract_cmd = status['cmd']
    image = ImageOps.exif_transpose(image).convert('RGB')
    if image.width*image.height>35_000_000:
        raise ValueError('Ảnh quá lớn để định vị OCR an toàn. Dùng bản scan nhỏ hơn.')
    # Normalized coordinates remain valid after scaling; use the same preparation as reading.
    image = reader.prepare_ocr_image(image)
    data = reader.pytesseract.image_to_data(ImageOps.autocontrast(ImageOps.grayscale(image)),
        lang='eng+vie' if 'vie' in status['languages'] else 'eng', config=f'--psm {psm}',
        output_type=reader.pytesseract.Output.DICT, timeout=60)
    words=[]
    for i,text in enumerate(data['text']):
        if not text.strip(): continue
        conf=float(data['conf'][i])
        words.append({'text':text, 'x':data['left'][i]/image.width, 'y':data['top'][i]/image.height,
            'w':data['width'][i]/image.width, 'h':data['height'][i]/image.height,
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
            image=Image.open(io.BytesIO(reader.render_pdf_page_png(path,number,200/72)))
    elif ext in {'.jpg','.jpeg','.png','.tif','.tiff'}:
        with Image.open(path) as original:
            original.seek(number-1)
            image=ImageOps.exif_transpose(original.copy())
    else:
        return []
    if image is not None:
        words += ocr_words(image)
        # Sparse OCR is already a distinct layer in stored source text. Do not blend readings.
        if 'sparse' in method:
            words += ocr_words(image,11)
    return words

def layout(path, number, method):
    stat=Path(path).stat()
    with _lock:
        return _layout(str(path),stat.st_mtime_ns,stat.st_size,number,method)

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
    boxes=[]; message=''
    try:
        boxes=locate(layout(doc['path'],page['number'],method),record['raw'],record['evidence'])
    except (ValueError, RuntimeError, IndexError, OSError) as exc:
        message=str(exc)[:300]
    low=[b for b in boxes if b['confidence'] is not None and b['confidence']<70]
    if not boxes and not message:
        message='Chưa định vị chắc chắn giá trị trên ảnh. Xem câu trích dẫn và toàn trang; hệ thống không đoán vị trí.'
    if record['method']=='Manual':
        message='Dữ liệu nhập/sửa thủ công: vùng đánh dấu chỉ là vị trí chữ khớp, cần tự kiểm tra căn cứ.'
    elif record['method'].startswith('Manual'):
        message='Giá trị đã được hiệu chỉnh. Vùng khoanh dựa vào chữ máy đọc gốc, không tự chứng minh bản sửa đúng.'
    return {'document_id':doc['id'],'name':doc['name'],'ext':doc['ext'],'page':page['number'],
        'method':page['method'],'quality':page['quality'],'text':page['text'],
        'raw':record['raw'],'evidence':record['evidence'],'boxes':boxes,'low_confidence_words':low,
        'ambiguous':any(b['ambiguous'] for b in boxes),'message':message,
        'confidence_note':'Độ tin cậy OCR chỉ phản ánh khả năng nhận chữ, không xác nhận giá trị đúng nghiệp vụ.'}
