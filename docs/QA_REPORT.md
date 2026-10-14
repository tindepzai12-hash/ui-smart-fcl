# Báo cáo kiểm thử U&I SMART 1.1 — 14/10/2026

## Kết quả bàn giao hiện tại

- Bộ backend cuối cùng: **42 PASS** trong 24,21 giây, gồm hai kiểm thử PDF Packing List bị đặt tên Bill of Lading (text và scan).
- Build TypeScript/Vite: PASS; frontend 8 PASS, Node gateway 2 PASS. Không đổi giao diện sau lần build này.
- Bản Render 1.1: health 200, API chưa đăng nhập 401, đăng nhập 303, OCR eng/vie sẵn sàng. Hai bộ PDF 6 trang đều qua đọc, tách, giữ nguyên bản gốc, kiểm tra dòng hàng/container, chặn Reviewed chưa xác minh và xuất Draft 7 sheet. ZIP sao lưu qua kiểm tra toàn vẹn.
- Đã kiểm tra trực quan tách scan, chặn khoảng trang trùng, xác nhận loại và lưu trạng thái xác minh sau reload. Đã xem Packing List scan trên bản Render.
- Kết nối OpenAI thật được xác minh lại lúc 15:16 ngày 14/10/2026: HTTP 200, `gpt-4.1-mini`, phản hồi Structured Outputs hợp lệ, 58 input/6 output token. Giao diện đã hiện “Đã kiểm tra kết nối”. Key nhập qua giao diện có thể mất sau triển khai. Không gửi chứng từ đến OpenAI trong lượt bàn giao.
- Chi tiết phiên bản, dữ liệu chuẩn và giới hạn ở RELEASE_1_1.md; kết quả cũ dưới đây được giữ làm lịch sử, không thay thế kết quả bàn giao này.

## Lịch sử sửa bản Gemini

Chạy thực tế trên Windows, Python 3.12.14, Node 24.21 và Edge headless. Dữ liệu thử tách khỏi dữ liệu làm việc. Báo cáo này thay thế kết quả trong gói Gemini, không dùng kết quả cũ làm bằng chứng cho bản hiện tại.

## Kết quả

| Nhóm | Kết quả |
|---|---|
| TypeScript strict + Vite | `node scripts/build.mjs` — PASS |
| Backend | `python -m pytest tests -q --basetemp=tmp/pytest-openai-connect` — 30 PASS |
| Frontend helper + component React thật | `node --test tests/frontend.test.mjs` — 8 PASS |
| Edge E2E | Luồng FCL đầy đủ đã PASS trước lần chỉnh nút thu gọn/cấu hình OpenAI; bằng chứng trong `qa/e2e-report.json` |
| Kiểm tra UI lần bổ sung | Trên tab Codex: thu gọn/mở rộng đúng trạng thái; nút 28×28 cùng hàng logo; trang không tràn ngang |
| Responsive | 1440, 1366, 1180, 1179, 768, 390 px; không tràn ngang body |
| Trình duyệt | Không lỗi JavaScript; không yêu cầu ra ngoài origin local |

Bằng chứng: `qa/e2e-report.json`, `qa/screenshots/`, `qa/e2e-draft.xlsx`, `qa/e2e-reviewed.xlsx`, `qa/e2e-mapped.xlsx`.

## Các sửa chữa và xác minh

### Bổ sung nút thu gọn và kết nối OpenAI

- Nút thu gọn đặt cạnh logo, không chiếm một hàng trống; tên truy cập và hướng biểu tượng thay đổi theo trạng thái. Thanh icon vẫn có tên điều hướng cho trình đọc màn hình.
- Đã khôi phục backend local sau khi thấy cổng 8765 không phản hồi. Phiên mới chưa có key. Người dùng chọn nhập key sau; chưa thực hiện gọi OpenAI thật hoặc gửi hồ sơ.
- Kiểm tra OpenAI dùng một yêu cầu Responses có cấu trúc nhỏ (`status=ok`), tối đa 64 output token, không lưu response và không gửi chứng từ. Chỉ đánh dấu kết nối thành công khi nhận kết quả hợp lệ; ghi token thực nếu API phản hồi.
- Kiểm tra thất bại xóa trạng thái kết nối cũ. Lỗi key/quyền/model/hạn mức được dịch tiếng Việt và không trả raw exception chứa secret.
- Có trạng thái đang lưu/đang kết nối, khóa thao tác trùng; bấm Kiểm tra kết nối tự lưu key/model đang nhập trước khi thử. Key vẫn chỉ ở bộ nhớ phiên/biến môi trường.
- Sáu kiểm thử mới dùng SDK giả lập: Structured Responses thành công, lỗi 401/403/404/429, thiếu key/refusal. Kết quả này không thay thế xác minh key thật.
- Tài liệu triển khai: [OpenAI Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create).

