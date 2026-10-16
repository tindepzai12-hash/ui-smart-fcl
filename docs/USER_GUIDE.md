# Hướng dẫn nhân viên xử lý hồ sơ U&I SMART

4 bước: tải chứng từ cùng một lô → AI đọc & đối chiếu → xử lý sai lệch → xuất báo cáo.

Dành cho nhân viên chứng từ U&I/FWD. Không cần xác minh lần lượt mọi trường. Sáu nhóm chính vẫn là Packing List, Booking, Invoice, Hợp đồng/PO, Arrival Notice và C/O nếu có. Tờ khai, danh sách qua giám sát và phiếu nhập kho có thể làm nguồn đối chiếu bổ sung; tài liệu không liên quan vào Giấy tờ khác.

## Ví dụ thật: bộ HS XUAT SAI GW

Các chứng từ do người dùng cung cấp, cùng lô AB2507002. Đây là ví dụ xuất khẩu để kiểm thử sai lệch trọng lượng, không phải bộ nhập khẩu đầy đủ.

- **Packing List:** Gross 489.00 KG; net 391.20 KG; 56 cartons; 1200 PCS.
- **Tờ khai 307537505830:** Tổng trọng lượng hàng (Gross): 515,08 KGM.
- **Sai lệch cần xem:** Gross chênh 26,08 kg. Chưa thể quyết định giấy nào đúng chỉ từ số đông.
- **Phiếu nhập kho:** Weight 515.080 không ghi gross/net; giữ vai trò riêng, không dùng để tự sửa gross.


## Bước 1. Tải bộ chứng từ của cùng một lô

**Việc nhân viên làm:** Tạo một hồ sơ cho một lô; tải các PDF hoặc ảnh của lô đó.

**Thao tác trên web:** Tạo hồ sơ → Thêm chứng từ; có thể chọn nhiều tệp.

**Kiểm tra trong bộ ví dụ:** Bộ ví dụ gồm Packing List + Invoice, tờ khai, danh sách qua giám sát và phiếu nhập kho.

**Khi nào chuyển bước?:** Đủ các tệp khách thực tế gửi; tài liệu không liên quan được giữ riêng.

**Nếu chưa đạt:** Không lấy chứng từ lô khác để lấp mục thiếu. Hợp đồng nhiều trang được đọc liền một tệp, không phải tách từng trang. Chỉ tách PDF khi thật sự gộp nhiều chứng từ khác loại.



## Bước 2. Cho AI đọc và đối chiếu

**Việc nhân viên làm:** Chọn OpenAI và đồng ý gửi nội dung chứng từ cho yêu cầu này.

**Thao tác trên web:** Chứng từ → AI hỗ trợ · OpenAI → đồng ý gửi → Đọc & đối chiếu.

**Kiểm tra trong bộ ví dụ:** Máy đọc riêng gross 489.00 và gross 515,08, giữ đúng trang nguồn.

**Khi nào chuyển bước?:** Tác vụ hoàn tất; dữ liệu đọc rõ có nguồn tự được nhận và đưa vào Excel, kể cả chỉ có một nguồn. Tự chuyển sang Sai lệch & xử lý.

**Nếu chưa đạt:** Nếu lỗi key/kết nối, chưa coi AI đã kiểm xong. Local vẫn có đối chiếu số liệu đã đọc; thông báo phạm vi rõ trên màn hình.



## Bước 3. Mở lý do và xử lý chỗ sai lệch

**Việc nhân viên làm:** Ưu tiên Sai lệch số liệu, sau đó Cần làm rõ; không duyệt mọi trường.

**Thao tác trên web:** Sai lệch & xử lý → Xem lý do: bản gốc và vùng đánh dấu mở sẵn cạnh từng giá trị. Dùng +/− để zoom đến 400%, Kính lúp để soi chữ, Vùng đánh dấu để quay lại ô nguồn.

**Kiểm tra trong bộ ví dụ:** Xem đúng nhãn Gross trên PL và tờ khai. Không so gross với net 391.20 hoặc Weight chưa rõ vai trò.

**Khi nào chuyển bước?:** Tích Tôi đã đối chiếu các nguồn hiển thị → Xác nhận đã kiểm tra & lưu; không bắt buộc gõ ghi chú. Nếu ô bắt buộc chưa đọc được: nhập tay giá trị đúng từ bản gốc trước khi tích xác nhận; ô trống không được duyệt. Hai giấy gốc khác nhau vẫn giữ sai lệch và cần liên hệ khách khi cần sửa chứng từ.

**Nếu chưa đạt:** Sửa giá trị làm việc không sửa PDF gốc. Không đổi tất cả nguồn cho khớp. Sau sửa, nhận xét ngữ nghĩa AI sẽ báo cần chạy lại. Khác biệt hợp đồng/booking có thể do phạm vi, giao nhiều đợt hoặc kế hoạch thay đổi.



## Bước 4. Xuất báo cáo và bàn giao

**Việc nhân viên làm:** Xem Thiếu nguồn để bổ sung phần bắt buộc. Đã nhận gồm dữ liệu một nguồn, tự đi vào Excel và không yêu cầu kiểm lại.

