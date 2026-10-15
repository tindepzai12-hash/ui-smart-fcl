# Hướng dẫn nhân viên xử lý hồ sơ U&I SMART

Làm mẫu một hồ sơ nhập khẩu sầu riêng FCL: nhận chứng từ → đọc → xác minh → đối chiếu → bàn giao bảng kê.

Bạn là nhân viên chứng từ/đại lý hải quan của FWD, nhận và kiểm tra hồ sơ cho khách nhập khẩu. Web hỗ trợ chuẩn bị dữ liệu, không tự khai hải quan, cấp giấy kiểm dịch, lấy lệnh giao hàng hay điều xe.

## Hồ sơ mẫu: sầu riêng tươi nhập khẩu bằng container lạnh

Tình huống đào tạo GIẢ LẬP, không phải hồ sơ thật hay xác nhận lô hàng được phép nhập khẩu. Nhân viên phải kiểm tra điều kiện theo dạng hàng, xuất xứ và quy định hiện hành. Web không tự nạp bộ hồ sơ ví dụ này.

- **Khách / người bán:** MINH AN FRUIT DEMO / THAI FRUIT DEMO — tên giả lập
- **Hàng / tuyến minh họa:** Sầu riêng tươi Monthong; Laem Chabang, Thái Lan → Cát Lái, Việt Nam; 1 × 40RF (container lạnh)
- **Invoice / Packing List / B/L:** INV-DUR-DEMO-001 / PL-DUR-DEMO-001 / BL-DUR-DEMO-001
- **Số kiện / khối lượng:** 1.000 thùng; NW (tịnh) 18.000 kg; GW (cả bì hàng) 19.500 kg
- **Số lượng tính tiền / trị giá:** 18.000 kg × 4,50 USD/kg = 81.000 USD; CIF Cát Lái, Incoterms 2020; giả định không có dòng phụ phí/chiết khấu riêng
- **Container / seal:** CSQU3054383 / DURIAN-DEMO001 — dữ liệu minh họa, không theo dõi chuyến thật


## Bước 1. Nhận hồ sơ và lập danh sách còn thiếu

**Việc nhân viên làm:** Nhận yêu cầu dịch vụ/ủy quyền phù hợp, thông tin pháp nhân và chứng từ khách gửi. Hỏi hàng tươi hay đông lạnh, xuất xứ, mục đích nhập, ngày dự kiến đến và đầu mối bổ sung. Chưa đoán mã HS hoặc số liệu thiếu.

**Thao tác trên web:** Hồ sơ logistics → Tạo hồ sơ → đặt tên SAU-RIENG-DEMO-001, điền khách hàng và chọn Nhập khẩu FCL đường biển. Một lô hàng dùng một hồ sơ.

**Kiểm tra trong ví dụ sầu riêng:** Kiểm đếm Invoice, PL, B/L; nhận Contract, Arrival Notice, C/O nếu có/áp dụng. Nhờ đầu mối nghiệp vụ xác định hồ sơ kiểm dịch, ATTP và giấy phép nếu thuộc diện áp dụng. Phân biệt giấy nước xuất khẩu với đăng ký/kết quả tại Việt Nam; không phải tất cả giấy có ngay ngày đầu.

**Khi nào chuyển bước?:** Biết khách nào, hàng gì, đang có giấy gì, thiếu gì và phải hỏi ai; đã tạo đúng hồ sơ lô hàng.

**Nếu chưa đạt:** Thiếu Invoice/PL/B/L hoặc thông tin dạng hàng/xuất xứ: yêu cầu khách bổ sung. Chưa rõ điều kiện nhập: chuyển người phụ trách tra cứu. Liên hệ qua kênh làm việc của đơn vị; web không tự gửi email.



## Bước 2. Tải đúng chứng từ của cùng lô hàng

**Việc nhân viên làm:** Gom đúng phiên bản giấy tờ của cùng lô. Scan phải đủ trang, đủ mép và đọc được chữ; không trộn Invoice lô khác.

**Thao tác trên web:** Chứng từ → Thêm chứng từ → chọn nhiều file cùng lúc. PDF gộp nhiều loại: tải lên, đọc xong rồi Tách bộ PDF, kiểm tra nhóm trang và xác nhận. Hợp đồng nhiều trang giữ cùng nhóm, không tách máy móc mỗi trang thành một chứng từ.

**Kiểm tra trong ví dụ sầu riêng:** Invoice INV-DUR-DEMO-001; PL dẫn chiếu cùng Invoice; B/L đúng khách/lô. Tên 1.pdf không quyết định loại. PDF gốc, bản scan và ảnh chụp giấy Invoice/PL/B/L đều tải vào Chứng từ. Chỉ tải giấy tờ liên quan đến hồ sơ.

