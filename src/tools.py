"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
- Đề tài 10: Trợ Lý tìm & đặt lịch xem Nhà trọ
"""


def search_apartments(location: str, max_price: int = 10000000) -> str:
    """
    Tra cứu danh sách phòng trọ hoặc căn hộ cho thuê theo khu vực và mức giá tối đa.

    Args:
        location (str): Khu vực hoặc quận/huyện (Ví dụ: 'Cầu Giấy', 'Bình Thạnh', 'Quận 7')
        max_price (int): Mức giá thuê tối đa theo tháng (VNĐ), mặc định là 10,000,000 VNĐ

    Returns:
        str: Danh sách phòng khả dụng kèm mã phòng, địa chỉ, giá và trạng thái
    """
    try:
        if not isinstance(location, str) or not location.strip():
            return "LỖI: Cần cung cấp khu vực tìm phòng."
        loc_lower = location.lower()
        mock_database = [
            {"id": "NT01", "name": "Căn hộ Studio Cầu Giấy", "address": "Số 12 Nguyễn Phong Sắc, Cầu Giấy, Hà Nội", "price": 5500000, "area": "Cầu Giấy", "status": "Còn trống"},
            {"id": "NT02", "name": "Phòng trọ khép kín Cầu Giấy", "address": "Ngõ 155 Cầu Giấy, Hà Nội", "price": 3800000, "area": "Cầu Giấy", "status": "Còn trống"},
            {"id": "NT03", "name": "Căn hộ 1PN Bình Thạnh", "address": "Đường Điện Biên Phủ, Bình Thạnh, TP.HCM", "price": 4500000, "area": "Bình Thạnh", "status": "Còn trống"},
            {"id": "NT04", "name": "Căn hộ Mini Cao Cấp Quận 7", "address": "Đường Nguyễn Hữu Thọ, Quận 7, TP.HCM", "price": 7500000, "area": "Quận 7", "status": "Còn trống"},
        ]

        results = []
        for item in mock_database:
            if item["area"].lower() in loc_lower or loc_lower in item["area"].lower():
                if item["price"] <= max_price:
                    results.append(f"- Mã phòng: [{item['id']}] | {item['name']} - Địa chỉ: {item['address']} - Giá: {item['price']:,} VNĐ/tháng ({item['status']})")

        if results:
            return f"Tìm thấy {len(results)} lựa chọn phù hợp tại '{location}' (Giá <= {max_price:,} VNĐ):\n" + "\n".join(results)
        return f"LỖI: Không tìm thấy phòng trọ nào ở khu vực '{location}' với giá dưới {max_price:,} VNĐ."
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể tra cứu phòng trọ. Chi tiết: {str(e)}"


def book_viewing_appointment(room_id: str, date_time: str, customer_name: str, phone: str) -> str:
    """
    Đặt lịch hẹn xem phòng trọ / căn hộ cho thuê.

    Args:
        room_id (str): Mã phòng cần xem (Ví dụ: 'NT01', 'NT02')
        date_time (str): Ngày giờ xem phòng (Ví dụ: '10:00 sáng ngày mai')
        customer_name (str): Tên khách hàng (Ví dụ: 'Phát')
        phone (str): Số điện thoại liên hệ (Ví dụ: '0987654321')

    Returns:
        str: Kết quả xác nhận đặt lịch hẹn hoặc thông báo lỗi
    """
    try:
        if not room_id or not date_time or not customer_name or not phone:
            return "LỖI: Cần cung cấp đầy đủ thông tin đặt lịch (mã phòng, thời gian, tên khách và số điện thoại)."
        valid_rooms = ["NT01", "NT02", "NT03", "NT04"]

        if room_id.upper() not in valid_rooms:
            return f"LỖI THẤT BẠI: Mã phòng '{room_id}' không tồn tại trên hệ thống hoặc đã hết phòng."

        return (
            f"✅ ĐẶT LỊCH THÀNH CÔNG!\n"
            f"- Mã phòng: {room_id.upper()}\n"
            f"- Khách hàng: {customer_name}\n"
            f"- SĐT liên hệ: {phone}\n"
            f"- Thời gian hẹn xem phòng: {date_time}\n"
            f"Nhân viên quản lý phòng sẽ gọi điện xác nhận lại với bạn trước 30 phút."
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể đặt lịch xem phòng. Chi tiết: {str(e)}"


def check_landlord_schedule(room_id: str, date: str) -> str:
    """Kiểm tra các khung giờ chủ nhà còn trống cho một phòng trong ngày yêu cầu.

    Args:
        room_id: Mã phòng, ví dụ ``NT01``.
        date: Ngày cần kiểm tra, ví dụ ``ngày mai`` hoặc ``30/07/2026``.

    Returns:
        Chuỗi liệt kê các khung giờ trống, hoặc thông báo lỗi rõ ràng.

    Note:
        Dữ liệu lịch là giả lập cho mục đích demo. Bản thực tế cần truy vấn
        hệ thống lịch của chủ nhà.
    """
    try:
        if not isinstance(room_id, str) or not room_id.strip():
            return "LỖI: Cần cung cấp mã phòng để kiểm tra lịch chủ nhà."
        if not isinstance(date, str) or not date.strip():
            return "LỖI: Cần cung cấp ngày muốn xem phòng."

        schedules = {
            "NT01": ["09:00", "10:00", "15:00"],
            "NT02": ["08:30", "13:30", "16:30"],
            "NT03": ["09:30", "14:00", "17:00"],
            "NT04": ["10:30", "13:00", "16:00"],
        }
        normalized_room_id = room_id.upper().strip()
        if normalized_room_id not in schedules:
            return f"LỖI THẤT BẠI: Mã phòng '{normalized_room_id}' không tồn tại hoặc không thể kiểm tra lịch."

        return (
            f"Lịch trống của chủ nhà cho phòng {normalized_room_id} vào {date.strip()}: "
            f"{', '.join(schedules[normalized_room_id])}. "
            "Vui lòng chọn một khung giờ trên trước khi đặt lịch."
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể kiểm tra lịch chủ nhà. Chi tiết: {str(e)}"


AVAILABLE_TOOLS = {
    "search_apartments": search_apartments,
    "check_landlord_schedule": check_landlord_schedule,
    "book_viewing_appointment": book_viewing_appointment,
}
