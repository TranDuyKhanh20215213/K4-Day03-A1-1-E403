"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, search_apartments, book_viewing_appointment
from prompts import CHATBOT_BASELINE_PROMPT
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 {response}")


def print_tool_registry():
    """In ra danh sách tool mà Role 2 cung cấp cho Role 4 tích hợp."""
    print("🧰 Tools: search_apartments, book_viewing_appointment")


def extract_booking_details(user_query: str):
    """Trích xuất thông tin đặt lịch từ câu hỏi người dùng."""
    room_id = None
    room_match = re.search(r"\bNT\d+\b", user_query.upper())
    if room_match:
        room_id = room_match.group(0)

    date_time = None
    time_match = re.search(r"vào\s+(.+?)(?:\s+cho\b|$)", user_query, flags=re.IGNORECASE)
    if time_match:
        date_time = time_match.group(1).strip()

    customer_name = None
    name_patterns = [
        r"\bkhách\s+hàng\s+([A-ZÀ-Ỹ][\wÀ-ỹ-]*)",
        r"\btên\s+([A-ZÀ-Ỹ][\wÀ-ỹ-]*)",
        r"\bcho\s+([A-ZÀ-Ỹ][\wÀ-ỹ-]*)",
    ]
    for pattern in name_patterns:
        name_match = re.search(pattern, user_query, flags=re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).strip()
            if candidate.lower() not in {"khách", "hàng", "người"}:
                customer_name = candidate
                break

    phone = None
    phone_match = re.search(r"\b\d{9,11}\b", user_query)
    if phone_match:
        phone = phone_match.group(0)

    return room_id, date_time, customer_name, phone


