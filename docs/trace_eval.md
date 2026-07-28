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

**Câu hỏi**: *"Tôi muốn tìm phòng trọ ở khu vực Cầu Giấy giá dưới 5 triệu/tháng có điều hòa và đặt lịch xem phòng vào 15:00 chiều thứ 7 này."*

### 🤖 Chatbot Baseline (Cấp 2 - LLM thông thường):
* **Phản hồi**: *"Bạn có thể lên các trang web như Chợ Tốt, Batdongsan.com.vn hoặc các nhóm Facebook để tìm phòng trọ tại Cầu Giấy dưới 5 triệu có điều hòa. Sau khi chọn được phòng phù hợp, bạn hãy tự gọi điện cho chủ nhà để hẹn lịch xem vào 15:00 chiều thứ 7."*
* **Nhận xét**: Chatbot Baseline chỉ đưa ra lời khuyên chung chung từ kiến thức tĩnh có sẵn. Không tra cứu được dữ liệu phòng thực tế, không biết lịch trống của chủ nhà và không thể tự tương tác để thực hiện hành động đặt lịch xem nhà cho người dùng.

---

### 🧠 ReAct Agent (Cấp 3 - ReAct Agent):
* **Thought 1**: Người dùng cần tìm phòng trọ tại Cầu Giấy, ngân sách < 5 triệu/tháng, có điều hòa. Tôi cần gọi tool `search_apartments` để tìm danh sách các phòng khả dụng.
* **Action 1**: `search_apartments[district='Cầu Giấy', max_price=5000000, amenities='điều hòa']`
* **Observation 1**: `Tìm thấy 2 phòng phù hợp: 1. Phòng 302 ngõ 123 Cầu Giấy (4.5 triệu/tháng, ĐH, NL, ban công); 2. Phòng 101 ngõ 68 Xuân Thủy (4.8 triệu/tháng, ĐH, khép kín).`
* **Thought 2**: Phòng 302 ngõ 123 Cầu Giấy khớp với tiêu chí tốt nhất. Người dùng muốn xem phòng vào 15:00 chiều thứ 7 (01/08/2026). Tôi cần gọi tool `check_landlord_schedule` để xem chủ nhà phòng 302 có rảnh khung giờ này không.
* **Action 2**: `check_landlord_schedule[apartment_id='CG-302', date='2026-08-01']`
* **Observation 2**: `Chủ nhà rảnh các khung giờ: 14:00 - 16:00 và 17:00 - 18:30.`
* **Thought 3**: Khung giờ 15:00 rảnh. Tôi tiến hành gọi tool `book_viewing_appointment` để đặt lịch xem phòng cho người dùng.
* **Action 3**: `book_viewing_appointment[apartment_id='CG-302', date_time='2026-08-01 15:00', user_contact='0912345678']`
* **Observation 3**: `Đặt lịch thành công! Mã cuộc hẹn: BK-9921. Liên hệ chủ nhà: Anh Nam (0987654321).`
* **Thought 4**: Đã tìm thấy phòng trọ phù hợp và hoàn tất việc đặt lịch xem phòng. Tôi sẽ tổng hợp kết quả trả lời người dùng.
* **Final Answer**: *"Tôi đã tìm thấy phòng trọ phù hợp tại 302 ngõ 123 Cầu Giấy (giá 4.5 triệu/tháng, đầy đủ điều hòa) và đặt thành công lịch xem phòng cho bạn vào 15:00 chiều Thứ 7 (01/08/2026). Mã cuộc hẹn: BK-9921. SĐT chủ nhà (Anh Nam): 0987654321."*
* **Nhận xét**: ReAct Agent giải quyết trọn vẹn yêu cầu nhờ quy trình suy luận 4 bước (`Thought -> Action -> Observation`), tương tác linh hoạt với các công cụ tra cứu dữ liệu thời gian thực và thực hiện hành động đặt lịch tự động.
