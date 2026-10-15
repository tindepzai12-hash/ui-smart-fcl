import io
import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from backend import reader
from fixtures import pdf, INVOICE


@pytest.mark.parametrize('fallback', [False, True])
def test_packet_retains_blank_page_between_text_pages(tmp_path, monkeypatch, fallback):
    if fallback:
        monkeypatch.setattr(reader, 'fitz', None)
    writer=PdfWriter()
    writer.add_page(PdfReader(io.BytesIO(pdf(INVOICE))).pages[0])
    writer.add_blank_page(width=595,height=842)
    writer.add_page(PdfReader(io.BytesIO(pdf('SALES CONTRACT\nContract No: C-001'))).pages[0])
    path=tmp_path/'packet.pdf';writer.write(path)
    pages=reader.read_document(path)
    assert [p['number'] for p in pages]==[1,2,3]
    assert pages[1]['text']=='' and pages[1]['method']=='Blank page'
    assert 'SALES CONTRACT' in pages[2]['text']


def test_unreadable_nonblank_page_still_fails(monkeypatch):
    image=Image.new('RGB',(1000,1400),'white')
    ImageDraw.Draw(image).rectangle((100,100,700,500),fill='black')
    def fail(*args,**kwargs):raise ValueError('Unreadable OCR')
    monkeypatch.setattr(reader,'ocr',fail)
    with pytest.raises(ValueError,match='Unreadable OCR'):
        reader.read_pdf_image(image)


def test_all_blank_pdf_is_not_a_successful_document(tmp_path):
    writer=PdfWriter();writer.add_blank_page(width=595,height=842)
    path=tmp_path/'blank.pdf';writer.write(path)
    with pytest.raises(ValueError,match='không có nội dung'):
        reader.read_document(path)


def test_ocr_timeout_is_actionable_and_thread_limit_is_set(monkeypatch):
    import os
    assert os.environ.get('OMP_THREAD_LIMIT')
    monkeypatch.setattr(reader,'ocr_status',lambda:{'ready':True,'cmd':'test','languages':['eng']})
    def timeout(*args,**kwargs):raise RuntimeError('Tesseract process timeout')
    monkeypatch.setattr(reader.pytesseract,'image_to_data',timeout)
    with pytest.raises(ValueError,match='60 giây'):
        reader.ocr(Image.new('RGB',(1000,1400),'white'))


def test_pdf_ocr_grayscale_retains_original_numbers_and_page_geometry(tmp_path):
    import pymupdf
    path=tmp_path/'weights.pdf'
    path.write_bytes(pdf('GROSS WEIGHT: 515.08 KGM\nNET WEIGHT: 391.20 KGM'))
    with pymupdf.open(path) as doc:
        page=doc[0]
        expected=page.get_pixmap(matrix=pymupdf.Matrix(200/72,200/72),colorspace=pymupdf.csGRAY,alpha=False)
        with reader.pdf_ocr_image(page) as image:
            assert image.mode=='L' and image.size==(expected.width,expected.height)
            assert image.tobytes()==expected.samples
        assert '515.08' in page.get_text() and '391.20' in page.get_text()
