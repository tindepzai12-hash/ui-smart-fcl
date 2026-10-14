# Kiến trúc / dữ liệu

React19 + TypeScript + Vite; Lucide; Inter tiếng Việt/Latin đóng gói local. FastAPI phục vụ API và dist cùng origin. SQLite qua sqlite3 với foreign key, WAL, transaction và version. Python modules chia reader/extraction/normalize/validation/AI/Excel/templates/database. Không dùng dịch vụ cloud để chạy Local.

## Schema và migration

Nguồn: `backend/migrations/001.sql`, version1. `schema_versions` ghi schema. Hiện chỉ có migration khởi tạo idempotent, chưa có migration nâng cấp từ prototype HTML hay tự động downgrade.

- cases: UUID, metadata, requirementsJSON, trạng thái, revision, thời điểm duyệt.
- documents: caseFK, file UUID, hash/size/type/status, xác minh loại, evidence/lỗi/phương pháp/thời gian. UNIQUE(case_id,hash) chặn trùng trong case.
- pages: nội dung từng trang, method/quality/tables; DOCX/XLSX dùng đơn vị logic, không khẳng định số trang in thật.
- records: kind field/item/container, document/page, raw/valueJSON, evidence, Pending/verified/rejected, note/method/version. Các dòng/container giữ riêng.
- revisions: before/after/reason; hoàn tác lần sửa gần nhất và đưa về pending.
- checks: key/result/severity/detailJSON/resolution. Thay đổi nguồn/chi tiết làm mất resolution cũ.
- exports: file/version/mode/type/case_revision. Tải lịch sử theo ID.
- templates: file/sheetheaderJSON/mappingJSON; internalDraft.
- audit: action/entity/actor/date/before/after/reason. Actor hiện là Nhân viên local, chưa danh tính xác thực.
- ai_cache/ai_usage: kết quả theo contenthash/model/schema, token thực hoặc null khi lỗi. Có dữ liệu thương mại, không có key.

Các đường dẫn file đều app sinh, không chạy đường dẫn/script do chứng từ chỉ định. Jobs chạy thread trong process, status ở bộ nhớ; sau restart giữ file và báo hồ sơ Reading bị gián đoạn để thử lại. Không phục hồi tiến độ trang của job cũ. Một khóa mutation bảo vệ công việc case đang chạy; record version chặn ghi đè khi hai editor giữ phiên cũ.

## Endpoint chính

`/api/health`, `/api/dictionary`, `/api/cases`; `/api/cases/{id}/documents`, `/process`, `/records`, `/review`, `/export`, `/audit`; `/api/documents/{id}/pages`, preview, classification; `/api/records/{id}` edit, verify, undo; `/api/checks/{id}/resolve`; `/api/jobs/{id}` và cancel; `/api/ai/status|configure|test`; `/api/backup`, `/api/backups/{id}`; `/api/templates`, `/api/templates/{id}/export`. Schema validation từ Pydantic; có tài liệu FastAPI tại /docs khi chạy local.

PDFText → perpage OCR khi cần → nhãn/bảng → field dictionary → Decimal/unit → checks → nhân viên → Excel. OpenAI tùy chọn thay lớp phân loại/trích xuất, vẫn qua validator và review. Hạn mức AI90.000 ký tự một tài liệu, timeout60s, retry1. Cache không làm mất kiểm tra bằng chứng. Không có request tới AI khi Local hoặc chưa consent.

## Kiểm soát dữ liệu

Bind loopback; TrustedHost; mutation header X-UI-Smart:local và Origin cùng host; không CORS ngoài; CSP tài nguyên self; file size/page/image/officeZIP giới hạn; không chạy macro/công thức; formula injection neutralize trong Excel; key ở memory/env, API không trả lại. Không xem đây là ranh giới đủ trước phần mềm độc hại trên chính máy. Chưa login/RBAC, audit bất biến, mã hóa file/DB/backup, multiuser hoặc chứng nhận tuân thủ bảo vệ dữ liệu.

Backup dùng SQLite backup API rồi ZIP snapshot + files/exports/templates. Restore staging, kiểm tra integrity/version/file/đường dẫn, cập nhật path, đóng SQLite thật trước đổi thư mục trên Windows, giữ dữ liệu cũ. Không restore khi backend đang dùng cổng mặc định. Nếu đổi cổng bằng run.py, phải tự dừng process đó trước khi chạy restore (guard hiện kiểm tra8765).
