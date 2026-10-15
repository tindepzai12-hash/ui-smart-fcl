import pytest
from backend import reader, ai


@pytest.mark.skipif(reader.fitz is None, reason='PyMuPDF not installed')
def test_original_pdf_sequence_preserves_multiline_description_and_separate_quantity(tmp_path):
    path=tmp_path/'table.pdf'
    with reader.fitz.open() as document:
        page=document.new_page()
        page.insert_text((40,45),'SALES CONTRACT')
        for y in [80,130,190]: page.draw_line((40,y),(540,y))
        for x in [40,280,365,450,540]: page.draw_line((x,80),(x,190))
        for x,label in [(45,'DESCRIPTION'),(285,'QTY (MT)'),(370,'UNIT PRICE'),(455,'AMOUNT')]:
            page.insert_text((x,105),label)
        # Stored text keeps the multiline cell together. Geometric sorting puts
        # the numeric columns between its two printed lines.
        page.insert_text((45,150),'BLUE BOLTS\nGRADE A',fontsize=10)
        for x,value in [(285,'3.5'),(370,'120.00'),(455,'420.00')]:
            page.insert_text((x,150),value,fontsize=10)
        geometric=page.get_text('text',sort=True)
        original=page.get_text('text',sort=False)
        assert ' '.join(original.split())!=' '.join(geometric.split())
        document.save(path)
    pages=reader.read_document(path)
    assert len(pages)==1 and pages[0]['method']=='PDF text'
    text=pages[0]['text']
    assert text.startswith(geometric) and text.endswith(original)
    assert '[PDF content-order layer' in text
    assert ai.evidence_ok('BLUE BOLTS GRADE A','BLUE BOLTS\nGRADE A',1,pages)
    assert not ai.evidence_ok('BLUE BOLTS GRADE B','BLUE BOLTS\nGRADE A',1,pages)
    result=ai.DocumentResult(document_type='Contract',classification_evidence='SALES CONTRACT',containers=[],
        fields=[ai.FieldResult(field_id='goods_quantity',raw_value='3.5',unit='MT',
            source_page=1,evidence_text='3.5',unit_evidence='QTY (MT)')],
        items=[ai.ItemResult(line_number='1',description='BLUE BOLTS GRADE A',quantity='3.5',unit='MT',
            source_page=1,evidence_text='BLUE BOLTS\nGRADE A\n3.5',cell_evidence=[
                ai.CellEvidence(attribute='description',evidence_text='BLUE BOLTS\nGRADE A'),
                ai.CellEvidence(attribute='quantity',evidence_text='3.5'),
                ai.CellEvidence(attribute='unit',evidence_text='QTY (MT)')])])
    records,rejected=ai.validated_subset(result,pages)
    assert not rejected and len(records)==2


def test_no_alternative_added_for_plain_text_or_identical_order():
    class Page:
        def get_text(self, *args, **kwargs): return 'Same text\n'
    assert reader.preserve_pdf_content_order(Page(),'Same text\n',[])=='Same text\n'
    assert reader.preserve_pdf_content_order(Page(),'Same  text\n',[[['header']]])=='Same  text\n'
