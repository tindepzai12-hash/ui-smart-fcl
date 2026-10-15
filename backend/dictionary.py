"""Stable field IDs and document-specific semantics; legal codes are never inferred."""
TYPES=['Packing List','Booking','Invoice','Invoice & Packing List','Contract','Purchase Order','C/O','B/L','Sea Waybill','AWB','Arrival Notice','Delivery Order','Insurance','Freight Invoice','Import Permit','Inspection Certificate','Phytosanitary Certificate','Other']
DOCUMENT_LABELS={'Contract':'Hợp đồng / Sales Contract','Purchase Order':'Đơn đặt hàng / Purchase Order','C/O':'C/O · nếu có','Booking':'Booking / Booking Confirmation'}

def supports(document_type, kind):
    return document_type == kind or (document_type == 'Invoice & Packing List' and kind in ['Invoice', 'Packing List']) or (kind == 'Contract' and document_type == 'Purchase Order')
# id, Vietnamese label, aliases, type, applicable documents, business class
SPECS=[
('invoice_number','Số hóa đơn',['invoice no','invoice number','commercial invoice no','invoice reference','số hóa đơn'],'text',['Invoice','Packing List','C/O','Contract','Purchase Order'],'A'),
('invoice_date','Ngày hóa đơn',['invoice date','date of invoice','ngày hóa đơn'],'date',['Invoice'],'A'),
('seller','Người bán',['seller','seller/exporter','supplier','người bán'],'text',['Invoice','Contract','Purchase Order'],'A'),
('buyer','Người mua',['buyer','bill to','sold to','người mua'],'text',['Invoice','Contract','Purchase Order'],'A'),
('exporter','Người xuất khẩu',['exporter','người xuất khẩu'],'text',['Invoice','C/O','Contract'],'A'),
('importer','Người nhập khẩu',['importer','người nhập khẩu'],'text',['Invoice','C/O','Contract'],'A'),
('shipper','Người gửi hàng',['shipper','consignor','người gửi hàng'],'text',['B/L','Sea Waybill','AWB','Packing List','Arrival Notice'],'A'),
('consignee','Người nhận hàng',['consignee','người nhận hàng'],'text',['B/L','Sea Waybill','AWB','Packing List','Arrival Notice','C/O'],'A'),
('notify_party','Bên được thông báo',['notify party','also notify'],'text',['B/L','Sea Waybill','Arrival Notice'],'A'),
('importer_tax_id','Mã số thuế người nhập khẩu',['importer tax id','buyer tax id','mã số thuế người nhập khẩu'],'text',['Invoice','Contract'],'C'),
('currency','Đồng tiền hóa đơn',['currency','invoice currency','đồng tiền'],'currency',['Invoice','Freight Invoice'],'A'),
('incoterms','Điều kiện Incoterms và địa điểm',['incoterms','delivery terms','terms of delivery','điều kiện giao hàng'],'text',['Invoice','Contract'],'A'),
('payment_terms','Điều khoản thanh toán',['payment terms','terms of payment'],'text',['Invoice','Contract'],'A'),
('invoice_total','Tổng trị giá hóa đơn',['invoice total','grand total','total amount','total invoice value','tổng trị giá'],'number',['Invoice'],'A'),
('packing_number','Số Packing List',['packing list no','packing list number'],'text',['Packing List'],'A'),
('bl_number','Số vận đơn biển',['b/l no','b/l number','bill of lading no','bill of lading number','sea waybill no','số vận đơn'],'text',['B/L','Sea Waybill','Packing List','Arrival Notice','Delivery Order'],'A'),
('awb_number','Số vận đơn hàng không',['awb no','awb number','air waybill no'],'text',['AWB'],'A'),
('booking','Số booking',['booking no','booking reference'],'text',['B/L','Sea Waybill'],'A'),
('vessel','Tên tàu',['vessel','vessel name','ocean vessel'],'text',['B/L','Sea Waybill','Arrival Notice'],'A'),
('voyage','Số chuyến',['voyage','voyage no'],'text',['B/L','Sea Waybill','Arrival Notice'],'A'),
('port_loading','Cảng xếp hàng',['port of loading','loading port'],'text',['B/L','Sea Waybill'],'A'),
('port_discharge','Cảng dỡ hàng',['port of discharge','discharge port'],'text',['B/L','Sea Waybill','Arrival Notice'],'A'),
('airport_departure','Sân bay đi',['airport of departure'],'text',['AWB'],'A'),
('airport_destination','Sân bay đến',['airport of destination'],'text',['AWB'],'A'),
('flight','Chuyến bay',['flight','flight details'],'text',['AWB'],'A'),
('chargeable_weight','Trọng lượng tính cước',['chargeable weight'],'weight',['AWB'],'A'),
('eta','Ngày đến dự kiến',['eta','estimated time of arrival'],'date',['Arrival Notice','B/L','Sea Waybill'],'A'),
('arrival_date','Ngày hàng đến ghi trên thông báo/lệnh',['arrival date','ngày hàng đến'],'date',['Arrival Notice','Delivery Order'],'A'),
('packages','Số kiện và loại bao bì',['number of packages','total packages','package count','packages','số kiện'],'quantity',['Packing List','B/L','Sea Waybill','AWB'],'A'),
('goods_quantity','Tổng số lượng hàng',['total quantity','goods quantity','quantity','qty','số lượng hàng'],'quantity',['Invoice','Packing List'],'A'),
('gross_weight','Trọng lượng cả bì',['gross weight','gross wt','g.w.','gross mass','trọng lượng cả bì'],'weight',['Packing List','B/L','Sea Waybill','AWB'],'A'),
('net_weight','Trọng lượng tịnh',['net weight','net wt','n.w.','trọng lượng tịnh'],'weight',['Packing List','Invoice'],'A'),
('volume','Thể tích',['cbm','measurement','volume'],'quantity',['Packing List','B/L','Sea Waybill'],'A'),
('shipping_marks','Ký mã hiệu',['shipping marks','marks and numbers'],'text',['Packing List','B/L','Sea Waybill'],'A'),
('origin','Nước xuất xứ',['country of origin','origin of goods','country of manufacture','xuất xứ hàng hóa'],'text',['Invoice','C/O'],'A'),
('co_number','Số chứng nhận xuất xứ',['c/o no','certificate of origin no','co reference'],'text',['C/O'],'A'),
('co_form','Mẫu C/O',['co form','form','type of certificate'],'text',['C/O'],'A'),
('co_issuer','Cơ quan cấp C/O',['issuing authority'],'text',['C/O'],'A'),
('co_date','Ngày cấp C/O',['issue date'],'date',['C/O'],'A'),
('origin_criteria','Tiêu chí xuất xứ',['origin criteria','origin criterion'],'text',['C/O'],'A'),
('freight_terms','Điều kiện cước',['freight terms','freight payment'],'text',['B/L','Sea Waybill'],'A'),
('contract_number','Số hợp đồng',['contract no','sales contract no'],'text',['Contract'],'A'),
('po_number','Số đơn đặt hàng',['po no','purchase order no'],'text',['Purchase Order'],'A'),
('do_number','Số lệnh giao hàng',['delivery order no','d/o no'],'text',['Delivery Order'],'A'),
('seller_address','Địa chỉ người bán',['seller address','supplier address'],'text',['Invoice','Contract'],'A'),
('buyer_address','Địa chỉ người mua',['buyer address','bill to address'],'text',['Invoice','Contract'],'A'),
('exporter_address','Địa chỉ người xuất khẩu',['exporter address'],'text',['Invoice','C/O','Contract'],'A'),
('importer_address','Địa chỉ người nhập khẩu',['importer address'],'text',['Invoice','Contract'],'A'),
('shipper_address','Địa chỉ người gửi hàng',['shipper address'],'text',['B/L','Sea Waybill','AWB'],'A'),
('consignee_address','Địa chỉ người nhận hàng',['consignee address'],'text',['B/L','Sea Waybill','AWB'],'A'),
('place_receipt','Nơi nhận hàng',['place of receipt'],'text',['B/L','Sea Waybill'],'A'),
('place_delivery','Nơi giao hàng',['place of delivery'],'text',['B/L','Sea Waybill'],'A'),
('cargo_description','Mô tả tổng lô vận tải',['description of goods','goods description','nature and quantity of goods'],'text',['B/L','Sea Waybill','AWB'],'A'),
('freight_amount','Phí vận tải ghi trên chứng từ',['freight amount','freight charge','freight total'],'number',['Freight Invoice','Invoice'],'A'),
('insurance_amount','Trị giá bảo hiểm ghi trên chứng từ',['insurance amount','insured amount'],'number',['Insurance'],'A'),
('permit_number','Số giấy phép',['import permit no','permit no','import license no'],'text',['Import Permit'],'A'),
('inspection_number','Số chứng nhận kiểm tra',['inspection certificate no','certificate no'],'text',['Inspection Certificate','Phytosanitary Certificate'],'A'),
('hs_code','Mã HS',['hs code','mã hs'],'text',[],'D'),
('declaration_type','Mã loại hình',[],'text',[],'C'),
('customs_office','Mã đơn vị hải quan',[],'text',[],'C'),
('storage_code','Mã địa điểm lưu kho',[],'text',[],'C'),
('discharge_code','Mã địa điểm dỡ hàng',[],'text',[],'C'),
('origin_code','Mã nước xuất xứ',[],'text',[],'C'),
('transport_code','Mã phương thức vận chuyển',[],'text',[],'C'),
('tax_rate','Thuế suất đã tra cứu',[],'number',[],'D'),
('customs_value','Trị giá hải quan đã xác định',[],'number',[],'D')]
FIELDS={s[0]:{'id':s[0],'label':s[1],'aliases':s[2],'type':s[3],'documents':s[4],'class':s[5],'level':'document','human_review':True,'sheet':'THONG_TIN_KHAI_BAO','official_mapping':'Pending — cần mẫu chỉ tiêu và danh mục hiện hành'} for s in SPECS}
for field,kinds in {
    'origin':['Contract'],
    'contract_number':['Invoice','Packing List'],
    'port_loading':['Invoice','Packing List','Contract','Arrival Notice','Delivery Order'],
    'port_discharge':['Invoice','Packing List','Contract','Delivery Order'],
    'shipper_address':['Arrival Notice','Delivery Order'],
    'consignee_address':['Arrival Notice','Delivery Order'],
    'place_delivery':['Arrival Notice','Delivery Order'],
}.items():
    FIELDS[field]['documents'] = list(dict.fromkeys([*FIELDS[field]['documents'],*kinds]))
