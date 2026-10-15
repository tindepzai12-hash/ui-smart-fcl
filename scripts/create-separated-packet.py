"""Matched synthetic fixture packets; reference images must never be included."""
from pathlib import Path
import io, json, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8')
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'output/pdf/FCL_8_File_Gia_Lap'
TEXT = OUT / '01_Chung_tu_ro_net'
SCAN = OUT / '02_Chung_tu_scan'
QA = ROOT.parent / 'tmp/pdfs/FCL_8_File_Gia_Lap'
for folder in [TEXT, SCAN, QA]: folder.mkdir(parents=True, exist_ok=True)
original = PdfReader(ROOT / 'samples/fcl-text.pdf')
scanned = PdfReader(ROOT / 'samples/fcl-scan.pdf')
assert len(original.pages) == len(scanned.pages) == 6
types = ['Invoice', 'Packing List', 'B/L', 'Arrival Notice', 'Delivery Order', 'C/O', 'Contract', 'Insurance']
for i in range(6):
    for source, folder in [(original, TEXT), (scanned, SCAN)]:
        writer = PdfWriter()
        writer.add_page(source.pages[i])
        writer.add_metadata({})
        writer.write(folder / f'{i+1}.pdf')
        if folder == TEXT:
            assert PdfReader(folder / f'{i+1}.pdf').pages[0].extract_text() == source.pages[i].extract_text()

seller = 'NINGBO HAIAN TEST EXPORT CO., LTD. (FICTIONAL)'
buyer = 'MINH AN TEST IMPORT COMPANY (FICTIONAL)'
invoice = 'INV-000287-26'
bl = 'HBL-TEST-261014-009'
container = 'MSCU6639870'
seal = 'MA26101408'
for name, title, issuer, lines in [
    ('7', 'SALES CONTRACT', 'Fictional seller and buyer - training specimen', [
        'Contract No: SC-TEST-000287-26', 'Contract Date: 2026-10-01',
        'Seller: '+seller, 'Buyer: '+buyer,
        'Seller Address: TEST ADDRESS, Ningbo, China',
        'Buyer Address: DIA CHI GIA LAP, Ho Chi Minh City, Vietnam',
        'Invoice Reference: '+invoice,
        'Currency: USD', 'Incoterms: CIF Cat Lai, Incoterms 2020', 'Payment Terms: T/T 30 days',
        'Port of Loading: NINGBO', 'Port of Discharge: CAT LAI', 'Country of Origin: CHINA',
        'Goods: Steel hinge A: 1200 PCS x 12.75 USD = 15300.00 USD',
        'Goods: Steel hinge B: 800 PCS x 10.30 USD = 8240.00 USD',
        'Total Quantity: 2000 PCS', 'Contract Total: USD 23540.00',
        'Amount in words: Twenty-three thousand five hundred forty US dollars only.',
        'Shipment: one FCL 40HC container; 100 cartons; no real booking.',
        'Test documents: Invoice, Packing List, B/L, C/O and insurance certificate.',
        'This specimen does not determine import permits, HS codes or customs taxes.',
        'No actual contract has been agreed or signed.'
    ]),
    ('8', 'INSURANCE CERTIFICATE', 'FICTIONAL TRAINING INSURER - no actual insurance coverage', [
        'Insurance Policy No: INS-TEST-000287-26', 'Issue Date: 2026-10-11',
        'Insured: '+buyer, 'Invoice Reference: '+invoice, 'B/L No: '+bl,
        'Shipper: '+seller, 'Consignee: '+buyer,
        'Vessel: TEST OCEAN STAR', 'Voyage: 026E',
        'Port of Loading: NINGBO', 'Port of Discharge: CAT LAI',
        'Goods: 2000 PCS steel hinges, packed in 100 cartons.',
        'Container: '+container, 'Seal: '+seal, 'Container Type: 40HC',
        'Gross Weight: 5200 KG', 'Net Weight: 4910 KG', 'Volume: 21.60 CBM',
        'Invoice Amount: USD 23540.00', 'Sum Insured: USD 25894.00',
        'Test insured amount = 110% x commercial invoice amount.',
        'Sum insured and invoice amount are different scopes; do not mark them mismatched.',
        'Fictional conditions: training specimen only; no insurer or coverage authenticated.',
        'No insurance claim, customs clearance or cargo release is authorized.'
    ])]:
    path = TEXT / (name + '.pdf')
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    c.setFillColorRGB(.95,.9,.75); c.rect(0,h-32,w,32,fill=1,stroke=0)
    c.setFillColorRGB(.35,.25,.05); c.setFont('Helvetica-Bold',9)
    c.drawCentredString(w/2,h-20,'SYNTHETIC TEST DOCUMENT - NOT VALID FOR TRADE OR CUSTOMS')
    c.setFillColorRGB(.08,.16,.25); c.setFont('Helvetica-Bold',20); c.drawString(40,h-72,title)
    c.setFont('Helvetica',9); c.drawString(40,h-95,issuer)
    c.line(40,h-108,w-40,h-108)
    y = h-135
    for line in lines:
        c.setFont('Helvetica',9)
        assert c.stringWidth(line,'Helvetica',9) < w-80, line
        c.drawString(40,y,line); y-=23
    c.setFont('Helvetica',8); c.drawString(40,32,'U&I SMART - Synthetic test / No genuine signature, stamp or legal validity')
    c.save()
    pdf = pdfium.PdfDocument(str(path))
    im = pdf[0].render(scale=200/72).to_pil().convert('L')
    im = im.rotate(.24,resample=Image.Resampling.BICUBIC,fillcolor=248).filter(ImageFilter.GaussianBlur(.18))
    im.convert('RGB').save(SCAN/(name+'.pdf'),'PDF',resolution=200)

