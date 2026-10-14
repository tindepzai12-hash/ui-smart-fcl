"""Offline readers; preserve page/table boundaries. No document instructions executed."""
import csv, io, os, shutil, subprocess
from pathlib import Path
try:
    import fitz
except ImportError:
    fitz = None
from PIL import Image, ImageOps, ImageStat
from docx import Document
from openpyxl import load_workbook
import xlrd, pytesseract
from .db import ROOT

if (ROOT / 'tools/tessdata/eng.traineddata').exists():
    os.environ['TESSDATA_PREFIX'] = str(ROOT / 'tools/tessdata')
elif (ROOT / 'tools/ocr/usr/share/tesseract-ocr/5/tessdata/eng.traineddata').exists():
    os.environ['TESSDATA_PREFIX'] = str(ROOT / 'tools/ocr/usr/share/tesseract-ocr/5/tessdata')

SUPPORTED = {'.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.xlsx', '.xls', '.csv', '.txt', '.docx'}
MAX_BYTES = 25 * 1024 * 1024
MAX_PAGES = 100
Image.MAX_IMAGE_PIXELS = 35_000_000

def ocr_status():
    cloud_ocr = ROOT / 'tools/ocr/tesseract'
    candidate = os.getenv('TESSERACT_CMD') or (str(cloud_ocr) if cloud_ocr.exists() else shutil.which('tesseract'))
    for p in [ROOT / 'tools/tesseract/tesseract.exe', Path('C:/Program Files/Tesseract-OCR/tesseract.exe')]:
        if not candidate and p.exists():
            candidate = str(p)
    if not candidate:
        return {'ready': False, 'languages': [], 'detail': 'Chưa cài Tesseract OCR'}
    try:
        r = subprocess.run(
            [candidate, '--list-langs'],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        langs = [s.strip() for s in r.stdout.splitlines()[1:] if s.strip()]
        return {'ready': r.returncode == 0 and 'eng' in langs, 'languages': langs, 'detail': 'Tesseract local', 'cmd': candidate}
    except Exception:
        return {'ready': False, 'languages': [], 'detail': 'Không chạy được Tesseract'}

def ocr(image):
    status = ocr_status()
    if not status['ready']:
        raise ValueError('OCR local chưa sẵn sàng. Cài Tesseract và thử lại; PDF text vẫn đọc được.')
    pytesseract.pytesseract.tesseract_cmd = status['cmd']
    image = ImageOps.exif_transpose(image).convert('RGB')
    if image.width * image.height > 35_000_000:
        raise ValueError('Ảnh quá lớn để OCR an toàn')
    lang = 'eng+vie' if 'vie' in status['languages'] else 'eng'
    gray = ImageOps.autocontrast(ImageOps.grayscale(image))
    data = pytesseract.image_to_data(gray, lang=lang, config='--psm 6', output_type=pytesseract.Output.DICT, timeout=60)
    lines = {}
    scores = []
    for i, t in enumerate(data['text']):
        if not t.strip():
            continue
        key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
        lines.setdefault(key, []).append(t)
        if float(data['conf'][i]) >= 0:
            scores.append(float(data['conf'][i]))
    text = '\n'.join(' '.join(v) for v in lines.values())
    quality = []
    if not text.strip():
        raise ValueError('OCR không đọc được chữ. Hãy dùng bản scan rõ hơn.')
    if not scores or sum(scores) / len(scores) < 70:
        quality.append('OCR chất lượng thấp; kiểm tra từng giá trị với bản gốc.')
    if image.width < 800 or ImageStat.Stat(gray).stddev[0] < 20:
        quality.append('Ảnh nhỏ/độ tương phản thấp; có thể bỏ sót chữ.')
    if 'vie' not in status['languages']:
        quality.append('Chưa cài ngôn ngữ vie; dấu tiếng Việt có thể đọc sai.')
    return text, ' '.join(quality) or 'OCR cần nhân viên kiểm tra'

def decode(data):
    for encoding in ['utf-8-sig', 'utf-16', 'cp1258']:
        try:
            return data.decode(encoding)
        except UnicodeError:
            pass
    raise ValueError('Không đọc được encoding. Lưu file dưới UTF-8 và thử lại.')

def render_pdf_page_png(path, page_number, scale=1.5):
    path = Path(path)
    if fitz is not None:
        with fitz.open(path) as pdf:
            if page_number > len(pdf):
                raise ValueError('Không có trang này')
            pix = pdf[page_number - 1].get_pixmap(matrix=fitz.Matrix(scale, scale))
            return pix.tobytes('png')
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(path))
    try:
        if page_number > len(pdf):
            raise ValueError('Không có trang này')
        pil_img = pdf[page_number - 1].render(scale=scale).to_pil()
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        return buf.getvalue()
    finally:
        pdf.close()

