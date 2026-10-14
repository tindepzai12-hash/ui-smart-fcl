# Cải thiện AI trích xuất chứng từ

Đây là cập nhật pipeline và prompt, chưa tạo model fine-tuned. Model hiện tại vẫn lấy từ cấu hình OpenAI của app.

`backend/ai_guidance.py` chứa ví dụ giả lập về bảng có ô rời, bằng chứng số dòng, tiền tệ và đơn vị. Các ví dụ không chứa giá trị đáp án của bộ PDF công khai dùng để đánh giá.

App kiểm tra kết quả bằng dictionary và bằng chứng trên trang. Nếu có dữ liệu bị loại hoặc một số trường quan trọng có dấu hiệu trong nguồn nhưng chưa được đọc, app yêu cầu một lượt đọc lại có giới hạn. Chỉ những giá trị vượt qua cùng bộ kiểm tra bằng chứng mới được bổ sung; một trường đã được chấp nhận không bị ghi đè. Dòng hàng được bổ sung ô thiếu chỉ khi các giá trị cũ cùng dòng vẫn khớp.

Lượt đọc lại không suy đoán ký tự 0/O, không tính lại số trên nguồn và không tự xác minh hồ sơ. Nếu lượt đọc lại thất bại, app giữ các bản ghi hợp lệ và báo cảnh báo; không cache lượt thất bại để lần sau còn có thể thử lại. Cache đã được đổi phiên bản để kết quả cũ không che bản sửa.

GPT-4.1 và GPT-4o dùng temperature 0 cho yêu cầu trích xuất để giảm biến thiên; đây không phải bảo đảm kết quả đúng hoặc hoàn toàn lặp lại. Các model khác giữ tham số mặc định tương thích.

Lượt đọc lại có thể thêm một yêu cầu AI cho mỗi chứng từ, kèm token usage thực tế. Không tự dùng model đắt hơn hoặc gửi thêm loại dữ liệu ngoài văn bản/OCR đã được người dùng đồng ý.

Muốn fine-tune sau này, cần bộ chứng từ được phép sử dụng, đáp án do nhân viên xác nhận và bộ kiểm thử riêng để tránh đánh giá trên chính dữ liệu huấn luyện. Hai phiên bản gốc/scan của cùng một hồ sơ không đại diện cho hai hồ sơ độc lập.

Nguồn đối chiếu: [OpenAI — Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create).