**Thao tác trên web:** Xuất Excel → Tải báo cáo Excel.

**Kiểm tra trong bộ ví dụ:** Báo cáo vẫn giữ giá trị nguồn, lỗi, ghi chú và lịch sử trước/sau sửa.

**Khi nào chuyển bước?:** Có báo cáo để trao đổi với khách hoặc đồng nghiệp; không cần xác minh từng trường để xuất.

**Nếu chưa đạt:** Không có cảnh báo không chứng minh bộ chứng từ đầy đủ, hợp lệ pháp lý hoặc đã được hải quan chấp nhận.

## Các tình huống để biết phải xử lý thế nào

### Đơn giá theo CBM, số lượng theo PCS

Web giữ nguyên số lượng, đơn giá và thành tiền. Không nhân số PCS với đơn giá/CBM để kết luận hóa đơn sai. Nếu AI chưa đọc đủ dòng hàng, xử lý mục đọc nguồn trước; hệ thống không lấy tổng các dòng còn lại để báo sai tổng hóa đơn.

### Cần xử lý: AI chưa đủ bằng chứng

Bấm Xem lỗi đọc & bản gốc: vùng chữ cần kiểm được bôi xanh, có phóng to và kính lúp. Sửa ô Giá trị đã kiểm tra nếu AI đọc sai, tích đã kiểm tra rồi lưu; ghi chú không bắt buộc. Trường bắt buộc còn trống không thể duyệt. Nếu chữ biến dạng không định vị chính xác được, xem vùng nhãn hoặc yêu cầu bản rõ hơn; không tạo trích dẫn giả. Lần đọc cũ cần chạy lại OpenAI để dùng workflow mới.

### Hai nguồn giống nhau và số lượng 1,200 PCS

56 CT và 56 CTN cùng đơn vị carton; số tờ khai giống nhau xếp Khớp màu xanh lá. Dữ liệu một nguồn đọc rõ được nhận thẳng vào Excel. 19,560 KGS giống nhau ở hai nguồn không tạo yêu cầu kiểm tay chỉ vì dấu phẩy: giữ chuỗi gốc nếu chưa đủ căn cứ chuyển thành số Excel.

### Đã kiểm tra / ghi cách xử lý có nghĩa gì?

Đây là quyết định nhân viên đã lưu cùng căn cứ, thời điểm và phiên bản dữ liệu. Mở nhóm này để xem lại. Khác biệt 489 KG và 515,08 KG vẫn là Sai lệch dù đã ghi phương án xử lý; xác nhận không sửa chứng từ gốc. Nếu sửa dữ liệu hoặc đọc lại, cần xem kết quả đối chiếu mới.

### Hai Packing List cùng lô ghi gross khác nhau

Hiện Sai lệch với cả hai nguồn; bấm Xem lý do. Không tự chọn file mới hoặc số xuất hiện nhiều hơn.

### Hợp đồng cho nhiều lần giao, Invoice chỉ một lần

Hiện ở Sai lệch / khác phạm vi để xem điều khoản partial delivery; khác tổng hợp đồng và một Invoice chưa chứng minh giấy tờ sai. Không ép các giá trị bằng nhau.

### Chỉ có một nguồn hoặc chữ scan không rõ

Một nguồn đọc rõ: tự nhận vào Excel, không cần kiểm lại. Chữ scan quá mờ/biến dạng: Cần làm rõ, mở vùng xanh để nhập tay. Hai trạng thái này khác nhau.

## Phần việc thực hiện bên ngoài U&I SMART

- Trao đổi với khách để xác nhận sai lệch thực tế và xin chứng từ rõ/đúng phiên bản.
- Các thủ tục hải quan, giấy phép, kiểm tra chuyên ngành và giao nhận thực hiện theo quy trình riêng của đơn vị.

AI hỗ trợ đọc và gợi ý ngữ nghĩa. Đối chiếu số học dùng quy tắc và đơn vị rõ ràng. Nhân viên quyết định nguồn đúng; web không tự sửa giấy gốc hoặc tự nộp tờ khai.

Nguồn: [Phạm vi và thao tác U&I SMART](https://ui-smart-fcl.onrender.com/). Bộ dừa VinaTrain gồm 5 chứng từ công khai và Arrival Notice giả lập có ghi rõ nhãn, chỉ để kiểm thử. Bộ AB2507002 do người dùng cung cấp là chứng từ thật.

## Khi gặp vấn đề với web

### OpenAI chưa hoàn tất

Kiểm tra Cài đặt/Render và thông báo lỗi. Không xem kết quả Local như đã được OpenAI kiểm ngữ nghĩa.

### Không thấy ô được đánh dấu

Mở vùng nguồn; nếu nhiều vị trí khớp hoặc OCR không định vị được, kiểm nguyên trang và nhãn.

### Mất dữ liệu sau Render khởi động lại

Render Free lưu dữ liệu tạm. Xuất báo cáo hoặc backup trước khi máy chủ triển khai lại.

