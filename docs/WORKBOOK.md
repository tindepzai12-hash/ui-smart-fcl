# Workbook XLSX thực

Engine: openpyxl. A = bản làm việc nội bộ; B = chuẩn bị dữ liệu khai báo. Cấu trúc A/B hiện giống nhau, khác nhãn phạm vi; B không phải mẫu import của bất kỳ phần mềm khai báo nào.

| Sheet | Nội dung / cấp dữ liệu |
|---|---|
| TONG_QUAN_HO_SO | Case, khách hàng, mode, thời gian, Draft/Reviewed, phiên bản, cảnh báo và phạm vi |
| THONG_TIN_KHAI_BAO | Một dòng cho mỗi field × nguồn; tên, giá trị, đơn vị, source, trạng thái, phương pháp, ghi chú |
| CHI_TIET_HANG_HOA | Một dòng hàng × nguồn, giữ mã hàng, quantity/unit, unit_price, amount, currency, origin/HS nếu nhân viên nhập, trạng thái/trang/phạm vi |
| CONTAINER_VAN_CHUYEN | Container/seal/type/packages/weight/CBM/BL nếu có, nguồn, trạng thái/trang |
| DOI_CHIEU_CHUNG_TU | Quy tắc, nguồn/giá trị, kết quả, mức độ, lý do và ghi chú xử lý |
| THIEU_VA_CAN_XAC_MINH | Cảnh báo chưa xử lý và chỉ tiêu mã/thuế/trị giá chưa có, lý do và hướng xử lý |
| NGUON_VA_LICH_SU | Record gốc/hiện tại, trang, evidence, phương pháp, raw, ghi chú; audit trước/sau/người/thời gian |

Khác nguồn giữ thành các dòng riêng để không tự quyết định nguồn đúng. Hai container xuất hiện ở cả PL và B/L sẽ có bốn dòng nguồn, **không có nghĩa bốn container vật lý**. Dòng Invoice và dòng PL có scope riêng; người dùng phải kiểm tra trước khi dùng để khai báo/gộp. Không tạo bản canonical bằng confidence; phiên bản hiện tại chưa có màn hình chọn dữ liệu đại diện sau giải quyết xung đột.

Draft giữ dữ liệu chờ và cảnh báo. Reviewed chỉ xuất khi tất cả record hoạt động đã verified, tài liệu đã đọc và xác nhận phân loại, checklist và đối chiếu chặn đã được xử lý, nhân viên hoàn thành kiểm tra case. Sửa/tải thêm dữ liệu làm mất duyệt hiện tại; workbook đã xuất giữ nguyên phiên bản lịch sử. Verified là thao tác của người dùng, không phải kết luận pháp lý.

Số lượng/đơn giá/thành tiền đã verified ghi dạng số khi phân tích được và không quá độ chính xác 15 chữ số Excel; số chưa rõ hoặc chưa verified giữ text. Số chứng từ/mã hàng/HS/mã loại hình giữ text, bảo toàn zero đầu. Backend tính đối chiếu với Decimal. Unicode tiếng Việt được giữ trong TXT/Word/Excel; chất lượng Unicode từ PDF phụ thuộc text layer/OCR thật.

Chuỗi đầu `=`, `+`, `-`, `@` được trung hòa bằng dấu apostrophe, không có ô formula do chứng từ sinh ra. Freeze panes, filter, wrap, chiều rộng giới hạn và validation trạng thái được tạo thật. App mở lại XLSX để kiểm tra sheet và không có công thức. Chưa kiểm tra bằng Excel desktop/LibreOffice; không suy ra thành công import từ việc mở được bằng openpyxl.

## Mẫu Excel của người dùng

Màn Xuất Excel → Chọn template XLSX → xem sheet/header → Thêm ô mapping → chọn sheet, ô (B3...) và **bản ghi nguồn cụ thể** → Xuất. Giữ định dạng ô hiện có, ghi giá trị text và thêm UI_SMART_NGUON để truy vết. Mapping được lưu SQLite.

Chỉ hỗ trợ scalar field, tối đa 100 ô, file dữ liệu thuần không formula/macro; không ghi vào ô phụ merged, không trùng ô, không tham chiếu record hồ sơ khác. Chưa hỗ trợ lặp dòng hàng/container, nhận diện header tự động, mở lại mapping đã lưu trong UI hoặc chứng nhận template phần mềm bên ngoài. Backend có API liệt kê templates/mapping; UI hiện tạo phiên mapping mới.

`samples/internal-template.xlsx` là mẫu **nội bộ giả lập**; ô B3 dùng minh họa số hóa đơn. `qa/e2e-draft.xlsx` và `qa/e2e-mapped.xlsx` là file kết quả kiểm thử, không dùng khai báo thật.

`samples/workbook-A-synthetic.xlsx` và `samples/workbook-B-synthetic.xlsx` minh họa đủ bảy sheet bằng dữ liệu QA; cả hai là Draft, có sai lệch cố ý để minh họa, không phải chứng từ thương mại hay mẫu import.