### Bản FCL Gemini đã sửa trước đó

- Nhập source từ ZIP qua thư mục staging; giữ `data/`, dependency và công cụ local. Sao lưu source trước cập nhật ở thư mục `ui-smart-backups/` bên cạnh dự án.
- Bỏ nhánh build dự phòng phụ thuộc file không tồn tại/Babel hệ thống. Build thật luôn kiểm tra TypeScript rồi dùng Vite; thiếu dependency báo lỗi và yêu cầu `npm ci`. Kiểm thử component dùng React thật.
- Waiver dùng schema hiện có: `requirements[kind].required=false` và `note`, không tạo cột `waived/waiver_reason` mới. Lý do chỉ có khoảng trắng bị từ chối. Chỉ các trường thiếu phụ thuộc chứng từ được miễn mới chuyển sang Cần kiểm tra; vẫn cần nhân viên xử lý rõ ràng. Kiểm thử B/L miễn có lý do đi tới Reviewed và không miễn nhầm dữ liệu Invoice.
- `reading:`/`classification:` không resolve bằng ghi chú; trả HTTP 400 tiếng Việt. Mục Missing thực sự phải bổ sung/điều chỉnh checklist.
- Điều kiện chặn và quy tắc trong Excel dùng tên dễ đọc; UI dùng mã quy tắc nội bộ để điều hướng, không phân tích chuỗi kỹ thuật hiển thị.
- Đổi loại chứng từ đưa bản ghi đã xác minh/đã sửa còn giữ lại về Chờ xác minh; giữ giá trị và tăng version.
- Tám bước có nút HTML, tên truy cập và hỗ trợ Enter/Space. Step 8 chỉ hoàn tất khi xuất Reviewed đúng revision; xuất Draft không được đánh dấu hoàn tất.
- Thanh việc tiếp theo lấy số lượng thực. Không có trường hợp còn blocker nhưng báo đã Reviewed.
- Bộ mẫu chuẩn/sai lệch tải từ whitelist local; chỉ nạp vào hồ sơ trống, không tự đọc hoặc tự duyệt. Mẫu đều giả lập.
- Danh sách chứng từ có cách đọc, trạng thái và chọn/xác nhận loại. Không bịa điểm confidence.
- Tìm kiếm trường/giá trị, lọc Chặn xuất/Cần kiểm/Đã duyệt, nút Lưu chỉnh sửa và ghi lý do xử lý. Hiển thị trường thiếu có hành động nhập bổ sung; trường được miễn có thể ghi lý do trực tiếp.
- Tuần tự hóa lưu/xác minh trên cùng bản ghi. E2E trì hoãn PATCH 250 ms rồi bấm Xác minh ngay sau sửa: dùng version mới, không tự xung đột 409. Giá trị và trạng thái còn sau reload.
- Ba vùng làm việc độc lập từ 1180 px; dưới 1180 px xếp dọc. Nhãn container dài xuống dòng, sửa lỗi tràn ngang 390 px.
- Nhãn đơn vị nguồn đúng loại: Trang / Sheet / Khối Word / Khối văn bản; giữ evidence và giá trị gốc.
- Container được nhóm bằng số viết hoa, bỏ khoảng trắng; không tính số trống thành container vật lý. Tổng quan, bảng kê và Excel tách số vật lý và số bản ghi nguồn. So sánh seal/loại; trọng lượng riêng container chỉ so khi có nguồn và đơn vị rõ, không chia tổng trọng lượng lô cho container.
- Hai nút xuất Draft và Reviewed độc lập. Reviewed khóa và giải thích điều kiện; E2E xác minh cổng khóa, duyệt hồ sơ giả lập và tải bản Reviewed thật. Workbook có 7 sheet, mapping scalar nội bộ vẫn hoạt động.
- Lỗi mạng/validation hiển thị tiếng Việt, không đổ object validation thô ra UI.

## Phạm vi chưa chứng nhận

- Chưa có bộ chứng từ khách hàng được phép dùng để đo độ chính xác; mọi kiểm thử nghiệp vụ dùng dữ liệu giả lập.
- Tại thời điểm kiểm thử Gemini ban đầu chưa gọi OpenAI thật. Sau đó connection probe thật đã thành công; chưa đo trích xuất chứng từ khách hàng.
- Excel là bảng làm việc nội bộ; chưa kiểm chứng import ECUS/VNACCS.
- Chưa kiểm thử screen reader thật, Safari/Firefox hoặc mở file bằng Microsoft Excel desktop. Không suy ra các kiểm thử này từ Edge/openpyxl.
- Các giới hạn OCR, bảo mật nhiều người dùng và triển khai vận hành nằm trong `docs/LIMITATIONS.md`.