for spec in FIELDS.values():
    if any(kind in spec['documents'] for kind in ['Invoice', 'Packing List']):
        spec['documents'] = [*spec['documents'], 'Invoice & Packing List']
# These roles and references also occur on carrier delivery notices/orders.
for field in ['shipper','consignee','notify_party','vessel','voyage','packages','gross_weight','volume']:
    for kind in ['Arrival Notice','Delivery Order']:
        if kind not in FIELDS[field]['documents']:
            FIELDS[field]['documents'] = [*FIELDS[field]['documents'], kind]
FIELDS['do_number']['aliases'] += ['ma nhan container (so lenh)', 'mã nhận container (số lệnh)']
LEGAL=[s[0] for s in SPECS if s[5] in ['C','D']]

# Commercial document review. Booking describes a plan, not proof of loading or clearance.
for key, label, aliases, value_type, kinds in [
    ('packing_date','Ngày Packing List',['packing list date','packing date'],'date',['Packing List']),
    ('booking_date','Ngày booking',['booking date','booking confirmation date','ngày booking'],'date',['Booking']),
    ('carrier','Hãng tàu / đơn vị xác nhận booking',['carrier','shipping line','ocean carrier'],'text',['Booking','B/L','Sea Waybill']),
    ('etd','Ngày đi dự kiến (ETD)',['etd','estimated time of departure','estimated departure date'],'date',['Booking','B/L','Sea Waybill']),
    ('cut_off','Thời hạn cut-off ghi trên booking',['cargo cut-off','cargo cut off','cy cut-off','cy cut off','cut-off'],'text',['Booking']),
    ('contract_date','Ngày hợp đồng / thỏa thuận',['contract date','sales contract date','agreement date','ngày hợp đồng'],'date',['Contract']),
    ('contract_total','Tổng trị giá hợp đồng',['contract total','total contract value','contract amount'],'number',['Contract']),
    ('po_date','Ngày đơn đặt hàng',['po date','purchase order date'],'date',['Purchase Order']),
]:
    FIELDS[key]={'id':key,'label':label,'aliases':aliases,'type':value_type,'documents':kinds,'class':'A','level':'document','human_review':True,'sheet':'THONG_TIN_KHAI_BAO','official_mapping':'Nội bộ — kiểm tra theo chứng từ nguồn'}
