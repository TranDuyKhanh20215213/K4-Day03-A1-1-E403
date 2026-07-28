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


def extract_booking_details(query: str):
    room = re.search(r"\bNT\d+\b", query, flags=re.IGNORECASE)
    time = re.search(r"vào\s+(.+?)(?:\s+cho\b|$)", query, flags=re.IGNORECASE)
    name = re.search(r"\bcho\s+([^\s(,]+)", query, flags=re.IGNORECASE)
    phone = re.search(r"\b\d{9,11}\b", query)
    return (
        room.group(0).upper() if room else None,
        time.group(1).strip() if time else None,
        name.group(1).strip() if name else None,
        phone.group(0) if phone else None,
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
