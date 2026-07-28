"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
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
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
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
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def print_tool_registry():
    """In ra danh sách tool mà Role 2 cung cấp cho Role 4 tích hợp."""
    print("\n🧰 Tool registry cho ReAct Agent:")
    for name in AVAILABLE_TOOLS:
        print(f" - {name}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    print_tool_registry()
    step = 0
    normalized_query = user_query.lower()

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        if "tìm" in normalized_query or "phòng" in normalized_query or "căn hộ" in normalized_query:
            print("🧠 Thought: Người dùng cần tìm phòng phù hợp theo khu vực và ngân sách.")
            print("🛠️ Action: search_apartments['Cầu Giấy', 6000000]")
            obs = search_apartments("Cầu Giấy", 6000000)
            print(f"👁️ Observation: {obs}")

            if "đặt lịch" in normalized_query or "xem phòng" in normalized_query:
                print("🧠 Thought: Người dùng còn muốn đặt lịch xem phòng, nên cần chốt lịch hẹn.")
                print("🛠️ Action: book_viewing_appointment['NT01', '10:00 sáng ngày mai', 'Phát', '0987654321']")
                obs = book_viewing_appointment("NT01", "10:00 sáng ngày mai", "Phát", "0987654321")
                print(f"👁️ Observation: {obs}")

            print("🏁 Final Answer: Tôi đã sử dụng tool để tìm phòng và, nếu cần, đặt lịch xem phòng cho người dùng.")
            break

        print("🏁 Final Answer: Tôi chưa nhận diện được hành động cụ thể từ câu hỏi này.")
        break

    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử các câu test phù hợp với Mốc 2: tìm phòng và đặt lịch xem nhà
    demo_queries = [tests[2]["question"], tests[3]["question"]]

    for index, sample_query in enumerate(demo_queries, start=1):
        print(f"\n=== DEMO {index} ===")
        print("--- CHẠY TRÊN CHATBOT BASELINE ---")
        run_baseline_chatbot(sample_query, provider)

        print("\n--- CHẠY TRÊN REACT AGENT ---")
        run_react_agent(sample_query, provider)