for key in ['booking','shipper','consignee','notify_party','vessel','voyage','port_loading','port_discharge','place_receipt','place_delivery','eta','packages','gross_weight','volume','cargo_description','shipper_address','consignee_address','freight_terms']:
    FIELDS[key]['documents']=list(dict.fromkeys([*FIELDS[key]['documents'],'Booking']))
for key in ['currency','goods_quantity','net_weight','gross_weight','packages','cargo_description','seller_address','buyer_address','incoterms','payment_terms','origin']:
    FIELDS[key]['documents']=list(dict.fromkeys([*FIELDS[key]['documents'],'Contract','Purchase Order']))
for key in ['goods_quantity','packages','gross_weight','net_weight','cargo_description']:
    FIELDS[key]['documents']=list(dict.fromkeys([*FIELDS[key]['documents'],'C/O']))
FIELDS['booking']['aliases']+=['booking number','booking confirmation no','booking ref','số booking']
FIELDS['contract_number']['aliases']+=['sale contract no','contract number','agreement no','agreement number','số hợp đồng','hợp đồng số']
FIELDS['contract_date']['aliases']+=['sale contract date']
FIELDS['currency']['label']='Đồng tiền'
FIELDS['currency']['aliases']+=['contract currency']
FIELDS['co_number']['aliases']+=['certificate number','certificate no','reference no']
FIELDS['co_date']['aliases']+=['date of issue','certificate date']
FIELDS['po_number']['documents']+=['Invoice','Packing List','Contract']
FIELDS['po_number']['aliases']+=['po number','purchase order number','po reference','số đơn đặt hàng']
FIELDS['contract_number']['documents']+=['Purchase Order']

