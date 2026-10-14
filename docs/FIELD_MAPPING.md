# Field Mapping triển khai

Có 65 scalar field ID và 18 thuộc tính item/container. CSV/JSON chứa đầy đủ nghĩa, cấp, nguồn, ưu tiên, điều kiện cần, datatype/unit, chuẩn hóa, đối chiếu, human review, sheet và ứng viên chỉ tiêu.

A = raw trực tiếp; B = dẫn xuất/chuẩn hóa kiểm chứng được, giữ raw A; C = mã/danh mục cần tra; D = quyết định chuyên môn. Không suy diễn C/D từ tên hàng hoặc role vận tải.

Ưu tiên nguồn là hướng dẫn nhân viên đọc, không tự quyết định giá trị đúng. Seller khác Exporter/Shipper; Buyer khác Importer/Consignee. Goods quantity khác packages. Nước gửi hàng khác nước xuất xứ; origin text khác origin_code. ETA dự kiến phải kiểm tra trước dùng làm ngày khai. Trị giá invoice khác customs_value.

Tham chiếu Mẫu01 là ứng viên ngữ nghĩa từ TT39/2018 và một phần TT121/2025 đã đọc; không phải mapping API/import đã chứng nhận. Dictionary API vẫn đánh dấu official mapping Pending. Cần SOP, biểu mẫu đích và danh mục tại ngày khai để hoàn tất.

