# Phạm vi tải chứng từ — cập nhật 15/10/2026

Theo yêu cầu người dùng, bỏ tab ảnh hiện trường/màn hình, chức năng tải ảnh riêng và chuyển chứng từ sang bộ ảnh. Chỉ có một nơi tải lên: Chứng từ, nhận cả PDF gốc, bản scan và ảnh chụp giấy tờ.

Giữ cơ chế backend loại ảnh không chứa chứng từ khỏi đối chiếu và Excel. Khi có tệp cũ hoặc ảnh bị AI loại, mục thu gọn “Tệp không tham gia đối chiếu” xuất hiện ngay trong Chứng từ, hiển thị lý do, cho tải bản gốc và chuyển về nếu nhận diện nhầm. Không xóa, không gộp dữ liệu ảnh vào bảng kê. Không có bộ tải ảnh riêng trên giao diện.

Chi tiết cơ chế backend trước thay đổi giao diện (các thao tác tải/chuyển bộ riêng không còn được cung cấp trên web):

# Phạm vi ảnh và chứng từ

- Chứng từ: PDF có text, PDF scan, ảnh chụp giấy hoặc screenshot đang hiển thị chứng từ thực tế. Phân loại theo nội dung, không theo tên/đuôi tệp.
- Bộ ảnh riêng: container, seal, hàng hóa, hiện trường hoặc màn hình portal/tra cứu/chat không hiển thị chứng từ. Không được tính vào checklist, records đang làm, đối chiếu, template mapping hoặc bảng kê Excel.
- Chọn nơi tải lên rõ ràng; tối đa 30 tệp/lần, 25 MB/tệp. Bộ ảnh nhận PDF/JPG/PNG/TIFF. Không tự gửi bộ ảnh riêng sang AI.
- OpenAI kiểm tra ảnh JPG/PNG/TIFF trong bộ Chứng từ bằng ảnh thu nhỏ trước OCR. Chỉ chuyển tự động khi nội dung rõ và mọi khung đều là ảnh tham khảo. Screenshot của PDF/Invoice vẫn là chứng từ. Tệp mơ hồ giữ nguyên bộ, chờ người dùng quyết định và không trích xuất tự động.
- PDF được phân tích bằng luồng đọc/tách hiện có; không có bước tự chuyển ảnh hiện trường nhúng trong PDF bằng vision. Người dùng cần chuyển bộ thủ công nếu tải PDF ảnh hiện trường nhầm vào Chứng từ.
- Local không có classifier thị giác, không hứa nhận diện ảnh hiện trường tự động. Có thể xem trước và chuyển bộ thủ công.
- Chuyển bộ giữ file và dữ liệu đã đọc; dữ liệu của ảnh được loại khỏi tập đang làm. Chuyển về Chứng từ đưa bản ghi về pending và yêu cầu xác nhận loại lại. Các thao tác đổi tập đang làm làm hết hiệu lực Reviewed.
- Thêm/xóa ảnh ở bộ riêng không làm thay đổi revision Reviewed của hồ sơ chứng từ; vẫn có audit riêng.
- Các kiểm thử vision dùng kết quả giả lập để kiểm tra routing/ranh giới; không phải benchmark độ chính xác AI thực tế.

Kiểm tra: 77 kiểm thử Python, 8 kiểm thử frontend, 4 kiểm thử gateway; TypeScript/Vite build. Kiểm tra browser desktop/mobile và tải ảnh vào gallery riêng.
