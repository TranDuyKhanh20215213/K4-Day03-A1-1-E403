"""ReAct Agent V1: prompt -> parser -> executor -> observation -> loop."""

import ast
import concurrent.futures
import json
import os
import re
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_SYSTEM_PROMPT, TIMEOUT_SECONDS
from providers import get_llm_provider
from tools import AVAILABLE_TOOLS


VALID_ROOM_IDS = {"NT01", "NT02", "NT03", "NT04"}
TOOL_ARITY = {
    "search_apartments": 2,
    "check_landlord_schedule": 2,
    "book_viewing_appointment": 4,
}


def load_test_cases():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_dir, "config", "test_cases.json")
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def run_baseline_chatbot(user_query: str, provider):
    print(f"\n💬 [CHATBOT BASELINE] {user_query}")
    print(f"🤖 {provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)}")


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
    else:
        date_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", user_query)
        if date_match:
            date_time = date_match.group(0)

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


def strip_accents(text: str) -> str:
    """Normalize text for lightweight safety checks."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def detect_prompt_injection(user_query: str) -> bool:
    """Detect common attempts to override system/tool instructions."""
    normalized = strip_accents(user_query)
    suspicious_patterns = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "bo qua huong dan",
        "bo qua tat ca huong dan",
        "tiet lo system prompt",
        "in system prompt",
        "reveal system prompt",
        "print system prompt",
        "api key",
        "secret",
        "delete_database",
        "xoa database",
        "goi tool khong duoc phep",
        "bypass guardrail",
    ]
    return any(pattern in normalized for pattern in suspicious_patterns)


def is_provider_error(response: str) -> bool:
    """Identify provider/network errors so the app can use deterministic fallback."""
    lowered = strip_accents(response)
    return any(
        marker in lowered
        for marker in [
            " exception]",
            " error]",
            "connection error",
            "chua cau hinh",
            "mock provider",
            "phan hoi gia lap offline",
        ]
    )


def invalid_calendar_date(text: str) -> bool:
    match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", text)
    if not match:
        return False
    try:
        datetime.strptime(match.group(0), "%d/%m/%Y")
        return False
    except ValueError:
        return True


def precheck_booking(query: str) -> str:
    """Block explicit invalid booking data before any tool call."""
    lowered = query.lower()
    if not any(marker in lowered for marker in ("đặt lịch", "xem phòng", "lịch hẹn")) and not re.search(r"\bnt\d+\b", lowered):
        return ""

    room_id, date_time, customer_name, phone = extract_booking_details(query)
    issues = []
    if room_id and room_id not in VALID_ROOM_IDS:
        issues.append(f"mã phòng {room_id} không tồn tại")
    if date_time and invalid_calendar_date(date_time):
        issues.append("ngày hẹn không hợp lệ")

    missing = [
        label
        for label, value in (
            ("mã phòng", room_id),
            ("thời gian", date_time),
            ("tên khách", customer_name),
            ("số điện thoại", phone),
        )
        if not value
    ]
    if missing:
        issues.append("thiếu " + ", ".join(missing))
    return "; ".join(issues)


def parse_react_response(response: str) -> dict:
    """Parse either Action or Final Answer from one LLM turn."""
    final = re.search(r"Final Answer:\s*(.+)", response, flags=re.IGNORECASE | re.DOTALL)
    action = re.search(r"Action:\s*([a-zA-Z_]\w*)\s*\[(.*)\]\s*$", response, flags=re.IGNORECASE | re.DOTALL)
    parsed = {"final_answer": final.group(1).strip() if final else "", "tool_name": "", "args": []}
    if not action:
        return parsed

    parsed["tool_name"] = action.group(1)
    try:
        parsed["args"] = ast.literal_eval(f"[{action.group(2)}]")
    except (SyntaxError, ValueError):
        return {"final_answer": "", "tool_name": "", "args": []}
    return parsed


def validate_tool_args(tool_name: str, args: list) -> str:
    if tool_name not in TOOL_ARITY:
        return f"ERROR: Tool '{tool_name}' không nằm trong allowlist."
    if len(args) != TOOL_ARITY[tool_name]:
        return f"ERROR: Tool '{tool_name}' nhận sai số lượng tham số."

    if tool_name == "search_apartments":
        location, max_price = args
        if not isinstance(location, str) or not location.strip():
            return "ERROR: location phải là chuỗi không rỗng."
        try:
            args[1] = int(max_price)
        except (TypeError, ValueError):
            return "ERROR: max_price phải là số nguyên."
        if not 0 < args[1] <= 100_000_000:
            return "ERROR: max_price nằm ngoài khoảng hợp lệ."

    elif tool_name == "check_landlord_schedule":
        room_id, date = map(str, args)
        if room_id.upper() not in VALID_ROOM_IDS or not date.strip():
            return "ERROR: mã phòng hoặc ngày kiểm tra không hợp lệ."
        args[:] = [room_id.upper(), date.strip()]

    else:
        room_id, date_time, customer_name, phone = map(str, args)
        if room_id.upper() not in VALID_ROOM_IDS:
            return "ERROR: mã phòng không tồn tại."
        if not re.fullmatch(r"\d{9,11}", phone):
            return "ERROR: số điện thoại phải có 9-11 chữ số."
        if not date_time.strip() or not customer_name.strip() or invalid_calendar_date(date_time):
            return "ERROR: thông tin đặt lịch không hợp lệ."
        args[:] = [room_id.upper(), date_time.strip(), customer_name.strip(), phone]
    return ""


def execute_tool(tool_name: str, args: list) -> str:
    error = validate_tool_args(tool_name, args)
    if error:
        return error

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(AVAILABLE_TOOLS[tool_name], *args)
        try:
            return future.result(timeout=TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError:
            return f"ERROR: Tool '{tool_name}' vượt timeout {TIMEOUT_SECONDS} giây."
        except Exception as exc:
            return f"ERROR: Tool '{tool_name}' gặp lỗi: {exc}"


def build_react_prompt(user_query: str, scratchpad: str) -> str:
    trace = scratchpad or "(chưa có Observation)"
    return f"""<user_query>
{user_query}
</user_query>

