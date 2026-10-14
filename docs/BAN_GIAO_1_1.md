# Bàn giao U&I SMART 1.1

Ngày: 14/10/2026. Phạm vi: hồ sơ nhập khẩu FCL đường biển của nhân viên chứng từ/đại lý hải quan tại forwarder.

## Truy cập

- Web: https://ui-smart-fcl.onrender.com/
- GitHub riêng tư: https://github.com/tindepzai12-hash/ui-smart-fcl
- Bản local hiện có: http://127.0.0.1:8765/
- Mật khẩu cloud đã bàn giao riêng trong `U_I_SMART_Cloud_Access.txt` trên máy chủ dự án; không kèm trong gói source.

## Đã hoàn thành

Tiếp nhận file, đọc PDF text/OCR scan Anh-Việt, phân loại theo nội dung, tách bộ PDF theo trang với xác nhận người dùng, bảo toàn file gốc và nguồn trang, trích xuất trường/dòng hàng/container, chỉnh sửa và xác minh, đối chiếu, cổng duyệt, Excel 7 sheet, lịch sử, sao lưu/khôi phục và kết nối OpenAI tùy chọn.

Hai bộ mẫu cùng dữ liệu (6 chứng từ/bộ), một bộ có text và một bộ scan chỉ có ảnh. Đọc `HUONG_DAN_TEST.md` trước khi thử. Dữ liệu và C/O huấn luyện không có giá trị giao dịch/hải quan. 42 kiểm thử backend, 8 frontend, 2 gateway đã qua; hai bộ PDF đã thử trực tiếp trên Render. Chi tiết: `QA_REPORT.md` và `RELEASE_1_1.md`.

## Chạy bản được bàn giao

Gói ZIP có source, frontend build và bộ mẫu. Nó không chứa dữ liệu làm việc, key/mật khẩu, dependency Python, node_modules hoặc Tesseract executable.

1. Giải nén vào thư mục mới; không chép đè thư mục đang có dữ liệu.
2. Cài Python 3.11+ và Tesseract 5. Làm theo README để chạy `setup.ps1`; lần thiết lập đầu cần Internet. Gói đã có `dist/` nên không cần Node để khởi động bản local.
3. Chạy `Start U_I SMART.cmd` hoặc `start-local.ps1`. Nếu bản khác đã chạy tại cổng 8765, dừng bản đó trước khi muốn chạy bản vừa giải nén. Không chạy hai bản trỏ cùng database.
4. Vào Cài đặt kiểm tra OCR trước khi dùng scan. Local không cần OpenAI key.

## OpenAI

Đã kiểm tra kết nối thật lúc 15:16 ngày 14/10/2026 (Asia/Saigon): `gpt-4.1-mini` trả kết quả có cấu trúc hợp lệ, HTTP 200; giao diện xác nhận đã kết nối. Lượt thử không gửi chứng từ. Đây là xác minh kết nối, không phải đo độ chính xác trích xuất hồ sơ thực tế.

Trong web U&I SMART, chọn **Cài đặt → Kết nối OpenAI → API key → Lưu cấu hình → Kiểm tra kết nối**. Giữ model `gpt-4.1-mini` nếu project có quyền dùng. Không gửi key trong chat, GitHub hoặc ZIP. Connection probe chỉ gửi nội dung thử ngắn, không gửi chứng từ. Xử lý chứng từ bằng AI cần đồng ý riêng trong hồ sơ.

Key nhập qua web nằm trong bộ nhớ phiên. Để giữ cấu hình qua khởi động lại, chủ hệ thống có thể tự thêm `OPENAI_API_KEY` trong Render → dịch vụ ui-smart-fcl → Environment. Không đưa giá trị key vào source. Việc lưu môi trường có thể triển khai lại, làm mất file/SQLite tạm của Render Free; sao lưu trước.

## Lưu dữ liệu

Bản local lưu SQLite/file trên ổ đĩa người dùng. Tải sao lưu thường xuyên và thử khôi phục vào thư mục riêng. Trên Render Free, SQLite/file có thể mất khi ngủ, khởi động hoặc triển khai lại. Đây là giới hạn hạ tầng hiện tại; gói bàn giao không tạo dịch vụ trả phí.

Cloud dùng mật khẩu chung, chưa tài khoản/phân quyền từng nhân viên, lưu trữ bền vững hay sao lưu ngoài máy chủ tự động. Cần quyết định hạ tầng, ngân sách và quyền nhân viên trước khi dùng như hệ thống doanh nghiệp. Không gọi bản này là đã đạt các điều kiện vận hành đó.

## Ranh giới nghiệp vụ

Reviewed là trạng thái qua kiểm tra của ứng dụng, không chứng minh thông quan. Không điều xe, truyền tờ khai, quyết định HS/thuế hoặc tính hợp lệ C/O. Workbook là bảng làm việc nội bộ; chưa kiểm chứng import ECUS/VNACCS. Độ chính xác trên hồ sơ khách hàng, scan phức tạp hoặc viết tay cần pilot có nguồn đối chiếu.

## Thành phần trong ZIP

- `ui-smart/`: source, scripts, tài liệu, test, mẫu và frontend build.
- `BAT_DAU_TAI_DAY.md`: tài liệu này.
- `BO_CHUNG_TU_TEST/`: hai PDF và hướng dẫn thử.
- `QA/`: kết quả kiểm thử giả lập và ảnh xác nhận giao diện; không có backup/database.
- `MANIFEST_SHA256.json`: mã kiểm tra toàn vẹn cho từng file đóng gói.

Các tài liệu Gemini cũ được giữ trong source để tham khảo; trạng thái bàn giao hiện tại phải đọc tài liệu phiên bản 1.1 và QA mới.
