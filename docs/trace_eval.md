# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*  
*Chủ đề: Đề tài 10 - Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá cho Đề tài 10                                                                                                                                                                                            |
| :--- |:----------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 🧠 **Multi-step Reasoning** |   `4/5`    | Cần phân tích yêu cầu (khu vực, mức giá, tiện ích) -> Tìm kiếm căn hộ -> Kiểm tra lịch chủ nhà -> Gợi ý thời gian đặt lịch xem nhà cho sinh viên.                                                                       |
| 🛠️ **Tool Interaction** |   `5/5`    | Bắt buộc phải tương tác với cơ sở dữ liệu/API thời gian thực: tra cứu danh sách nhà trọ (`search_apartments`), kiểm tra lịch trống (`check_landlord_schedule`), và thực hiện tạo lịch hẹn (`book_viewing_appointment`). |
| 🔀 **Dynamic Decision** |   `4/5`    | Nếu phòng mong muốn đã hết/đã cọc hoặc chủ nhà bận khung giờ yêu cầu, Agent phải tự động đưa ra phương án thay đổi (gợi ý phòng tương đương hoặc đề xuất khung giờ khả dụng khác).                                      |
| ⏳ **Long Horizon** |   `4/5`    | Quy trình kéo dài qua nhiều giai đoạn: từ tiếp nhận nhu cầu, lọc kết quả, đối chiếu điều kiện thực tế, xác nhận thông tin khách hàng đến khi đặt lịch thành công và xuất mã xác nhận.                                   |
| **TỔNG ĐIỂM FIT** | **17/20**  | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!**                                                                                                                                                                        |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3 - ĐỀ TÀI 10)

**Câu hỏi**: *"Tìm giúp tôi các phòng trọ hoặc căn hộ ở khu vực Cầu Giấy với ngân sách dưới 6 triệu/tháng."*

### 🤖 Chatbot Baseline (Cấp 2 - LLM thông thường):
🤖 Tôi rất vui được hỗ trợ bạn trong việc tìm nhà trọ hoặc căn hộ tại khu vực Cầu Giấy! Với ngân sách dưới 6 triệu/tháng, bạn có thể tham khảo một số gợi ý sau:

1. **Phong trọ truyền thống**: Thường có giá từ 1.5 triệu đến 4 triệu/tháng, tùy thuộc vào diện tích và tiện nghi.
2. **Căn hộ mini**: Giá thường dao động từ 3 triệu đến 6 triệu/tháng. Các căn hộ này thường có các tiện nghi như bếp riêng, máy lạnh.

### Một số lưu ý khi tìm phòng trọ/căn hộ:
- **Tiện nghi**: Kiểm tra xem có đầy đủ các tiện ích như nước nóng, Wi-Fi, máy giặt, bếp không.
- **Địa điểm**: Tìm phòng gần nơi làm việc hoặc trường học để tiết kiệm thời gian đi lại.
- **Hợp đồng**: Đọc kỹ hợp đồng thuê nhà, đặc biệt là các điều khoản về tiền cọc, thời gian thuê, và quyền lợi của hai bên.
- **Xem phòng trực tiếp**: Nên đến xem phòng trực tiếp để tránh tình trạng không như hình ảnh quảng cáo.

Bạn có thể tìm kiếm trên các trang web bất động sản hoặc các nhóm mạng xã hội để tìm các phòng trọ phù hợp. Nếu cần thêm thông tin cụ thể hơn, hãy cho tôi biết nhé!

---

### 🧠 ReAct Agent (Cấp 3 - ReAct Agent):
💬 [CHATBOT BASELINE] Tìm phòng trọ ở Cầu Giấy giá dưới 6 triệu, sau đó đặt lịch xem phòng NT01 vào 10:00 sáng ngày mai cho Phát (SĐT: 0987654321).
🤖 Chào bạn Phát!

Rất vui được hỗ trợ bạn trong việc tìm phòng trọ tại Cầu Giấy với mức giá dưới 6 triệu. Tuy nhiên, để đặt lịch xem phòng NT01, bạn cần liên hệ trực tiếp với chủ nhà hoặc môi giới của phòng đó để xác nhận thời gian và thông tin cụ thể.

Dưới đây là một số lưu ý khi bạn đi xem phòng trọ:
1. **Kiểm tra thực tế**: Hãy xem xét kỹ lưỡng tình trạng của phòng, các thiết bị và nội thất có hoạt động tốt không.
2. **Hợp đồng thuê**: Đảm bảo rằng bạn đọc kỹ hợp đồng trước khi ký, chú ý đến các điều khoản rõ ràng và công bằng.
3. **Chi phí phụ thêm**: Hãy hỏi chủ nhà về các khoản phí phát sinh như điện, nước, internet để có tổng chi phí chính xác.

Nếu bạn cần thêm thông tin về danh sách phòng trọ hay kinh nghiệm thuê nhà, hãy cho tôi biết nhé! Chúc bạn tìm được phòng trọ ưng ý!

--- ReAct ---

🤖 [REACT AGENT] Tìm phòng trọ ở Cầu Giấy giá dưới 6 triệu, sau đó đặt lịch xem phòng NT01 vào 10:00 sáng ngày mai cho Phát (SĐT: 0987654321).
🧰 Tools: search_apartments, book_viewing_appointment

--- Step 1/2 ---
🧠 Thought: cần tìm phòng phù hợp
🛠️ Action: search_apartments(Cầu Giấy, 6000000)
👁️ Tìm thấy 2 lựa chọn phù hợp tại 'Cầu Giấy' (Giá <= 6,000,000 VNĐ):
- Mã phòng: [NT01] | Căn hộ Studio Cầu Giấy - Địa chỉ: Số 12 Nguyễn Phong Sắc, Cầu Giấy, Hà Nội - Giá: 5,500,000 VNĐ/tháng (Còn trống)
- Mã phòng: [NT02] | Phòng trọ khép kín Cầu Giấy - Địa chỉ: Ngõ 155 Cầu Giấy, Hà Nội - Giá: 3,800,000 VNĐ/tháng (Còn trống)

--- Step 2/2 ---
🧠 Thought: cần đặt lịch xem phòng
🛠️ Action: book_viewing_appointment(NT01, 10:00 sáng ngày mai, Phát, 0987654321)
👁️ ✅ ĐẶT LỊCH THÀNH CÔNG!
- Mã phòng: NT01
- Khách hàng: Phát
- SĐT liên hệ: 0987654321
- Thời gian hẹn xem phòng: 10:00 sáng ngày mai
Nhân viên quản lý phòng sẽ gọi điện xác nhận lại với bạn trước 30 phút.
🏁 Hoàn tất

