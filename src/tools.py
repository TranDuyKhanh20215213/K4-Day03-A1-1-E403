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


def get_weather(location: str) -> str:
    return f"Thời tiết tại {location}: 28°C, nắng nhẹ."


def search_flights(origin: str, destination: str) -> str:
    return f"Không áp dụng cho chủ đề thuê nhà."


AVAILABLE_TOOLS = {
    "search_apartments": search_apartments,
    "book_viewing_appointment": book_viewing_appointment,
    "get_weather": get_weather,
    "search_flights": search_flights,
}