REVIEW_GROUPS=[
    {'type':'Packing List','label':'Packing List','required_fields':['packages','gross_weight'],'fields':['packing_number','packing_date','invoice_number','contract_number','po_number','shipper','consignee','goods_quantity','packages','gross_weight','net_weight','volume','shipping_marks']},
    {'type':'Booking','label':'Booking / Booking Confirmation','required_fields':['booking','port_loading','port_discharge'],'fields':['booking','booking_date','carrier','shipper','consignee','notify_party','vessel','voyage','port_loading','port_discharge','place_receipt','place_delivery','etd','eta','cut_off','cargo_description','packages','gross_weight','volume','freight_terms']},
    {'type':'Invoice','label':'Invoice','required_fields':['invoice_number','invoice_date','seller','buyer','currency','invoice_total'],'fields':['invoice_number','invoice_date','seller','seller_address','buyer','buyer_address','contract_number','po_number','currency','incoterms','payment_terms','goods_quantity','invoice_total','origin']},
    {'type':'Contract','label':'Hợp đồng / thỏa thuận mua bán / PO','required_fields':[],'fields':['contract_number','contract_date','po_number','po_date','seller','seller_address','buyer','buyer_address','currency','incoterms','payment_terms','goods_quantity','contract_total','origin']},
    {'type':'C/O','label':'C/O · nếu có','required_fields':['co_number','origin'],'fields':['co_number','co_form','co_date','co_issuer','exporter','exporter_address','importer','importer_address','consignee','invoice_number','origin','origin_criteria','cargo_description','goods_quantity','packages','gross_weight','net_weight']},
]
REVIEW_GROUPS.append({'type':'Arrival Notice','label':'Arrival Notice / Thông báo hàng đến','required_fields':['bl_number'],'fields':['bl_number','shipper','shipper_address','consignee','consignee_address','notify_party','vessel','voyage','port_loading','port_discharge','place_delivery','eta','arrival_date','packages','gross_weight','volume']})
FIELDS['packing_number']['label']='Số Packing List (nếu có)'
FIELDS['packing_number']['required']=False
FIELDS['eta']['aliases'] += ['est. arrival date','estimated arrival date','est arrival date']
REVIEW_FIELDS=list(dict.fromkeys(key for group in REVIEW_GROUPS for key in group['fields']))
PROFILE_TYPES=['Packing List','Booking','Invoice','C/O','Contract','Arrival Notice']
# Subtypes share a checklist group; they remain distinct when recognized from content.
PROFILE_VARIANTS=PROFILE_TYPES+['Purchase Order','Invoice & Packing List']
# Supporting documents participate in shipment consistency, not the six-type checklist.
SUPPORTING_TYPES=['Customs Declaration','Customs Release','Warehouse Receipt']
COMPARISON_TYPES=PROFILE_VARIANTS+SUPPORTING_TYPES
TYPES+=SUPPORTING_TYPES
DOCUMENT_LABELS.update({'Customs Declaration':'Tờ khai hải quan','Customs Release':'Danh sách hàng qua giám sát','Warehouse Receipt':'Phiếu / yêu cầu nhập kho'})
for key,label,aliases,value_type,kinds in [
    ('declaration_number','Số tờ khai',['số tờ khai','declaration no'],'text',SUPPORTING_TYPES[:2]),
    ('declared_weight','Tổng trọng lượng khai báo (chưa rõ gross/net)',['tổng trọng lượng hàng'],'weight',['Customs Release']),
    ('cargo_weight','Trọng lượng chưa ghi rõ gross/net',['trọng lượng','weight','cargo weight'],'weight',['Warehouse Receipt','Booking']),
    ('shipment_terms','Điều khoản giao hàng / giao từng phần',['shipment','partial shipment','delivery schedule','thời hạn giao hàng'],'text',['Contract','Purchase Order']),
]:
    FIELDS[key]={'id':key,'label':label,'aliases':aliases,'type':value_type,'documents':kinds,'class':'A','level':'document','human_review':True,'sheet':'THONG_TIN_KHAI_BAO','official_mapping':'Nội bộ — đối chiếu bằng chứng'}
