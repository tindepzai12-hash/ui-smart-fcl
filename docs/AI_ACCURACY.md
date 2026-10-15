# Cải thiện AI trích xuất chứng từ

## Quy tắc không suy diễn bắt buộc

[AI_NO_INFERENCE.md](AI_NO_INFERENCE.md) là chính sách bắt buộc được `backend/ai.py` đọc trực tiếp và chèn vào system instructions cho cả lượt đầu và lượt sửa. Cache bao gồm nội dung chính sách và loại đã được nhân viên xác nhận, nên đổi loại không dùng lại kết quả Other cũ.

MD không tự bảo đảm AI đúng. Backend tiếp tục kiểm bằng chứng từng giá trị/ô, nhãn nghiệp vụ, loại chứng từ và đơn vị; giá trị không qua kiểm tra bị loại, hiển thị cảnh báo và không được tự xác minh. Số lượng không được tự coi là trọng lượng tịnh. Kiểm thử có trường thiếu, tên tệp gây hiểu nhầm, chỉ dẫn độc hại và chọn nhầm loại thủ công.

Nếu máy chưa xác định loại, nhân viên kiểm bản gốc → chọn loại → Đưa vào bộ chính → chọn OpenAI và đồng ý gửi nội dung → Đọc tệp này. Tác vụ chỉ xử lý tệp vừa chọn. Loại thủ công là phạm vi trích xuất, không phải bằng chứng: nếu nguồn có tiêu đề mâu thuẫn hoặc thiếu nhãn nghiệp vụ hỗ trợ thì không được ép tạo trường dữ liệu. Tệp không có tiêu đề rõ nhưng có nhãn Invoice No/Booking No/... vẫn có thể trích xuất theo loại đã xác nhận.

Đây là cập nhật pipeline và prompt, chưa tạo model fine-tuned. Model hiện tại vẫn lấy từ cấu hình OpenAI của app.

`backend/ai_guidance.py` chứa ví dụ giả lập về bảng có ô rời, bằng chứng số dòng, tiền tệ và đơn vị. Các ví dụ không chứa giá trị đáp án của bộ PDF công khai dùng để đánh giá.

App kiểm tra kết quả bằng dictionary và bằng chứng trên trang. Nếu có dữ liệu bị loại hoặc một số trường quan trọng có dấu hiệu trong nguồn nhưng chưa được đọc, app yêu cầu một lượt đọc lại có giới hạn. Chỉ những giá trị vượt qua cùng bộ kiểm tra bằng chứng mới được bổ sung; một trường đã được chấp nhận không bị ghi đè. Dòng hàng được bổ sung ô thiếu chỉ khi các giá trị cũ cùng dòng vẫn khớp.

Lượt đọc lại không suy đoán ký tự 0/O, không tính lại số trên nguồn và không tự xác minh hồ sơ. Nếu lượt đọc lại thất bại, app giữ các bản ghi hợp lệ và báo cảnh báo; không cache lượt thất bại để lần sau còn có thể thử lại. Cache đã được đổi phiên bản để kết quả cũ không che bản sửa.

GPT-4.1 và GPT-4o dùng temperature 0 cho yêu cầu trích xuất để giảm biến thiên; đây không phải bảo đảm kết quả đúng hoặc hoàn toàn lặp lại. Các model khác giữ tham số mặc định tương thích.

Lượt đọc lại có thể thêm một yêu cầu AI cho mỗi chứng từ, kèm token usage thực tế. Không tự dùng model đắt hơn hoặc gửi thêm loại dữ liệu ngoài văn bản/OCR đã được người dùng đồng ý.

Muốn fine-tune sau này, cần bộ chứng từ được phép sử dụng, đáp án do nhân viên xác nhận và bộ kiểm thử riêng để tránh đánh giá trên chính dữ liệu huấn luyện. Hai phiên bản gốc/scan của cùng một hồ sơ không đại diện cho hai hồ sơ độc lập.

Nguồn đối chiếu: [OpenAI — Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create).


## Real-document regression safeguards

- Origin requires an explicit origin label with the country in the same evidence quote, at both document and item level. A seller address or loading port is insufficient.
- Packing List numbers require their own printed number label. Package counts and Invoice numbers cannot fill that field.
- Bounded re-reading may fill a missing unit from a printed quantity header without changing the accepted raw number.
- Party/address comparisons ignore punctuation, case and address labels but retain all word/number tokens. Contract port/Incoterms differences require scope review rather than automatic mismatch.
- Mass quantities are compared through explicit KG/MT/LB conversion with an explanatory check; raw values and source units are retained. Named-month date punctuation is normalized deterministically.