**Khi nào chuyển bước?:** Danh sách Chứng từ chứa đúng giấy tờ của lô; PDF gộp đã chia đúng nhóm trước khi đối chiếu.

**Nếu chưa đạt:** Thiếu trang/mờ: xin bản rõ. Nếu AI loại nhầm ảnh chụp giấy, mở Tệp không tham gia đối chiếu trong Chứng từ → tải bản gốc để kiểm tra → Chuyển về Chứng từ → xác nhận loại và đọc lại.



## Bước 3. Cho web đọc và xác nhận loại giấy

**Việc nhân viên làm:** Cho máy hỗ trợ đọc rồi tự xác nhận giấy gì bằng tiêu đề/nội dung. Đề xuất của máy không thay kiểm tra của nhân viên.

**Thao tác trên web:** Chọn Xử lý Local hoặc AI hỗ trợ · OpenAI; nếu dùng OpenAI thì đồng ý gửi dữ liệu → Đọc & trích xuất → chờ xong. Chọn từng tệp → xem loại → Xác nhận loại. Nếu đổi loại, xác nhận rồi chạy lại trích xuất.

**Kiểm tra trong ví dụ sầu riêng:** COMMERCIAL INVOICE → Invoice; PACKING LIST → Packing List; BILL OF LADING → B/L. Phytosanitary Certificate là giấy kiểm dịch thực vật; C/O là chứng nhận xuất xứ. Hai giấy không thay nhau. File gộp phải tách nhóm đúng trước.

**Khi nào chuyển bước?:** Tệp đọc xong, không còn lỗi đọc chưa xử lý và đã xác nhận đúng loại từng chứng từ.

**Nếu chưa đạt:** Đọc lỗi: thử lại hoặc thay scan rõ. AI chưa kết nối: kiểm tra Cài đặt, có thể dùng Local rồi kiểm nguồn. Chưa rõ loại giấy: hỏi người phụ trách, không chọn tùy ý để hết cảnh báo.



## Bước 4. Kiểm từng giá trị với giấy gốc

**Việc nhân viên làm:** Đọc số, đơn vị, nhãn và ngữ cảnh. Chờ xác minh nghĩa là chưa được người duyệt, không có nghĩa AI đã cố tình đọc sai.

**Thao tác trên web:** Bắt đầu kiểm tra hoặc Xem nguồn → xem đúng tệp/trang và chữ khoanh. Đúng: Đúng, xác minh & tiếp. Sai: Sửa giá trị → nhập theo bản gốc → Lưu sửa → xác minh; Đúng, xác minh & tiếp cũng lưu bản sửa trước khi chuyển. Hàng hóa/container dùng hộp Kiểm tra / sửa. Chưa đủ căn cứ: Để sau, mục tiếp.

**Kiểm tra trong ví dụ sầu riêng:** Invoice: 81.000 USD, 18.000 kg × 4,50 USD/kg. PL: 1.000 thùng, NW 18.000 kg, GW 19.500 kg. Kiểm cont CSQU3054383, seal DURIAN-DEMO001 theo nguồn có ghi. Giấy ghi 18,000.00 KGS nhưng giá trị làm việc 18000 KG: kiểm quy ước dấu số và đơn vị, không vội coi là lệch.

**Khi nào chuyển bước?:** Bản ghi được duyệt đều có căn cứ. Mục chưa chắc được để lại, không duyệt hàng loạt chỉ để giảm số đếm.

**Nếu chưa đạt:** Cam là OCR có điểm nhận chữ thấp, chưa khẳng định sai. Nhiều vùng khớp: đọc nhãn NW/GW, dòng kế bên. Không khoanh được: xem Chữ OCR / PDF, Câu trích dẫn và toàn trang. Sửa ô dữ liệu không sửa chứng từ gốc của khách.



## Bước 5. Xử lý số lệch giữa các giấy

**Việc nhân viên làm:** Phân biệt máy đọc sai, khác cách thể hiện và chính giấy tờ mâu thuẫn. Chỉ sửa kết quả máy khi bản gốc chứng minh được; không làm các số khớp giả tạo.

**Thao tác trên web:** Đối chiếu → mục lệch → Xem nguồn từng bên. OCR sai: sửa bản ghi và xác minh. Khác đơn vị/phạm vi: kiểm nhãn/căn cứ, Ghi lý do xử lý khi mục đó cho phép và có giải thích phù hợp. Bản gốc mâu thuẫn: yêu cầu khách/bên phát hành làm rõ, sửa giấy và cung cấp phiên bản đúng.

