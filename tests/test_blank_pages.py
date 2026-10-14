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
