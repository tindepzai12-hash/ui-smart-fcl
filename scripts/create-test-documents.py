"""Two matched synthetic FCL packets. No real trade documents or signatures."""
import io, json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT.parent / 'ui-smart/vendor')]
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageEnhance, ImageFilter

OUT = ROOT.parent / 'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)
QA = ROOT.parent / 'ui-smart/qa/test-packets'
QA.mkdir(parents=True, exist_ok=True)
for name, file in [('Regular', 'arial.ttf'), ('Bold', 'arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + file))
W, H = A4
BLUE = colors.HexColor('#183b56')
GRAY = colors.HexColor('#657783')
seller = 'NINGBO HAIAN TEST EXPORT CO., LTD. (FICTIONAL)'
buyer = 'MINH AN TEST IMPORT COMPANY (FICTIONAL)'
invoice = 'INV-000287-26'
bl = 'HBL-TEST-261014-009'
container = 'MSCU6639870'
seal = 'MA26101408'

def header(c, title, issuer, page):
    c.setFillColor(colors.HexColor('#f5e7c5'))
    c.rect(0, H-30, W, 30, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#70520b')); c.setFont('Bold', 9)
    c.drawCentredString(W/2, H-19, 'SYNTHETIC TEST DOCUMENT - NOT VALID FOR TRADE OR CUSTOMS')
    c.setFillColor(BLUE); c.setFont('Bold', 21); c.drawString(40, H-68, title)
    c.setFont('Regular', 9); c.setFillColor(GRAY); c.drawString(40, H-90, issuer)
    c.setStrokeColor(BLUE); c.line(40, H-103, W-40, H-103)
    c.setFillColor(GRAY); c.setFont('Regular', 8)
    c.drawString(40, 30, 'FCL TEST / U&I SMART - Internal verification only / No signature or official seal')
    c.drawRightString(W-40, 30, f'{page}/6')

def fields(c, rows, y=H-130):
    c.setFillColor(colors.HexColor('#182a35')); c.setFont('Regular', 9.5)
    for key, value in rows:
        c.drawString(40, y, f'{key}: {value}')
        y -= 20
    return y-12

def table(c, rows, widths, y):
    t = Table(rows, colWidths=widths, rowHeights=28)
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Regular'), ('FONTNAME', (0,0), (-1,0), 'Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e6edf1')),
        ('GRID', (0,0), (-1,-1), .55, colors.HexColor('#99aebc')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    _, height = t.wrap(W-80, H)
    t.drawOn(c, 40, y-height)
    return y-height-25

def note(c, lines, y):
    c.setFillColor(GRAY); c.setFont('Regular', 9)
    for line in lines:
        c.drawString(40, y, line); y -= 16

target = OUT / '01_FCL_Bo_chung_tu_ro_net.pdf'
c = canvas.Canvas(str(target), pagesize=A4)
c.setTitle('Synthetic FCL matched packet - selectable text')
c.setAuthor('U&I SMART - Synthetic QA fixtures')
header(c, 'COMMERCIAL INVOICE', seller, 1)
y = fields(c, [('Invoice No', invoice), ('Invoice Date', '2026-10-10'), ('Seller', seller),
    ('Seller Address', 'TEST ADDRESS, Ningbo, China'), ('Buyer', buyer),
    ('Buyer Address', 'DIA CHI GIA LAP, Ho Chi Minh City, Vietnam'),
    ('Currency', 'USD'), ('Incoterms', 'CIF Cat Lai, Incoterms 2020'),
    ('Payment Terms', 'T/T 30 days'), ('Country of Origin', 'CHINA'), ('Total Quantity', '2000 PCS'),
    ('Invoice Total', '23540.00')])
y = table(c, [['Item No','Product Code','Description','Quantity','Unit','Unit Price','Amount'],
    ['1','00128','Steel hinge A','1200','PCS','12.75','15300.00'],
    ['2','00456','Steel hinge B','800','PCS','10.30','8240.00']], [40,65,125,55,42,68,80], y)
note(c, ['Currency for all line amounts: USD.', 'Arithmetic check: 15300.00 + 8240.00 = 23540.00 USD.',
    'Commercial parties, addresses and references are fictional test data.'], y)
c.showPage()
header(c, 'PACKING LIST', seller, 2)
y = fields(c, [('Packing List No','PL-000287-26'), ('Invoice Reference',invoice), ('B/L No',bl),
    ('Shipper',seller), ('Consignee',buyer), ('Total Packages','100 CARTONS'), ('Total Quantity','2000 PCS'),
    ('Gross Weight','5200 KGS'), ('Net Weight','4910 KG'), ('Volume','21.60 CBM'), ('Shipping Marks','MINH AN TEST / 1-100')])
y = table(c, [['Item No','Product Code','Description','Quantity','Unit'],
    ['1','00128','Steel hinge A','1200','PCS'], ['2','00456','Steel hinge B','800','PCS']], [45,80,205,75,70], y)
y = table(c, [['Container','Seal','Type'], [container,seal,'40HC']], [180,180,115], y)
note(c, ['100 cartons / 2000 pieces - one physical container.', 'Weights refer to cargo; do not confuse with container tare or VGM.'], y)
c.showPage()
header(c, 'BILL OF LADING', 'TEST OCEAN FORWARDING LTD. - Fictional forwarder / House B/L', 3)
y = fields(c, [('B/L No',bl), ('Shipper',seller), ('Consignee',buyer), ('Notify Party',buyer),
    ('Vessel','TEST OCEAN STAR'), ('Voyage','026E'), ('Port of Loading','NINGBO'), ('Port of Discharge','CAT LAI'),
    ('Place of Delivery','CAT LAI'), ('ETA','2026-10-20'), ('Packages','100 CARTONS'), ('Gross Weight','5.20 MT'),
    ('Volume','21.60 CBM'), ('Freight Terms','FREIGHT PREPAID'), ('Description of Goods','2000 PCS STEEL HINGES / 100 CARTONS')])
y = table(c, [['Container','Seal','Type'], [container,seal,'40HC']], [180,180,115], y)
note(c, ['HOUSE BILL TEST SPECIMEN - not a negotiable transport document.', 'One physical 40HC container; no real carrier has issued this document.'], y)
c.showPage()
header(c, 'ARRIVAL NOTICE', 'TEST OCEAN FORWARDING LTD. - Fictional destination agent', 4)
y = fields(c, [('B/L No',bl), ('Consignee',buyer), ('Notify Party',buyer), ('Vessel','TEST OCEAN STAR'),
    ('Voyage','026E'), ('Port of Discharge','CAT LAI'), ('ETA','2026-10-20')])
y = table(c, [['Container','Seal','Type'], [container,seal,'40HC']], [180,180,115], y)
note(c, ['Shipment reference: INV-000287-26 / 100 cartons / 5200 KG.', 'This notice does not confirm customs release or permission to collect cargo.',
    'Contact: test-agent@example.invalid - deliberately non-operational address.'], y)
c.showPage()
header(c, 'DELIVERY ORDER', 'TEST OCEAN FORWARDING LTD. - Fictional destination agent', 5)
y = fields(c, [('Delivery Order No','DO-TEST-261020-009'), ('B/L No',bl)])
y = table(c, [['Container','Seal','Type'], [container,seal,'40HC']], [180,180,115], y)
note(c, ['Consignee: MINH AN TEST IMPORT COMPANY (FICTIONAL)', 'Issue date: 2026-10-20 / Test expiry: 2026-10-23.',
    'Conditional test document only. Not evidence of customs clearance.', 'No terminal, depot or trucking instruction is authorized by this specimen.'], y)
c.showPage()
header(c, 'CERTIFICATE OF ORIGIN', 'FICTIONAL TRAINING ISSUER - No preferential claim', 6)
y = fields(c, [('C/O No','CO-TEST-000287'), ('CO Form','TRAINING ONLY - NOT AN OFFICIAL FORM'),
    ('Issue Date','2026-10-11'), ('Issuing Authority','FICTIONAL TRAINING ISSUER'), ('Exporter',seller),
    ('Consignee',buyer), ('Invoice Reference',invoice), ('Country of Origin','CHINA'), ('Origin Criteria','TEST ONLY - NO LEGAL DETERMINATION')])
note(c, ['This page tests recognition of C/O fields only.', 'No issuing authority, origin criterion, stamp or signature is authenticated.',
    'Presence of this page must never imply eligibility for preferential duty.', 'Import permit / specialized inspection are not included; applicability requires review.'], y)
c.save()

# Raster-only PDF: mild skew, paper tone, blur and JPEG compression as in a photocopy.
source = pdfium.PdfDocument(str(target))
images = []
rng = random.Random(287)
for index in range(len(source)):
    im = source[index].render(scale=200/72).to_pil().convert('L')
    im = ImageEnhance.Contrast(im).enhance(.91)
    im = im.point(lambda v: min(248, int(v*.97+5)))
    im = im.rotate((.28,-.22,.35,-.25,.18,-.32)[index], resample=Image.Resampling.BICUBIC, expand=False, fillcolor=245)
    im = im.filter(ImageFilter.GaussianBlur(.22))
    # Repeatable scanner streak, outside the text block.
    from PIL import ImageDraw
    draw = ImageDraw.Draw(im)
    draw.line((35,80,35,im.height-65), fill=225, width=2)
    images.append(im.convert('RGB'))
scan_target = OUT / '02_FCL_Bo_chung_tu_scan.pdf'
images[0].save(scan_target, 'PDF', save_all=True, append_images=images[1:], resolution=200, quality=82)
assert len(PdfReader(target).pages) == len(PdfReader(scan_target).pages) == 6
assert all(len(p.extract_text()) > 100 for p in PdfReader(target).pages)
assert all(not p.extract_text().strip() for p in PdfReader(scan_target).pages)
for label, path in [('text',target),('scan',scan_target)]:
    doc = pdfium.PdfDocument(str(path))
    previews = []
    for i in range(len(doc)):
        img = doc[i].render(scale=.65).to_pil().convert('RGB')
        img.save(QA / f'{label}-{i+1}.png')
        previews.append(img)
    contact = Image.new('RGB',(previews[0].width*3,previews[0].height*2),'#dfe5e9')
    for i, img in enumerate(previews): contact.paste(img, ((i%3)*img.width,(i//3)*img.height))
    contact.save(QA / f'{label}-contact.png')
manifest = {'invoice':invoice,'bl':bl,'invoice_total':'23540.00','currency':'USD','items':2,'pieces':2000,
    'packages':'100 CTN','gross_weight_kg':'5200','net_weight_kg':'4910','volume_cbm':'21.60',
    'physical_containers':1,'container':container,'seal':seal,
    'page_types':['Invoice','Packing List','B/L','Arrival Notice','Delivery Order','C/O'],
    'scan_has_text_layer':False,'all_parties_fictional':True}
(QA / 'expected.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':[str(target),str(scan_target)],'bytes':[target.stat().st_size,scan_target.stat().st_size], 'pages':6}))
