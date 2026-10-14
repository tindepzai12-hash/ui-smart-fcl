# Trạng thái và Pending

## Đã triển khai, đã kiểm thử bằng dữ liệu giả lập

Ứng dụng local và lưu SQLite thật; nhiều file/case; PDF text/scan/ảnh và OCR Anh/Việt; Word/XLSX/TXT đọc thật; rules nhãn/header; dòng hàng và container độc lập; giữ vai trò bên/đơn vị; đối chiếu quy tắc; nguồn/trang/raw; chỉnh lưu/undo/xác minh; Draft/Reviewed có gate; XLSX7sheet; mapping scalar internal; audit/backup/restore; kết nối AI tùy chọn có schema/evidence checks; responsive/browser flow. Kết quả chi tiết ở QA_REPORT.md.

## Pending trước khi áp dụng rộng

| Hạng mục | Trạng thái / việc cần làm |
|---|---|
| Độ chính xác trên hồ sơ U&I | Chưa có mẫu thật được phép dùng/tập ground truth độc lập. Pilot theo từng layout/mặt hàng; không báo accuracy từ synthetic |
| OCR phức tạp | Chưa tự deskew/orientation, bbox, highlight vùng ảnh, xử lý bảng scan đa cột ổn định, handwriting. Có quality warning/sửa tay; ảnh xoay ở viewer không thay đổi OCR |
| Trích xuất layout tự do | Rules cần nhãn/header hỗ trợ, không suy diễn hàng bị thiếu; số có dấu phân cách mơ hồ bị chặn review. Ngày slash mơ hồ bị cảnh báo; cần kiểm tra nguồn rồi lưu YYYY-MM-DD |
| XML/EDI/e-invoice ký số | Chưa hỗ trợ; chỉ loại file trong reader hiện tại |
| Line matching và canonical source | Chưa ghép SKU giữa PL/Invoice theo mọi tình huống hoặc chọn bản ghi đại diện sau resolution. Giữ hàng theo nguồn, cảnh báo phạm vi; không auto merge |
| Review legal | Mã/thuế/trị giá cần nhập và căn cứ; chưa danh mục mã pháp lý phiên bản hóa hay thư viện hồ sơ mặt hàng |
| Chỉ tiêu chính thức | Có ứng viên mapping/source nghiên cứu; rà soát toàn bộ sửa đổi hiện hành và biểu mẫu chi tiết Pending |
| Workbook C / ECUS/VNACCS | Chưa có template thật và import thử. Không gọi template nội bộ là tương thích |
| Mapping nâng cao | Chưa export bảng lặp vào template, công thức/macro, tự nhận diện header; UI hiện mở lại mapping scalar đã lưu |
| AI thật | Chưa thử key/API thật; chỉ unit/schema/mock error. Model availability, billing, fidelity/refusal, timeout/retry thật cần key và consent |
| AI semantic layer | Chưa có giải thích xung đột/normalization bằng model độc lập; normalization/validation hiện deterministic. Cache/schema vẫn cần bump khi đổi dictionary |
| Bằng chứng AI | Kiểm tra literal evidence hỗ trợ chống bịa, chưa chứng minh kết luận semantic đúng; không auto verify |
| Đo chi phí | Token thật có nếu API phản hồi; không bịa estimated cost, chưa bảng giá theo model/thời điểm |
| Hiệu năng/sự cố | Chưa stress hồ sơ lớn, nhiều người dùng, power loss giữa file/DB mutation, ổ đĩa đầy, antivirus locks. Jobs không resume từng trang sau restart |
| Bảo mật doanh nghiệp | Chưa RBAC/login/identity, encryption, immutable audit, retention tự động, malware scanning, privacy impact assessment |
| Trình duyệt/Excel | Tested Edge desktop/responsive widths; chưa Safari/Firefox, screen reader thực hoặc mở workbook bằng Excel desktop/LibreOffice |
| Tích hợp ONP | Chưa API/SOP/quyền truy cập; module tích hợp không có số liệu/status giả |
| Packaging | Source + frontend build + scripts; chưa exe installer/code signing hoặc single-file portable OCR |

## Luồng được phép của MVP

Nhân viên đọc nguồn, sửa/xác minh và dùng Excel như bản làm việc. Reviewed chỉ thể hiện app đã qua các gate đã định nghĩa; không thay quy trình phê duyệt nội bộ, kiểm tra xuất xứ, xác định HS/thuế hay thông quan. Sau khi có mẫu doanh nghiệp và phần mềm đích, mở rộng từng mục cùng test nguồn đối chiếu.