def extract_search_context(user_query: str):
    """Trích xuất ngữ cảnh tìm phòng từ câu hỏi, nếu có."""
    normalized_query = user_query.lower()
    location = None

    patterns = [
        r"\b(?:ở khu vực|tại|khu vực|ở)\s+([A-Za-zÀ-Ỹà-ỹ0-9-]+(?:\s+[A-Za-zÀ-Ỹà-ỹ0-9-]+){0,1})",
        r"\btìm\s+(?:phòng trọ|căn hộ|nhà|phòng)\s+(?:ở|tại)\s+([A-Za-zÀ-Ỹà-ỹ0-9-]+(?:\s+[A-Za-zÀ-Ỹà-ỹ0-9-]+){0,1})",
        r"\btìm\s+giúp\s+tôi.*?\s(?:ở|tại)\s+([A-Za-zÀ-Ỹà-ỹ0-9-]+(?:\s+[A-Za-zÀ-Ỹà-ỹ0-9-]+){0,1})",
    ]
    for pattern in patterns:
        match = re.search(pattern, user_query, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            candidate = re.split(r"\s+(?:giá|dưới|triệu|nghìn|tháng|sau|đó|vào|cho|cần|với|có|là)\b", candidate, maxsplit=1, flags=re.IGNORECASE)[0]
            candidate = candidate.strip(" ,.;:-")
            if candidate and len(candidate.split()) <= 4:
                location = candidate
                break

    max_price = None
    price_patterns = [
        r"(?:dưới|giá dưới)\s+(\d+(?:[.,]\d+)?)\s*(triệu|nghìn)?",
        r"(?:dưới|giá dưới)\s+(\d+)",
    ]
    for pattern in price_patterns:
        price_match = re.search(pattern, normalized_query)
        if price_match:
            value = float(price_match.group(1).replace(",", "."))
            unit = price_match.group(2) or ""
            if unit == "triệu":
                max_price = int(value * 1000000)
            elif unit == "nghìn":
                max_price = int(value * 1000)
            else:
                max_price = int(value)
            break

    return location, max_price


def infer_task_plan(user_query: str):
    """Phân loại yêu cầu thành chuỗi công việc linh hoạt: tìm phòng, đặt lịch, hoặc cả hai."""
    normalized_query = user_query.lower()
    search_keywords = ["tìm", "tìm kiếm", "giá dưới", "khu vực", "thuê", "căn hộ", "nhà trọ", "trọ", "ở"]
    booking_keywords = ["đặt lịch", "xem phòng", "xem nhà", "hẹn", "mã phòng", "lịch hẹn"]
    has_room_ref = bool(re.search(r"\bnt\d+\b", normalized_query))

    needs_search = any(keyword in normalized_query for keyword in search_keywords)
    needs_booking = any(keyword in normalized_query for keyword in booking_keywords) or has_room_ref

    if needs_search and needs_booking:
        return ["search", "booking"]
    if needs_search:
        return ["search"]
    if needs_booking:
        return ["booking"]
    return []


def is_tool_failure(result: str) -> bool:
    """Phát hiện khi tool trả về lỗi hoặc đầu vào không hợp lệ."""
    lowered = result.lower()
    return any(marker in lowered for marker in ["lỗi", "không thể", "không hợp lệ", "không tồn tại", "đã hết phòng", "không tìm thấy"])


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent linh hoạt theo intent của người dùng, có Guardrails cho edge case.
    """
    print(f"\n🤖 [REACT AGENT] {user_query}")
    print_tool_registry()

    plan = infer_task_plan(user_query)
    if not plan:
        print("🧠 Thought: Câu hỏi không rõ ràng về việc tìm phòng hay đặt lịch.")
        print("🏁 Final Answer: Tôi chỉ hỗ trợ tìm phòng và đặt lịch xem phòng cho đề tài này.")
        return

    for step, action in enumerate(plan, start=1):
        print(f"\n--- Step {step}/{len(plan)} ---")

        if action == "search":
            location, max_price = extract_search_context(user_query)
            if not location:
                print("🧠 Thought: Câu hỏi chưa cung cấp khu vực cụ thể để tra cứu phòng.")
                print("🛡️ Guardrail: Yêu cầu người dùng cung cấp khu vực trước khi tiếp tục.")
                return
            if max_price is None:
                print("🧠 Thought: Câu hỏi chưa cung cấp ngân sách tối đa để tra cứu phòng.")
                print("🛡️ Guardrail: Yêu cầu người dùng cung cấp mức giá trước khi tiếp tục.")
                return
            print("🧠 Thought: cần tìm phòng phù hợp")
            print(f"🛠️ Action: search_apartments({location}, {max_price})")
            try:
                obs = search_apartments(location, max_price)
                print(f"👁️ {obs}")
                if is_tool_failure(obs):
                    print("🛡️ Guardrail: Dừng vòng lặp vì tool báo lỗi hoặc không tìm thấy kết quả phù hợp.")
                    return
            except Exception as exc:
                print(f"⚠️ Observation: Tool lỗi - {exc}")
                print("🛡️ Guardrail: Dừng vòng lặp vì tool gặp lỗi.")
                return
            continue

        if action == "booking":
            room_id, date_time, customer_name, phone = extract_booking_details(user_query)
            missing_fields = []
            if not room_id:
                missing_fields.append("mã phòng")
            if not date_time:
                missing_fields.append("thời gian")
            if not customer_name:
                missing_fields.append("tên khách")
            if not phone:
                missing_fields.append("số điện thoại")
            if missing_fields:
                print("🧠 Thought: Câu hỏi thiếu thông tin đặt lịch cần thiết.")
                print(f"🛡️ Guardrail: Thiếu {', '.join(missing_fields)}. Yêu cầu người dùng cung cấp thêm thông tin trước khi đặt lịch.")
                return
            print("🧠 Thought: cần đặt lịch xem phòng")
            print(f"🛠️ Action: book_viewing_appointment({room_id}, {date_time}, {customer_name}, {phone})")
            try:
                obs = book_viewing_appointment(room_id, date_time, customer_name, phone)
                print(f"👁️ {obs}")
                if is_tool_failure(obs):
                    print("🛡️ Guardrail: Dừng vòng lặp vì dữ liệu đặt lịch không hợp lệ hoặc tool báo lỗi.")
                    return
            except Exception as exc:
                print(f"⚠️ Observation: Tool lỗi - {exc}")
                print("🛡️ Guardrail: Dừng vòng lặp vì tool gặp lỗi.")
                return
            continue

    print("🏁 Hoàn tất")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 Provider: {provider.__class__.__name__}")
    
    tests = load_test_cases()
    print(f"✅ Loaded {len(tests)} test cases\n")
    
    # Chạy thử các câu test phù hợp với Mốc 2 và edge case guardrail
    demo_queries = [tests[2]["question"], tests[3]["question"], tests[4]["question"]]

    for index, sample_query in enumerate(demo_queries, start=1):
        print(f"\n=== Demo {index} ===")
        print("--- Baseline ---")
        run_baseline_chatbot(sample_query, provider)

        print("\n--- ReAct ---")
        run_react_agent(sample_query, provider)