def read_document(path, progress=lambda *_: None, cancelled=lambda: False):
    path = Path(path)
    ext = path.suffix.lower()
    pages = []

    def add(text, method, quality='', tables=None):
        if cancelled():
            raise InterruptedError('Đã hủy xử lý')
        if len(text) > 250000:
            raise ValueError('Một trang quá dài; giới hạn 250.000 ký tự')
        pages.append({'number': len(pages) + 1, 'text': text, 'method': method, 'quality': quality, 'tables': tables or []})
        progress(len(pages))

    if ext == '.pdf':
        if fitz is not None:
            with fitz.open(path) as pdf:
                if pdf.is_encrypted:
                    raise ValueError('PDF có mật khẩu. Hãy mở khóa trước khi tải lên.')
                if len(pdf) > MAX_PAGES:
                    raise ValueError('PDF vượt giới hạn 100 trang')
                for page in pdf:
                    if cancelled():
                        raise InterruptedError('Đã hủy xử lý')
                    text = page.get_text('text', sort=True)
                    tables = []
                    if len(text.strip()) >= 20:
                        try:
                            tables = [t.extract() for t in page.find_tables().tables]
                        except Exception:
                            pass
                        add(text, 'PDF text', '', tables)
                    else:
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        text, quality = ocr(Image.open(io.BytesIO(pix.tobytes('png'))))
                        add(text, 'OCR', quality)
        else:
            from pypdf import PdfReader
            import pdfplumber
            import pypdfium2 as pdfium
            try:
                reader_pdf = PdfReader(str(path))
            except Exception as exc:
                raise ValueError('Không đọc được tệp PDF: ' + str(exc))
            if reader_pdf.is_encrypted:
                raise ValueError('PDF có mật khẩu. Hãy mở khóa trước khi tải lên.')
            if len(reader_pdf.pages) > MAX_PAGES:
                raise ValueError('PDF vượt giới hạn 100 trang')
            with pdfplumber.open(str(path)) as plumber_pdf:
                pdfium_doc = pdfium.PdfDocument(str(path))
                try:
                    for idx, p_page in enumerate(plumber_pdf.pages):
                        if cancelled():
                            raise InterruptedError('Đã hủy xử lý')
                        text = p_page.extract_text() or ''
                        tables = []
                        if len(text.strip()) >= 20:
                            try:
                                tables = p_page.extract_tables() or []
                            except Exception:
                                pass
                            add(text, 'PDF text', '', tables)
                        else:
                            pil_img = pdfium_doc[idx].render(scale=2).to_pil()
                            text, quality = ocr(pil_img)
                            add(text, 'OCR', quality)
                finally:
                    pdfium_doc.close()
    elif ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
        with Image.open(path) as im:
            count = getattr(im, 'n_frames', 1)
            if count > MAX_PAGES:
                raise ValueError('Ảnh vượt giới hạn 100 trang')
            for n in range(count):
                im.seek(n)
                text, q = ocr(im.copy())
                add(text, 'OCR', q)
    elif ext == '.xlsx':
        wb = load_workbook(path, read_only=True, data_only=False)
        try:
            if len(wb.worksheets) > MAX_PAGES:
                raise ValueError('Workbook có quá nhiều sheet')
            for sheet in wb:
                if sheet.max_row > 10000 or sheet.max_column > 100:
                    raise ValueError('Sheet vượt 10.000 dòng hoặc 100 cột')
                table = [[str(v) if v is not None else '' for v in row] for row in sheet.iter_rows(values_only=True)]
                add(
                    sheet.title + '\n' + '\n'.join(' | '.join(r) for r in table),
                    'Excel',
                    'Đơn vị hiển thị là Sheet bảng tính (không phải trang in cố định). Công thức chỉ được đọc dưới dạng text, không chạy.',
                    [table],
                )
        finally:
            wb.close()
    elif ext == '.xls':
        wb = xlrd.open_workbook(path)
        for s in wb.sheets():
            if s.nrows > 10000 or s.ncols > 100:
                raise ValueError('XLS vượt giới hạn bảng')
            table = [[str(v) for v in s.row_values(i)] for i in range(s.nrows)]
            add(
                s.name + '\n' + '\n'.join(' | '.join(r) for r in table),
                'Excel',
                'Đơn vị hiển thị là Sheet bảng tính (không phải trang in cố định).',
                [table],
            )
    elif ext == '.docx':
        d = Document(path)
        tables = [[[cell.text for cell in row.cells] for row in t.rows] for t in d.tables]
        text = '\n'.join(p.text for p in d.paragraphs) + '\n' + '\n'.join(' | '.join(row) for table in tables for row in table)
        add(text, 'Word', 'Đơn vị hiển thị Word là khối nội dung logic; không phải số trang in cố định.', tables)
    elif ext in ['.txt', '.csv']:
        text = decode(path.read_bytes())
        tables = []
        if ext == '.csv':
            try:
                dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;\t|')
                tables = [list(csv.reader(io.StringIO(text), dialect))]
            except csv.Error:
                pass
        add(text, 'Text', '', tables)
    else:
        raise ValueError('Định dạng không hỗ trợ')
    if not pages or not any(p['text'].strip() for p in pages):
        raise ValueError('Tệp không có nội dung đọc được')
    return pages