previews = []
for i in range(1,9):
    for folder, prefix in [(TEXT,'text'),(SCAN,'scan')]:
        path = folder / f'{i}.pdf'
        reader = PdfReader(path)
        assert len(reader.pages) == 1
        assert bool(reader.pages[0].extract_text().strip()) == (prefix=='text')
        doc = pdfium.PdfDocument(str(path))
        im = doc[0].render(scale=.8).to_pil().convert('RGB')
        im.save(QA/f'{prefix}-{i}.png')
        if prefix=='text': previews.append(im)
contact = Image.new('RGB',(previews[0].width*4,previews[0].height*2),'#dfe5e9')
for i,im in enumerate(previews): contact.paste(im,((i%4)*im.width,(i//4)*im.height))
contact.save(QA/'contact.png')
manifest = {'all_data_synthetic':True,'types':dict(zip([f'{i}.pdf' for i in range(1,9)],types)),
            'invoice':invoice,'bl':bl,'items':2,'quantity_pcs':2000,'packages_ctn':100,
            'invoice_total_usd':'23540.00','sum_insured_usd':'25894.00','net_weight_kg':4910,'gross_weight_kg':5200,
            'volume_cbm':'21.60','container':container,'seal':seal,'container_type':'40HC',
            'origin':'CHINA','port_loading':'NINGBO','port_discharge':'CAT LAI',
            'no_photos_or_screenshots_in_document_packet':True,'scan_text_layer':False,
            'no_legal_determination': 'HS, duty, C/O eligibility and import permit applicability require professional verification.'}
(OUT/'KET_QUA_MONG_DOI.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
readme = '''BỘ KIỂM THỬ GIẢ LẬP - không phải bộ chứng từ thật tìm từ doanh nghiệp.
Mọi trang đều ghi rõ không có giá trị thương mại/hải quan. Không dùng cho lô hàng thật.

01_Chung_tu_ro_net: chọn đồng thời 1.pdf đến 8.pdf, tải vào Chứng từ của một hồ sơ mới.
02_Chung_tu_scan: bộ giấy tờ cùng nội dung, PDF chỉ có ảnh; thử trong một hồ sơ khác.
1 Invoice; 2 Packing List; 3 B/L; 4 Arrival Notice; 5 Delivery Order; 6 C/O;
7 Contract; 8 Insurance. Tên số dùng để kiểm tra nhận diện theo nội dung.

AI: chọn OpenAI, đọc thông báo gửi dữ liệu, đồng ý rồi bấm Đọc & trích xuất.
Local: đọc bằng rules/OCR; thiếu OCR phải cài/cấu hình trước khi thử bộ scan.
Đối chiếu KET_QUA_MONG_DOI.json. Bản ghi chờ xác minh không có nghĩa bản ghi sai.
Nhân viên xác nhận loại và kiểm tra giá trị với bản gốc trước khi duyệt hồ sơ.
C/O chỉ kiểm thử nhận diện, không chứng minh đủ điều kiện hưởng ưu đãi.
Bảo hiểm 25894 USD khác invoice 23540 USD: phạm vi khác, không phải lỗi.
Không thêm giấy phép/kiểm dịch giả để ép checklist qua. Bộ này không xác nhận yêu cầu pháp lý cho một mặt hàng thật.

Chỉ tải chứng từ của lô; ảnh container, seal, hàng hóa hoặc màn hình tra cứu không nằm trong bộ kiểm thử này.
Ảnh chụp hoặc scan Invoice/Packing List/B/L vẫn tải tại Chứng từ.
Bộ kiểm thử giấy tờ này KHÔNG chứa ảnh hiện trường hoặc ảnh màn hình.
'''
(OUT/'DOC_TRUOC_KHI_TEST.txt').write_text(readme,encoding='utf-8-sig')
archive = OUT.parent / 'FCL_8_Chung_Tu_Rieng_Ro_Net_Va_Scan.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in OUT.rglob('*'):
        if path.is_file(): z.write(path,path.relative_to(OUT))
print(json.dumps({'archive':str(archive),'files':16,'size':archive.stat().st_size},ensure_ascii=False))