<trace>
{trace}
</trace>"""


def needs_tool(query: str) -> bool:
    lowered = query.lower()
    return any(marker in lowered for marker in ("tìm phòng", "tìm giúp", "giá dưới", "đặt lịch", "xem phòng", "nt"))


def is_clarification(answer: str) -> bool:
    lowered = answer.lower()
    return "?" in answer or any(marker in lowered for marker in ("vui lòng", "cung cấp", "cho biết"))


def is_provider_error(response: str) -> bool:
    lowered = response.lower()
    return any(marker in lowered for marker in (" exception]", " error]", "connection error", "chưa cấu hình"))


def detect_prompt_injection(query: str) -> bool:
    lowered = query.lower()
    markers = ("ignore previous instructions", "bỏ qua hướng dẫn", "system prompt", "api key", "bypass guardrail")
    return any(marker in lowered for marker in markers)


def run_react_agent(user_query: str, provider):
    print(f"\n🤖 [REACT AGENT] {user_query}")
    print("🧰 Tools: " + ", ".join(AVAILABLE_TOOLS))

    if detect_prompt_injection(user_query):
        print("🛡️ Guardrail: Phát hiện prompt injection.")
        print("🏁 Final Answer: Tôi chỉ hỗ trợ tìm phòng và đặt lịch xem phòng.")
        return

    booking_error = precheck_booking(user_query)
    if booking_error:
        print(f"🛡️ Guardrail: {booking_error}.")
        print(f"🏁 Final Answer: Chưa thể đặt lịch vì {booking_error}.")
        return

    scratchpad = ""
    executed_actions = set()

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- ReAct Iteration {iteration}/{MAX_ITERATIONS} ---")
        prompt = build_react_prompt(user_query, scratchpad)
        output = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        print(output)

        if is_provider_error(output):
            print("🛡️ Guardrail: Provider LLM không khả dụng.")
            print("🏁 Final Answer: Chưa thể xử lý yêu cầu lúc này.")
            return

        parsed = parse_react_response(output)
        if parsed["final_answer"]:
            has_evidence = "Observation:" in scratchpad
            if needs_tool(user_query) and not has_evidence and not is_clarification(parsed["final_answer"]):
                observation = "ERROR: Không được trả Final Answer trước khi có Observation."
                print(f"👁️ Observation: {observation}")
                scratchpad += f"{output}\nObservation: {observation}\n\n"
                continue
            print("🏁 Hoàn tất")
            return

        if not parsed["tool_name"]:
            observation = "ERROR: Phản hồi phải có Action hoặc Final Answer đúng định dạng."
        else:
            signature = (parsed["tool_name"], repr(parsed["args"]))
            if signature in executed_actions:
                observation = "ERROR: Action này đã được gọi với cùng tham số."
            else:
                executed_actions.add(signature)
                observation = execute_tool(parsed["tool_name"], parsed["args"])

        print(f"👁️ Observation: {observation}")
        scratchpad += f"{output}\nObservation: {observation}\n\n"

    print("🛡️ Guardrail: Đã chạm MAX_ITERATIONS, dừng để tránh lặp vô hạn.")
    print("🏁 Final Answer: Chưa thể hoàn tất yêu cầu trong số vòng xử lý cho phép.")


def main():
    print("=" * 50)
    print("🏫 LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 50)
    provider = get_llm_provider()
    tests = load_test_cases()
    print(f"🔌 Provider: {provider.__class__.__name__}")
    print(f"✅ Loaded {len(tests)} test cases\n")

    for index, test in enumerate(tests[2:5], start=1):
        print(f"\n=== Demo {index} ===")
        print("--- Baseline ---")
        run_baseline_chatbot(test["question"], provider)
        print("\n--- ReAct ---")
        run_react_agent(test["question"], provider)


if __name__ == "__main__":
    main()
