import unittest

from src.app import extract_booking_details, extract_search_context


class ExtractSearchContextTests(unittest.TestCase):
    def test_parses_location_and_million_budget(self):
        location, max_price = extract_search_context(
            "Tìm phòng trọ ở Cầu Giấy giá dưới 6 triệu"
        )
        self.assertEqual(location, "Cầu Giấy")
        self.assertEqual(max_price, 6_000_000)

    def test_returns_none_when_location_and_budget_are_not_explicit(self):
        location, max_price = extract_search_context("Tôi cần thuê một phòng phù hợp")
        self.assertIsNone(location)
        self.assertIsNone(max_price)

    def test_extracts_only_the_place_name_from_a_search_request(self):
        location, max_price = extract_search_context(
            "Tìm giúp tôi các phòng trọ ở khu vực Cầu Giấy với ngân sách dưới 6 triệu"
        )
        self.assertEqual(location, "Cầu Giấy")
        self.assertEqual(max_price, 6_000_000)

    def test_does_not_use_sample_defaults_for_booking_details(self):
        room_id, date_time, customer_name, phone = extract_booking_details(
            "Tôi muốn đặt lịch cho khách hàng Linh vào chiều mai"
        )
        self.assertIsNone(room_id)
        self.assertEqual(date_time, "chiều mai")
        self.assertEqual(customer_name, "Linh")
        self.assertIsNone(phone)


if __name__ == "__main__":
    unittest.main()
