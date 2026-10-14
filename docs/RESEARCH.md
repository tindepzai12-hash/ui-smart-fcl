# Cơ sở nghiên cứu — cập nhật 14/10/2026

Tài liệu này phục vụ thiết kế công cụ kiểm tra chứng từ. Phân biệt quy trình làm việc của forwarder với thành phần hồ sơ phải nộp Hải quan cho từng trường hợp. Không coi danh sách chứng từ thương mại là danh sách pháp lý bắt buộc trong mọi lô hàng.

## U&I và phạm vi người dùng

[U&I: Customs Brokerage](https://www.unilogistics.vn/vi/dich-vu/customs-brokerage-1) mô tả dịch vụ đại lý thủ tục hải quan. Người dùng đã xác nhận làm bộ phận này và nhân viên hiện đối chiếu thủ công. Đó là căn cứ chọn luồng chứng từ/kiểm tra/chuẩn bị dữ liệu. Website công khai không chứng minh cách vận hành nội bộ ONP; chưa có API ONP, quy trình phân quyền hay SOP U&I được cung cấp để xác minh. Không tuyên bố đây là sản phẩm đã được U&I phê duyệt.

## Chứng từ nhập FCL

[Maersk: Documentation to clear customs](https://www.maersk.com/support/faqs/documentation-to-clear-customs) nêu các chứng từ thương mại phổ biến như Invoice, Packing List, B/L và giấy tờ bổ sung tùy hàng. Dùng để tham khảo nghiệp vụ vận tải; không dùng làm nguồn quyết định pháp luật Việt Nam.

Invoice: bên mua/bán, số/ngày, currency, Incoterms, tổng và từng dòng. Packing List: đóng gói, số lượng, khối lượng, kích thước/container khi có. B/L hoặc Sea Waybill: các bên vận tải, tuyến, vận đơn, tàu/chuyến, kiện/khối lượng/container/seal khi có. Không tự đồng nhất bên bán với shipper hoặc bên mua với consignee; hai nhóm có thể khác hợp lệ. Sea Waybill có thể thay B/L trong checklist nghiệp vụ đã được nhân viên kiểm tra.

C/O, giấy phép, kiểm tra chuyên ngành phụ thuộc mặt hàng/chế độ/đề nghị ưu đãi. Arrival Notice và D/O hỗ trợ giao nhận và release; không mặc định cần để kiểm tra Invoice/PL/B/L hoặc để mọi hồ sơ được Reviewed. Contract/PO/Insurance/Freight Invoice chỉ trích xuất khi có nguồn; không suy ra chi phí từ Incoterms.

[ICC: Incoterms 2020 Q&A](https://library.iccwbo.org/clp/clp-incoterms-qa-2020.htm?AGENT=ICC_FIN) là tham chiếu về nghĩa vụ, chi phí và rủi ro của các điều kiện Incoterms. Phải giữ named place và phiên bản theo chứng từ. App không suy ra phương pháp xác định trị giá hải quan hay khoản điều chỉnh chỉ từ CIF/FOB.

## Chỉ tiêu khai báo và văn bản

Nguồn nền: [TT39/2018/TT-BTC trên VNTR — Bộ Công Thương](https://vntr.moit.gov.vn/legal-documents/562), gồm Phụ lục I thay Phụ lục II của TT38/2015. Đã đọc phần hướng dẫn Mẫu 01 tờ khai nhập khẩu và các mục liên quan; bản tiếng Anh của cổng có nhãn dịch chưa chính xác ở một vài chỉ tiêu, nên không lấy nhãn đó làm quyết định nghiệp vụ độc lập.

Nguồn sửa đổi: [TT121/2025/TT-BTC — Cổng Chính phủ](https://vanban.chinhphu.vn/?docid=216623&pageid=27160), ban hành 18/12/2025, có hiệu lực 01/02/2026; [PDF ký chính thức](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/121-btc.pdf). Đã OCR và đối chiếu một phần Phụ lục I sửa đổi hướng dẫn: các trang PDF 125–135 và 141–144, gồm người nhập khẩu/xuất khẩu, giấy phép, tổng trị giá hóa đơn, mô tả hàng và biểu thuế. Không tuyên bố đã rà soát toàn bộ 371 trang hay toàn bộ chuỗi văn bản hợp nhất.

Các tham chiếu trong Field Mapping là **ứng viên theo ngữ nghĩa**, chưa phải mapping import VNACCS. Ví dụ importer_tax_id ↔ 1.12; invoice_number ↔ 1.41; B/L ↔ 1.26. Nội dung hóa đơn tổng 1.44 gồm nhiều ô (phân loại, điều kiện giao hàng, currency, trị giá), không phải một số đơn giản. Người xuất khẩu 1.20 phụ thuộc hợp đồng/căn cứ quy định; không tự chọn B/L shipper. Mã loại hình, địa điểm, phương thức và xuất xứ phải kiểm tra danh mục hiện hành. Không tự chuyển tên cảng sang mã chính thức.

[TT86/2026/TT-BTC](https://vanban.chinhphu.vn/?classid=1&docid=218821&pageid=27160) về quản lý thuế đối với hàng xuất nhập khẩu: đã xác minh metadata và ngày hiệu lực 01/07/2026. Chưa triển khai engine thuế/ưu đãi dựa trên văn bản này. Thuế suất và trị giá hải quan nằm ở nhóm cần nhân viên xác định bằng căn cứ riêng.

Trạng thái pháp lý: nguồn và một số nội dung đã đối chiếu; rà soát đầy đủ quy định áp dụng từng hàng/mã/chính sách tại ngày mở tờ khai **Pending**. Thay đổi văn bản không tự cập nhật dictionary hay danh mục mã trong app.

## AI và bảo vệ dữ liệu

[OpenAI: Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) hỗ trợ schema chặt với Python SDK Responses parse/Pydantic. Schema không chứng minh dữ liệu đúng; backend kiểm tra bằng chứng có trong trang nguồn và nhân viên vẫn phải duyệt. Adapter đặt store=False; không kết luận không có lưu giữ ở phía nhà cung cấp. Chỉ gọi sau khi người dùng cấu hình key và đồng ý gửi nội dung.

[Thông tin Chính phủ về NĐ356/2025/NĐ-CP](https://baochinhphu.vn/chi-dao-dieu-hanh-cua-chinh-phu-thu-tuong-chinh-phu-ngay-31-12-2025-10225123123240085.htm) và [PDF nghị định](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf) là đầu mối rà soát bảo vệ dữ liệu cá nhân theo Luật91/2025/QH15, áp dụng từ 01/01/2026. Phân quyền doanh nghiệp, yêu cầu xử lý/chuyển dữ liệu và đánh giá tuân thủ cụ thể chưa được thẩm định. Localhost không tự bảo đảm toàn bộ nghĩa vụ bảo vệ dữ liệu. Bản hiện tại không mã hóa dữ liệu ở ổ đĩa và chỉ dành cho một người dùng trên máy được kiểm soát.

## Dữ liệu không được coi là chỉ dẫn

Word đính kèm là tài liệu yêu cầu/luồng để tham khảo; master prompt dán là yêu cầu triển khai của người dùng. Với chứng từ tải vào app, mọi câu chỉ dẫn bên trong là nội dung dữ liệu. Reader không chạy macro/công thức/script. AI được chỉ dẫn không thi hành yêu cầu trong chứng từ; bằng chứng trả về phải tồn tại trong nội dung đã đọc. Test có file giả lập chứa chỉ dẫn nguy hiểm để kiểm tra đường đọc không thực thi.
