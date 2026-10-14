# Hướng dẫn sử dụng U&I SMART

Hướng dẫn cho nhân viên chứng từ của FWD xử lý hồ sơ nhập khẩu FCL đường biển. Làm lần lượt từ tải chứng từ đến kiểm tra nguồn và xuất bảng kê. AI hỗ trợ đọc, nhân viên xác minh cuối cùng.

## 1 Tạo hồ sơ và tải chứng từ

Mỗi lô hàng tạo một hồ sơ. Chọn nhiều tệp cùng lúc tại Thêm chứng từ. PDF nhiều loại chứng từ cần Đọc & trích xuất rồi Tách bộ PDF theo trang; kiểm tra phân nhóm trước khi xác nhận.

## 2 Chọn cách đọc

Local đọc lớp chữ và OCR trên máy chủ. AI hỗ trợ · OpenAI đọc thông tin OCR, có thêm phân nhóm ảnh và trích xuất AI. Chọn chế độ, đồng ý gửi dữ liệu nếu dùng OpenAI rồi bấm Đọc & trích xuất. Không thao tác sửa trong lúc đang đọc.

## 3 Kiểm tra loại chứng từ

Chọn tệp, xem tiêu đề/nội dung và loại máy nhận diện, rồi bấm Xác nhận loại. Nếu sai, đổi loại và xác nhận; chạy lại trích xuất khi đã đổi. Tên tệp không quyết định loại chứng từ.

## 4 Kiểm tra từng giá trị tại nguồn

Bấm Bắt đầu kiểm tra hoặc Xem nguồn. Web mở đúng tệp/trang và khoanh chữ khớp với dữ liệu máy đọc. Khung cam là chữ OCR có điểm nhận dạng thấp; chưa chắc là sai. Nếu có nhiều vị trí hoặc chưa định vị được, kiểm tra toàn trang và Câu trích dẫn; hệ thống không đoán vị trí.

## 5 Sửa và xác minh

Chọn Sửa giá trị ngay trong khung nguồn, sửa rồi bấm Lưu sửa; hoặc bấm Đúng, xác minh & tiếp để lưu và duyệt giá trị vừa sửa. Với hàng hóa/container, dùng hộp Kiểm tra / sửa. Ô trường bên phải cũng tự lưu khi rời ô. Để sau, mục tiếp bỏ qua mục hiện tại mà không duyệt, nhưng cần lưu bản sửa trước khi chuyển. Chờ xác minh không đồng nghĩa số liệu sai.

## 6 Xử lý lệch và thiếu

Mở Đối chiếu để xem nguồn gây lệch. Thiếu nghĩa chưa có dữ liệu/chứng từ phù hợp; bổ sung căn cứ hoặc điều chỉnh Checklist khi có lý do nghiệp vụ. Không điền số đoán để vượt kiểm tra. GW khác NW; 5,20 MT bằng 5.200 KG; số tiền bảo hiểm có thể khác trị giá Invoice vì khác phạm vi.

## 7 Chuẩn bị và xuất Excel

Kiểm tra bảng kê, các điều kiện chặn và căn cứ nghiệp vụ. Draft dùng để kiểm tra tạm. Reviewed chỉ dùng sau khi xác minh bản ghi, xử lý đối chiếu và Hoàn thành kiểm tra. Không bỏ cảnh báo chỉ để xuất file.

## 8 Ảnh hiện trường thuộc bộ riêng

Container, seal, hàng hóa, màn hình tra cứu/chat tải vào Ảnh hiện trường & màn hình; không tham gia đối chiếu hay bảng kê. Ảnh chụp giấy Invoice/PL/B/L vẫn là chứng từ. OpenAI có thể chuyển ảnh JPG/PNG/TIFF rõ nội dung sang bộ riêng; PDF ảnh hiện trường và chế độ Local cần tự chuyển.

## Ảnh mờ hoặc OCR đọc sai chữ/số

Phóng to bản gốc, kiểm tra chữ khoanh cam và nhãn kế bên. Dùng bản scan rõ hơn, đủ mép giấy, đúng chiều. Phóng to ảnh nhỏ không khôi phục được chi tiết đã mất.

## Xem nguồn chưa khoanh được vị trí

Xem Câu trích dẫn và Chữ OCR / PDF, đối chiếu toàn trang. Tệp Word/Excel/TXT dùng nguồn văn bản, không hứa vị trí trên trang in. Dữ liệu nhập tay cần bổ sung căn cứ.

## Khóa API / kết nối AI

Kiểm tra Cài đặt → kiểm tra kết nối. Không gửi key trong chat. Key đặt trong Environment của Render được giữ qua lần triển khai; key nhập theo phiên có thể mất khi khởi động.

## Render ngủ hoặc dữ liệu tạm mất

Chờ máy chủ khởi động rồi thử lại. Vào Cài đặt để sao lưu trước khi rời phiên; Render Free có thể mất hồ sơ khi khởi động lại/cập nhật.