REVIEW_FIELDS+=['declaration_number','declared_weight','cargo_weight','shipment_terms']
for key in ['gross_weight','net_weight','packages','goods_quantity','volume','booking','vessel','voyage','etd','invoice_number','seller','buyer','exporter','importer','cargo_description']:
    kinds=(['Customs Declaration'] if key in ['gross_weight','net_weight','goods_quantity','invoice_number','seller','buyer','exporter','importer'] else SUPPORTING_TYPES)
    FIELDS[key]['documents']=list(dict.fromkeys([*FIELDS[key]['documents'],*kinds]))
for key in ['booking','vessel','voyage','etd','eta','cargo_description']:
    FIELDS[key]['documents']=list(dict.fromkeys([*FIELDS[key]['documents'],'Invoice','Packing List','Invoice & Packing List']))
FIELDS['gross_weight']['aliases']+=['tổng trọng lượng hàng (gross)']
for spec in FIELDS.values():
    if any(k in spec['documents'] for k in ['Invoice','Packing List']):
        spec['documents']=list(dict.fromkeys([*spec['documents'],'Invoice & Packing List']))

def commercial_profile(requirements, mode='FCL'):
    return mode == 'FCL' and 'Booking' in requirements and 'Contract' in requirements

def default_requirements(mode='FCL'):
    if mode == 'FCL':
        return {
            'Packing List':{'required':True,'note':'Bộ kiểm tra nội bộ: phiếu đóng gói; nhận cả bản gộp Invoice & Packing List'},
            'Booking':{'required':True,'note':'Booking / Booking Confirmation; không thay bằng B/L, số liệu là kế hoạch đặt chỗ'},
            'Invoice':{'required':True,'note':'Bộ kiểm tra nội bộ: hóa đơn thương mại'},
            'Contract':{'required':True,'note':'Sales/Sale Contract, hợp đồng/thỏa thuận mua bán; chấp nhận Purchase Order có căn cứ'},
            'Arrival Notice':{'required':True,'note':'Thông báo hàng đến; số B/L tham chiếu không thay số Booking. Kiểm thông tin có trên bản gốc'},
            'C/O':{'required':False,'note':'Nếu khách cung cấp thì nhận diện và kiểm tra; thiếu C/O không chặn duyệt nội bộ'},
        }
    return {'Invoice':{'required':True,'note':'Checklist nghiệp vụ'},'Packing List':{'required':True,'note':'Checklist nghiệp vụ'},('AWB' if mode=='AIR' else 'B/L'):{'required':True,'note':'Sea Waybill có thể thay B/L'},'C/O':{'required':False,'note':'Nếu áp dụng chứng minh xuất xứ'},'Import Permit':{'required':False,'note':'Nếu mặt hàng phải có giấy phép'},'Inspection Certificate':{'required':False,'note':'Nếu thuộc kiểm tra chuyên ngành'}}
