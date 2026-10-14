# Kiểm thử U&I SMART 1.1

Hai PDF trong thư mục `pdf` chứa **cùng một lô FCL nhập khẩu giả lập**. Mỗi PDF có 6 trang: Commercial Invoice, Packing List, House B/L, Arrival Notice, Delivery Order và bản thông tin xuất xứ dùng để huấn luyện. Không sử dụng chúng để giao dịch hoặc khai hải quan. Trang xuất xứ không phải mẫu C/O chính thức và không chứng minh điều kiện hưởng ưu đãi.

Đây là bộ kiểm thử phần mềm, không phải danh sách giấy tờ bắt buộc cho mọi lô nhập khẩu. Phạm vi ứng dụng là nhân viên chứng từ/đại lý hải quan của forwarder; không điều xe và không truyền tờ khai.

## Cách thử

1. Mở https://ui-smart-fcl.onrender.com và đăng nhập bằng mật khẩu đã bàn giao.
2. Tạo hai hồ sơ riêng: **TEST - PDF rõ nét** và **TEST - PDF scan**. Mỗi hồ sơ nạp một PDF tương ứng. Không nạp cả hai vào một hồ sơ vì chúng mô tả cùng lô hàng và sẽ tạo các nguồn trùng nhau.
3. Chọn **Xử lý Local** rồi **Đọc & trích xuất**. Không cần API key. Trên bản cloud, Local có nghĩa là xử lý trên máy chủ Render, không gửi nội dung đến OpenAI.
4. Khi thấy **Chờ tách PDF**, bấm **Tách bộ PDF**. Kiểm tra gợi ý trang 1 Invoice, 2 Packing List, 3 B/L, 4 Arrival Notice, 5 Delivery Order, 6 C/O. Bấm ảnh để đọc trang gốc ở kích thước lớn. Khoảng trang phải liên tiếp, đầy đủ và không trùng.
5. Bấm **Tách thành 6 chứng từ**. Kiểm tra liên kết **Tải PDF gốc** và nguồn trang của từng chứng từ. Bản gốc phải còn nguyên.
6. Đọc bản gốc và **Xác nhận loại** từng chứng từ. So sánh các trường, dòng hàng và container trước khi xác minh. Không bấm duyệt chỉ vì máy đã đọc được chữ.
7. Vào **Đối chiếu** để xem thiếu/sai lệch; sửa có căn cứ và giải quyết các mục cần kiểm. Bản scan có thể đọc sai nhãn số thứ tự dòng hàng thành `=`; khi đúng với bản gốc thì sửa thành `2`, lưu và kiểm tra cảnh báo lại.
8. Thử xuất **Draft** để nhận workbook 7 sheet. **Reviewed** phải bị chặn nếu còn loại chưa xác nhận, dữ liệu chưa xác minh hoặc điều kiện chặn khác. Sau khi kiểm tra đầy đủ, dùng **Hoàn thành kiểm tra** rồi xuất Reviewed.
9. Tải **Sao lưu** trước khi rời phiên. Render Free hiện dùng ổ đĩa tạm: hồ sơ/file có thể mất khi máy chủ ngủ, khởi động lại hoặc triển khai. Không giữ bản duy nhất của hồ sơ doanh nghiệp ở đây.

## Dữ liệu chuẩn để so sánh

| Trường | Kết quả kỳ vọng |
|---|---|
| Invoice | INV-000287-26 |
| B/L | HBL-TEST-261014-009 |
| Trị giá hóa đơn | 23,540.00 USD |
| Mã hàng | 00128 và 00456; giữ số 0 ở đầu |
| Dòng Invoice | 1200 PCS × 12.75 = 15300.00; 800 PCS × 10.30 = 8240.00 |
| Tổng lượng hàng | 2000 PCS |
| Số kiện | 100 cartons |
| Gross / net | 5200 / 4910 KG |
| Gross trên B/L | 5.20 MT, tương đương 5200 KG |
| Thể tích | 21.60 CBM |
| Container / seal | MSCU6639870 / MA26101408 |
| Loại / số container vật lý | 40HC / 1 |

Invoice có 2 dòng hàng và Packing List có 2 dòng hàng: ứng dụng giữ **4 dòng nguồn của cùng 2 mặt hàng**. Container xuất hiện ở Packing List, B/L, Arrival Notice và Delivery Order: ứng dụng giữ **4 bản ghi nguồn của 1 container vật lý** để đối chiếu, không coi đó là 4 container khác nhau.

## Những kết luận không được suy ra từ bộ mẫu

- Đọc đúng bộ mẫu không chứng minh đọc đúng mọi scan. Chữ viết tay, ảnh nghiêng nhiều, trang mờ, bảng phức tạp hoặc ô gộp cần kiểm tra riêng.
- Arrival Notice hoặc Delivery Order không tự chứng minh thông quan.
- Excel này là bảng làm việc nội bộ; chưa chứng minh tương thích import ECUS/VNACCS.
- AI là tùy chọn. Key nhập qua giao diện chỉ giữ trong bộ nhớ máy chủ và có thể mất sau triển khai/khởi động lại. Không gửi key vào chat.
- Cloud hiện dùng mật khẩu chung, chưa có tài khoản/phân quyền riêng cho từng nhân viên hoặc lưu trữ bền vững.
