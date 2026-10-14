# U&I SMART — hồ sơ nhập khẩu FCL đường biển

Bản local một người dùng cho nhân viên chứng từ/đại lý hải quan của forwarder U&I. Giao diện, OCR, đối chiếu, chỉnh sửa và xuất Excel chạy thật. Khởi động và xử lý Local không cần OpenAI key. Đây là bản MVP đã kiểm thử bằng chứng từ giả lập; cần pilot với mẫu nghiệp vụ được phép sử dụng trước khi áp dụng hàng ngày.

## Mở trên máy hiện tại

Ứng dụng: **http://127.0.0.1:8765/**. Nếu đã dừng, nhấp đúp **Start U_I SMART.cmd**. Hoặc mở PowerShell trong thư mục dự án rồi chạy:

```powershell
.\start-local.ps1
```

Nếu PowerShell chặn script, chỉ cho phép trong cửa sổ đang dùng:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-local.ps1
```

Trên máy này đã có dependency Python, frontend build, Tesseract và ngôn ngữ tiếng Anh/Việt. Script khởi động thử tìm Python trong PATH, sau đó runtime Codex. Có thể chỉ định chính xác:

```powershell
.\start-local.ps1 -Python 'C:\Users\Windows\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
.\stop-local.ps1
```

Không mở `index.html` bằng file://. Frontend cần backend để lưu và đọc dữ liệu. Script chỉ chạy backend ẩn, bind 127.0.0.1; không triển khai cloud.

## Cài trên máy Windows khác

1. Giải nén cả dự án. Cài Python 3.11+ có pip; Node 20.19+ nếu cần build lại frontend.
2. Chạy `setup.ps1 -Python 'đường dẫn python.exe'`. Lần thiết lập đầu cần Internet để tải dependency và ngôn ngữ OCR. Nếu có `dist/`, không cần Node để chạy ứng dụng.
3. Cài Tesseract 5 bằng `winget install --id UB-Mannheim.TesseractOCR --exact`. Có thể đặt biến môi trường `TESSERACT_CMD` nếu executable ở vị trí khác. Xem trạng thái thật tại Cài đặt.
4. Chạy `start-local.ps1`. Sau khi chuẩn bị dependency, xử lý Local dùng tài nguyên trên máy; font và script không tải từ CDN.

Dependency Python nằm trong `vendor/`, tách khỏi Python toàn hệ thống. Có `package-lock.json` và requirements ghim phiên bản. Gói source bàn giao không bao gồm dependency đã cài hay dữ liệu khách hàng; chạy setup trên máy mới. Frontend build được kèm trong gói.

## Sử dụng tám bước

1. **Tạo hồ sơ:** Đặt tên, khách hàng. Phạm vi chính là nhân viên chứng từ/đại lý hải quan của forwarder.
2. **Nạp chứng từ:** Thêm file thật hoặc chọn Bộ mẫu chuẩn/Bộ mẫu sai lệch trong hồ sơ trống. Mẫu là dữ liệu giả lập.
3. **Đọc & nhận diện:** Chọn Local → Đọc & trích xuất; kiểm tra và xác nhận loại từng tệp. Chọn loại mới rồi xác nhận; dữ liệu liên quan cần kiểm tra lại. Giới hạn 25 MB/tệp, 100 trang/tệp, 30 tệp/lần.
4. **Xác minh trường:** Tìm trường/giá trị, lọc Chặn xuất/Cần kiểm/Đã duyệt, mở nguồn và đối chiếu. Lưu chỉnh sửa rồi xác minh từng bản ghi. Giá trị số/ngày mơ hồ phải làm rõ; Seller/Exporter/Shipper và Buyer/Importer/Consignee giữ vai trò riêng.
5. **Đối chiếu chéo:** Xử lý sai lệch/thiếu/cần kiểm theo nguồn và phạm vi. Ghi lý do không sửa đè nguồn hoặc thay bước đọc/phân loại.
6. **Chuẩn bị bảng kê:** Rà checklist theo lô; chứng từ không bắt buộc phải có lý do. Dữ liệu thiếu liên quan vẫn cần nhân viên xử lý. Container vật lý và bản ghi nguồn được đếm riêng.
7. **Kiểm tra xuất file:** Xem điều kiện chặn, bổ sung hoặc xác minh rồi Hoàn thành kiểm tra. Sửa dữ liệu sẽ hủy trạng thái Reviewed cũ.
8. **Xuất Excel:** Hai nút bản nháp/bản đã duyệt độc lập; bản nháp xuất được khi có dữ liệu, bản đã duyệt phải qua cổng kiểm tra. Workbook 7 sheet là hồ sơ nội bộ; mapping template scalar có nguồn truy vết.

Tám bước có thể bấm hoặc dùng bàn phím để mở vùng tương ứng. Dấu hoàn tất phản ánh dữ liệu hiện tại; xuất Draft không hoàn tất bước 8. Không có chức năng điều xe, gửi tờ khai thật hoặc tự xác định mã HS/thuế.

## OpenAI tùy chọn từ bước phân loại

Vào **Cài đặt → Kết nối OpenAI**, nhập key trong ô mật khẩu, chọn model rồi Lưu cấu hình. Key bị xóa khỏi ô sau khi lưu; chỉ backend giữ trong bộ nhớ phiên hoặc lấy từ biến `OPENAI_API_KEY`. Không ghi key vào SQLite, workbook, browser storage hay gói backup. Khởi động lại sẽ mất key nhập qua UI.

Kiểm tra kết nối chỉ đọc thông tin model; thành công không chứng minh model được phép dùng Structured Outputs cho chứng từ. Để xử lý AI: chọn OpenAI trong hồ sơ, chủ động đánh dấu đồng ý gửi nội dung rồi bắt đầu. Nội dung trang đã đọc/OCR sẽ gửi ra ngoài; file gốc không được upload trong adapter hiện tại. Đây là thao tác tùy chọn, có thể phát sinh phí API; không tự bật khi Local lỗi.

Kết quả AI cần schema và bằng chứng khớp trang nguồn; vẫn phải nhân viên xác minh. Có timeout/retry, cache và token usage thật; chưa có bảng giá để tính tiền. Tích hợp đã kiểm tra bằng phản hồi giả lập; **chưa gọi OpenAI thật** vì chưa có key được người dùng cấu hình/cho phép cho chứng từ. Không gửi key trong chat.

## Lưu trữ, sao lưu và khôi phục

`data/smart.sqlite`: hồ sơ, records, kiểm tra, lịch sử. `data/files/`: file gốc UUID; `data/exports/`: các XLSX; `data/templates/`: mẫu; `data/backups/`: ZIP. Dữ liệu ứng dụng không nằm trong localStorage. Chỉ backup mới bảo vệ trước mất máy/ổ đĩa.

Trong Cài đặt chọn tạo/tải backup. Khôi phục khi app đã dừng:

```powershell
.\stop-local.ps1
.\restore-local.ps1 -Archive 'C:\duong-dan\UI_SMART_backup_xxx.zip'
.\start-local.ps1
```

Restore kiểm tra ZIP/SQLite/schema/file trước, giữ thư mục dữ liệu trước restore để có thể quay lại. Không xóa các thư mục đó khi chưa xác nhận bản phục hồi đúng. Backup chứa chứng từ và cache kết quả AI, nên bảo quản như hồ sơ thương mại; hiện chưa mã hóa backup/database.

## Phát triển và kiểm thử

```powershell
$env:PYTHONPATH='vendor;.'
python -m pytest tests -q --basetemp=tmp/pytest-manual
node --test tests/frontend.test.mjs
node scripts/build.mjs
node tests/e2e.mjs
```

E2E cần app đang chạy và Microsoft Edge đã cài. Test chỉ tạo/xóa hồ sơ giả lập của chính nó; không dùng chứng từ thật. Nên chạy với dự án sao chép riêng nếu đang xử lý công việc. `scripts/build.mjs` tránh lỗi Windows cmd shim ở thư mục có ký tự `&`.

## Tài liệu bàn giao

- [Quyết định và audit prototype](docs/DECISIONS.md)
- [Nguồn nghiên cứu và ranh giới nghiệp vụ](docs/RESEARCH.md)
- [Field Mapping](docs/FIELD_MAPPING.md), bản đầy đủ [CSV](docs/FIELD_MAPPING.csv), [JSON](docs/FIELD_MAPPING.json)
- [Cấu trúc workbook](docs/WORKBOOK.md)
- [Kiến trúc và lưu trữ](docs/ARCHITECTURE.md)
- [Báo cáo QA](docs/QA_REPORT.md)
- [Hạn chế và Pending](docs/LIMITATIONS.md)

Không điều xe/nhập kho/truyền tờ khai. Không tự quyết định HS, thuế, trị giá hải quan hay tính hợp lệ C/O. Mẫu khai báo bên ngoài chỉ được gọi tương thích khi có mẫu thật và import thử thành công.