**Kiểm tra trong ví dụ sầu riêng:** NW 18.000 kg khác GW 19.500 kg là khác chỉ tiêu. B/L GW 19,5 MT bằng PL GW 19.500 kg nếu cùng phạm vi. B/L GW 19.800 kg khác PL GW 19.500 kg cho cùng lô thì phải làm rõ; không sửa 19.800 thành 19.500 để hết đỏ.

**Khi nào chuyển bước?:** Sai lệch đã sửa đúng nguồn hoặc có giải thích hợp lệ theo quyền/quy trình đơn vị; không bỏ qua mâu thuẫn thực tế.

**Nếu chưa đạt:** Chờ khách sửa giấy: giữ chưa hoàn tất, có thể xuất Draft trao đổi nội bộ. Không xác minh số mà bạn biết không khớp bản gốc.



## Bước 6. Chuẩn bị khai báo và kiểm tra điều kiện hàng sầu riêng

**Việc nhân viên làm:** Người có nghiệp vụ xác định HS, loại hình, mã địa điểm, thuế, trị giá hải quan và hồ sơ chuyên ngành. Ví dụ này không làm căn cứ pháp lý cho lô thật.

**Thao tác trên web:** Chuẩn bị khai báo → Nhập hoặc Bổ sung chỉ tiêu → ghi căn cứ. Điều chỉnh Checklist chỉ khi đã xác định yêu cầu thực tế và có lý do. Tải giấy kiểm dịch đúng loại Phytosanitary Certificate để xem/kiểm nội dung.

**Kiểm tra trong ví dụ sầu riêng:** Xác nhận dạng hàng tươi, xuất xứ và đối tượng nhập cụ thể. Đầu mối chuyên ngành xác định kiểm dịch/ATTP, giấy nước xuất khẩu, đăng ký/kết quả ở Việt Nam và giấy phép nếu áp dụng. Xin ưu đãi C/O phải kiểm điều kiện tương ứng. Web chưa có checklist kiểm dịch/ATTP riêng cho sầu riêng; nhân viên phải theo dõi phần này ngoài web.

**Khi nào chuyển bước?:** Chỉ tiêu có người chịu trách nhiệm và căn cứ; phần chuyên ngành được xác định, giao đầu mối, ghi rõ việc đang chờ trong hồ sơ công việc đơn vị.

**Nếu chưa đạt:** Chưa có căn cứ HS/thuế/kết quả chuyên ngành: chuyển người phụ trách, giữ việc thực tế ở trạng thái chờ. Không tắt Không bắt buộc chỉ để xuất Reviewed. Dấu xanh trên web không xác nhận sầu riêng được phép nhập.



## Bước 7. Xuất bảng kê và bàn giao đúng trạng thái

**Việc nhân viên làm:** Rà bảng kê với phiên bản giấy gốc cuối. Phân biệt nháp trao đổi với bản đã kiểm tra nội bộ; ghi rõ việc còn chờ khi bàn giao.

**Thao tác trên web:** Xuất Excel → xem điều kiện chặn/dữ liệu. Còn mục chưa kiểm: Xuất bản nháp (Draft). Đã xác nhận loại, xác minh bản ghi và xử lý các mục chặn: Hoàn thành kiểm tra → Xuất bản đã duyệt (Reviewed). Mở Excel rà lại rồi gửi qua kênh của đơn vị.

**Kiểm tra trong ví dụ sầu riêng:** Khách nhập, INV-DUR-DEMO-001, 81.000 USD, 1.000 thùng, GW/NW, cont/seal và chỉ tiêu tra cứu đúng bản cuối. Người phụ trách kiểm tra riêng tình trạng chuyên ngành bên ngoài theo phạm vi dịch vụ.

**Khi nào chuyển bước?:** Có bảng kê đúng trạng thái, nguồn giấy tương ứng và danh sách việc còn chờ để bàn giao. Reviewed chỉ nghĩa qua cổng kiểm tra dữ liệu nội bộ web, không nghĩa hải quan đã thông quan.

**Nếu chưa đạt:** Reviewed bị chặn: mở điều kiện chặn và xử lý từng mục. Sửa sau duyệt: xác minh lại bản mới, không dùng file cũ. Web không tự gửi Excel hoặc nộp tờ khai.



## Bước 8. Phối hợp sau bàn giao, không điều xe trong web

**Việc nhân viên làm:** Theo phạm vi hợp đồng, bàn giao đầu mối khai báo/kiểm dịch/giao nhận và theo dõi yêu cầu bổ sung. Xuất Excel chưa phải hoàn thành cả lô hàng.

**Thao tác trên web:** Lịch sử để rà lần sửa/xác minh. Có giấy/phiên bản mới: bổ sung đúng hồ sơ, đọc và kiểm lại phần thay đổi. Cài đặt → tải sao lưu nếu cần giữ hồ sơ qua lần máy chủ khởi động.