| ID | Tên / cấp | Nhóm | Nguồn | Ứng viên chỉ tiêu |
|---|---|---|---|---|
| invoice_number | Số hóa đơn | A | Invoice; Packing List; C/O; Contract; Purchase Order | 1.41 |
| invoice_date | Ngày hóa đơn | A | Invoice | 1.42 |
| seller | Người bán | A | Invoice; Contract; Purchase Order | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| buyer | Người mua | A | Invoice; Contract; Purchase Order | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| exporter | Người xuất khẩu | A | Invoice; C/O; Contract | 1.20 |
| importer | Người nhập khẩu | A | Invoice; C/O; Contract | 1.13 |
| shipper | Người gửi hàng | A | B/L; Sea Waybill; AWB; Packing List; Arrival Notice | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| consignee | Người nhận hàng | A | B/L; Sea Waybill; AWB; Packing List; Arrival Notice; C/O | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| notify_party | Bên được thông báo | A | B/L; Sea Waybill; Arrival Notice | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| importer_tax_id | Mã số thuế người nhập khẩu | C | Invoice; Contract | 1.12 |
| currency | Đồng tiền hóa đơn | A | Invoice; Freight Invoice | 1.44 (ô đồng tiền) |
| incoterms | Điều kiện Incoterms và địa điểm | A | Invoice; Contract | 1.44 (ô điều kiện giao hàng) |
| payment_terms | Điều khoản thanh toán | A | Invoice; Contract | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| invoice_total | Tổng trị giá hóa đơn | A | Invoice | 1.44 (ô tổng trị giá) |
| packing_number | Số Packing List | A | Packing List | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| bl_number | Số vận đơn biển | A | B/L; Sea Waybill; Packing List; Arrival Notice; Delivery Order | 1.26 |
| awb_number | Số vận đơn hàng không | A | AWB | 1.26 |
| booking | Số booking | A | B/L; Sea Waybill | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| vessel | Tên tàu | A | B/L; Sea Waybill; Arrival Notice | 1.31 (một phần thông tin tàu) |
| voyage | Số chuyến | A | B/L; Sea Waybill; Arrival Notice | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| port_loading | Cảng xếp hàng | A | B/L; Sea Waybill | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| port_discharge | Cảng dỡ hàng | A | B/L; Sea Waybill; Arrival Notice | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| airport_departure | Sân bay đi | A | AWB | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| airport_destination | Sân bay đến | A | AWB | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| flight | Chuyến bay | A | AWB | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| chargeable_weight | Trọng lượng tính cước | A | AWB | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| eta | Ngày đến dự kiến | A | Arrival Notice; B/L; Sea Waybill | 1.32 (kiểm tra ngày khai thực tế) |
| packages | Số kiện và loại bao bì | A | Packing List; B/L; Sea Waybill; AWB | 1.27 |
| goods_quantity | Tổng số lượng hàng | A | Invoice; Packing List | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| gross_weight | Trọng lượng cả bì | A | Packing List; B/L; Sea Waybill; AWB | 1.28 |
| net_weight | Trọng lượng tịnh | A | Packing List; Invoice | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| volume | Thể tích | A | Packing List; B/L; Sea Waybill | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| shipping_marks | Ký mã hiệu | A | Packing List; B/L; Sea Waybill | 1.30 |
| origin | Nước xuất xứ | A | Invoice; C/O | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| co_number | Số chứng nhận xuất xứ | A | C/O | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| co_form | Mẫu C/O | A | C/O | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| co_issuer | Cơ quan cấp C/O | A | C/O | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| co_date | Ngày cấp C/O | A | C/O | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| origin_criteria | Tiêu chí xuất xứ | A | C/O | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| freight_terms | Điều kiện cước | A | B/L; Sea Waybill | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| contract_number | Số hợp đồng | A | Contract | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| po_number | Số đơn đặt hàng | A | Purchase Order | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| do_number | Số lệnh giao hàng | A | Delivery Order | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| seller_address | Địa chỉ người bán | A | Invoice; Contract | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| buyer_address | Địa chỉ người mua | A | Invoice; Contract | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| exporter_address | Địa chỉ người xuất khẩu | A | Invoice; C/O; Contract | 1.22 |
| importer_address | Địa chỉ người nhập khẩu | A | Invoice; Contract | 1.15 |
| shipper_address | Địa chỉ người gửi hàng | A | B/L; Sea Waybill; AWB | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| consignee_address | Địa chỉ người nhận hàng | A | B/L; Sea Waybill; AWB | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| place_receipt | Nơi nhận hàng | A | B/L; Sea Waybill | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| place_delivery | Nơi giao hàng | A | B/L; Sea Waybill | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| cargo_description | Mô tả tổng lô vận tải | A | B/L; Sea Waybill; AWB | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| freight_amount | Phí vận tải ghi trên chứng từ | A | Freight Invoice; Invoice | 1.47 (số chứng từ chưa tự thành khoản trị giá) |
| insurance_amount | Trị giá bảo hiểm ghi trên chứng từ | A | Insurance | 1.48 (số chứng từ chưa tự thành khoản trị giá) |
| permit_number | Số giấy phép | A | Import Permit | 1.38 (một phần) |
| inspection_number | Số chứng nhận kiểm tra | A | Inspection Certificate; Phytosanitary Certificate | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| hs_code | Mã HS | D | Nhập tay với nguồn/căn cứ | 1.74 |
| declaration_type | Mã loại hình | C | Nhập tay với nguồn/căn cứ | 1.4 |
| customs_office | Mã đơn vị hải quan | C | Nhập tay với nguồn/căn cứ | 1.8 |
| storage_code | Mã địa điểm lưu kho | C | Nhập tay với nguồn/căn cứ | 1.29 |
| discharge_code | Mã địa điểm dỡ hàng | C | Nhập tay với nguồn/căn cứ | 1.33 |
| origin_code | Mã nước xuất xứ | C | Nhập tay với nguồn/căn cứ | 1.79 |
| transport_code | Mã phương thức vận chuyển | C | Nhập tay với nguồn/căn cứ | 1.6 |
| tax_rate | Thuế suất đã tra cứu | D | Nhập tay với nguồn/căn cứ | 1.76 (không bao gồm mọi sắc thuế) |
| customs_value | Trị giá hải quan đã xác định | D | Nhập tay với nguồn/căn cứ | Chưa ánh xạ trực tiếp; có thể không phải chỉ tiêu khai báo |
| item.line_number | line_number | A | Invoice/PL theo scope | Pending |
| item.product_code | Mã hàng | A | Invoice/PL theo scope | Pending |
| item.description | Mô tả hàng | A | Invoice/PL theo scope | 1.78 |
| item.quantity | Số lượng | A | Invoice/PL theo scope | Pending |
| item.unit | Đơn vị | A | Invoice/PL theo scope | Pending |
| item.unit_price | Đơn giá | A | Invoice/PL theo scope | Pending |
| item.line_amount | Thành tiền | A | Invoice/PL theo scope | Pending |
| item.currency | currency | A | Invoice/PL theo scope | Pending |
| item.origin | origin | A | Invoice/PL theo scope | 1.79 |
| item.hs_code | hs_code | D | Invoice/PL theo scope | 1.74 |
| item.scope | scope | A | Invoice/PL theo scope | Pending |
| container.container_number | Số container | A | PL/B/L/Sea Waybill | Pending |
| container.seal_number | Số seal | A | PL/B/L/Sea Waybill | Pending |
| container.container_type | Loại container | A | PL/B/L/Sea Waybill | Pending |
| container.packages | packages | A | PL/B/L/Sea Waybill | Pending |
| container.gross_weight | gross_weight | A | PL/B/L/Sea Waybill | Pending |
| container.cbm | cbm | A | PL/B/L/Sea Waybill | Pending |
| container.bl_number | bl_number | A | PL/B/L/Sea Waybill | Pending |

## Các lỗi cần tránh

- Không dùng Shipper của B/L để tự điền người xuất khẩu1.20 khi hợp đồng mô tả bên khác.
- Không chuyển buyer thành importer nếu chưa xác minh pháp nhân, mã số thuế và ủy thác.
- 1.44 có các ô khác nhau; không ghi nguyên CIF Cat Lai vào một ô mã Incoterms của mẫu đích.
- Không tự gộp nhiều invoice cùng B/L hay lấy tổng invoice làm thành tiền từng dòng.
- Hai container xuất hiện ở hai nguồn là hai container vật lý với bốn bản ghi nguồn.
- HS/thuế/trị giá không trích xuất tự động từ chứng từ vào trạng thái verified.
- Ngày slash và dấu ngăn số phải xác minh nguồn/locale.
