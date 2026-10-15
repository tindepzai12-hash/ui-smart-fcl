# U&I SMART — hồ sơ nhập khẩu FCL đường biển

## Bản nâng cấp 1.1

Gói bàn giao: đọc [Bắt đầu tại đây](docs/BAN_GIAO_1_1.md), [Hướng dẫn thử hai PDF](docs/HUONG_DAN_TEST.md) và [QA hiện tại](docs/QA_REPORT.md). Bộ backend cuối cùng gồm 42 ca đã qua; không gửi key hoặc dữ liệu khách hàng cùng source.

Đã bổ sung tách bộ PDF nhiều chứng từ theo trang, giữ file gốc và truy vết nguồn; nâng cấp OCR bảng scan, sửa cảnh báo sau chỉnh dữ liệu và nối lại tác vụ khi mở hồ sơ. Hai PDF giả lập cùng dữ liệu có sẵn trong mục Chứng từ → Chứng từ để kiểm thử. [Hướng dẫn, dữ liệu kỳ vọng và kiểm thử 1.1](docs/RELEASE_1_1.md).

Bản nâng cấp chạy xử lý/lưu/xuất file thật. Render Free vẫn lưu tạm thời và dùng mật khẩu chung; chưa đủ để giữ hồ sơ doanh nghiệp lâu dài hay phân quyền nhân viên. 40 kiểm thử backend, 8 frontend, 2 gateway và build đã pass trên Windows bằng dữ liệu giả lập.

## Bản cloud dùng thử

Web: **https://ui-smart-fcl.onrender.com**. Repository riêng tư: **https://github.com/tindepzai12-hash/ui-smart-fcl**.

Triển khai Render **Free / Node 24 / Singapore**. Node quản lý web, đăng nhập và bộ xử lý Python trên loopback. OCR tiếng Anh/Việt hoạt động trên máy chủ. Mật khẩu truy cập được đặt bằng biến môi trường, không lưu trong Git. Mọi người có mật khẩu cùng truy cập một không gian dùng chung.

Chứng từ tải lên bản cloud được xử lý trên máy chủ Singapore. Chế độ “Local” ở đây nghĩa là không dùng OpenAI. Render Free xóa SQLite và file khi ngủ, khởi động lại hoặc triển khai lại; tải sao lưu trong Cài đặt trước khi rời phiên. Bản này dành cho demo và thử nghiệm. Dữ liệu thật trên máy local không được đưa lên repository hoặc máy chủ.

Kết nối OpenAI trong Cài đặt bằng key riêng của bạn. Key nhập tại web chỉ ở bộ nhớ phiên máy chủ; để giữ sau khởi động lại, đặt `OPENAI_API_KEY` trong Render Environment. Chi tiết: [hướng dẫn triển khai](docs/RENDER_DEPLOY.md).

## Bản local

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

## Checklist thương mại và năm bước sử dụng

5 nhóm: **Packing List, Booking, Invoice, Hợp đồng/Đơn đặt hàng, C/O (nếu có)**. Nhận diện riêng 6 loại: Packing List, Booking, Invoice, Contract, Purchase Order, C/O. Contract và PO giữ số/ngày, nguồn riêng; có một trong hai đáp ứng nhóm hợp đồng trong checklist nội bộ, không có nghĩa hai giấy tờ tương đương pháp lý. Không yêu cầu B/L, container, seal hoặc chỉ tiêu khai báo trong phạm vi này.

1. **Tải & nhận diện:** Tạo hồ sơ, chọn nhiều tệp cùng lúc. Dùng Local hoặc OpenAI với đồng ý gửi nội dung. Tách PDF nhiều chứng từ; kiểm và xác nhận loại theo nội dung. Bộ mẫu chuẩn/sai lệch là giả lập và chỉ nạp vào hồ sơ trống.
2. **Kiểm trường:** Xem nguồn từng trường/dòng hàng, sửa lỗi trích xuất có căn cứ, lưu và xác minh. Vai trò bên bán/mua/gửi/nhận giữ riêng.
3. **Đối chiếu:** Kiểm số tham chiếu, trường cùng vai trò/đơn vị/phạm vi và số học Invoice. Booking là kế hoạch, hợp đồng/PO có thể gồm nhiều đợt giao; khác số lượng không tự kết luận sai.
4. **Checklist:** Mở từng nhóm để xem trường cốt lõi, trường có ghi thì kiểm và nguồn. C/O thiếu không chặn; có cung cấp thì kiểm số/xuất xứ. Nhóm khác không yêu cầu trong tình huống cụ thể phải ghi lý do.
5. **Duyệt & xuất:** Xử lý điều kiện chặn rồi Hoàn thành kiểm tra. Excel 6 sheet có bản Draft/Reviewed và nguồn/lịch sử; sửa dữ liệu hủy Reviewed cũ. Reviewed chỉ là kiểm dữ liệu nội bộ.

Hướng dẫn nhân viên và ví dụ sầu riêng tại [huong-dan.html](https://ui-smart-fcl.onrender.com/huong-dan.html), sinh từ cùng nội dung với hướng dẫn trong ứng dụng. Giới hạn 25 MB/tệp, 100 trang/tệp, 30 tệp/lần. Tên file không quyết định loại chứng từ.

## OpenAI tùy chọn từ bước phân loại

Vào **Cài đặt → Kết nối OpenAI**, nhập key trong ô mật khẩu, chọn model rồi Lưu cấu hình. Key bị xóa khỏi ô sau khi lưu; chỉ backend giữ trong bộ nhớ phiên hoặc lấy từ biến `OPENAI_API_KEY`. Không ghi key vào SQLite, workbook, browser storage hay gói backup. Khởi động lại sẽ mất key nhập qua UI.

Kiểm tra kết nối gửi yêu cầu Structured Outputs nhỏ, không chứa chứng từ; thành công xác nhận truy cập model/schema, không đo độ chính xác trích xuất. Để xử lý AI: chọn OpenAI trong hồ sơ, chủ động đánh dấu đồng ý gửi nội dung rồi bắt đầu. Nội dung trang đã đọc/OCR sẽ gửi ra ngoài; file gốc không được upload trong adapter hiện tại. Đây là thao tác tùy chọn, có thể phát sinh phí API; không tự bật khi Local lỗi.

Kết quả AI cần schema và bằng chứng khớp trang nguồn; vẫn phải nhân viên xác minh. Có timeout/retry, cache và token usage thật; chưa có bảng giá để tính tiền. Kết nối thật với gpt-4.1-mini đã thành công ngày 14/10/2026 bằng key người dùng nhập trực tiếp; chưa đo trích xuất trên chứng từ khách hàng. Không gửi key trong chat.

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