**Kiểm tra trong ví dụ sầu riêng:** Bàn giao đúng phiên bản, ghi kiểm dịch/ATTP còn chờ gì và ai theo dõi. Chỉ lưu giấy tờ liên quan đến hồ sơ; ảnh container hoặc màn hình tra cứu không thay giấy chứng nhận hoặc lệnh giao hàng.

**Khi nào chuyển bước?:** Người nhận biết phần đã kiểm và việc chưa hoàn tất. Điều xe, vận hành container lạnh và giao hàng do đầu mối vận tải/giao nhận làm qua công cụ/quy trình của họ.

**Nếu chưa đạt:** Giấy sửa sau bàn giao: báo người liên quan qua kênh đơn vị, thay/thu hồi bảng kê cũ theo quy trình. Web không tự cập nhật hải quan, hãng tàu, cảng hay vận tải.

## Ba tình huống để biết phải xử lý thế nào

### Máy đọc 81.000 USD thành 87.000 USD

Xem TOTAL trên Invoice gốc. Giấy là 81.000 USD thì sửa dữ liệu 81000 USD, lưu và xác minh. Đây là sửa trích xuất, không sửa hóa đơn của khách.

### PL NW 18.000 kg, B/L GW 19.500 kg

Không ép hai số bằng nhau. Tìm GW trên PL để so với GW B/L; giữ NW riêng. Chỉ so cùng đơn vị và cùng phạm vi.

### Thiếu kiểm dịch nhưng web không cảnh báo

Web chưa bao phủ hết chuyên ngành. Kiểm danh sách nghiệp vụ ngoài web và yêu cầu bổ sung đúng đầu mối. Reviewed không thay kết quả kiểm dịch hoặc quyết định thông quan.

## Phần việc thực hiện bên ngoài U&I SMART

- Xác định khả năng nhập theo dạng hàng/xuất xứ/mục đích và quy định hiện hành; tra HS, thuế và căn cứ áp dụng.
- Đăng ký, tiếp nhận kiểm tra và theo dõi kết quả kiểm dịch/ATTP, giấy phép nếu áp dụng qua cơ quan/hệ thống có thẩm quyền. Giấy nước xuất khẩu, giấy đăng ký và kết quả kiểm tra tại Việt Nam là các tài liệu khác nhau.
- Khai hải quan, thuế, phản hồi/thông quan trên hệ thống được phép; xử lý bản gốc, ủy quyền và bổ sung theo nghiệp vụ.
- Lệnh giao hàng, hãng tàu/cảng, điều xe và vận hành container lạnh do đầu mối được phân công làm. Cài đặt nhiệt độ theo chỉ dẫn hàng hóa/booking/thỏa thuận thực tế, không lấy từ ví dụ này.

Giới hạn hiện tại: chưa có mẫu/checklist chuyên ngành sầu riêng; không tự xác thực C/O, giấy kiểm dịch, điều kiện nhập hay trạng thái hệ thống ngoài. Bộ hồ sơ pháp lý đầy đủ do người có nghiệp vụ xác định; đây là hướng dẫn làm việc với dữ liệu.

Nguồn: [Cổng Dịch vụ công Quốc gia — kiểm dịch thực vật nhập khẩu và kiểm tra ATTP](https://vpcp.dichvucong.gov.vn/p/home/dvc-chi-tiet-thu-tuc-hanh-chinh.html?ma_thu_tuc=1.004038). Tham khảo 15/10/2026: phân biệt hồ sơ đăng ký, chứng nhận nước xuất khẩu, giấy phép khi áp dụng và kết quả kiểm tra. Tra lại quy định/cơ quan có thẩm quyền cho từng lô thật.

## Khi gặp vấn đề với web

### Không thấy hướng dẫn

Bấm Hướng dẫn sử dụng ở đầu trang. Mở từ hồ sơ đang làm thì Quay lại hồ sơ để tiếp tục. Bản tải về mở riêng và in/lưu PDF bằng trình duyệt.

### OCR chưa chắc hoặc không khoanh được

Phóng to bản gốc, xem Câu trích dẫn và Chữ OCR / PDF; xin bản rõ hơn nếu cần. Điểm OCR chỉ phản ánh nhận chữ, không xác nhận đúng nghiệp vụ.

### AI chưa kết nối

Cài đặt → kiểm tra kết nối. Có thể đọc Local rồi xác minh. Không gửi key trong chat; key Environment Render giữ qua triển khai, key theo phiên có thể mất.

### Render ngủ hoặc mất hồ sơ

Chờ máy chủ thức dậy. Render Free lưu tạm, có thể mất khi khởi động/cập nhật. Tải sao lưu trong Cài đặt nếu cần giữ hồ sơ; Excel không thay sao lưu toàn bộ hồ sơ.

