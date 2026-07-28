"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline provider mô phỏng ReAct để chạy demo mà không cần API key."""

    @staticmethod
    def _extract_query_and_trace(prompt: str) -> tuple[str, str]:
        """Tách câu hỏi và trace do app tạo từ ReAct prompt."""
        query_match = re.search(
            r"User Query:\s*(.*?)\n\s*Available tools:",
            prompt,
            flags=re.IGNORECASE | re.DOTALL,
        )
        query = query_match.group(1).strip() if query_match else ""
        trace = prompt.partition("Trace so far:")[2]
        return query, trace

    @staticmethod
    def _find_location(query: str) -> str:
        for location in ("Cầu Giấy", "Bình Thạnh", "Quận 7"):
            if location.lower() in query.lower():
                return location
        return ""

    @staticmethod
    def _find_budget(query: str) -> int:
        match = re.search(r"(?:dưới|tối đa|giá)\s*(\d+(?:[.,]\d+)?)\s*triệu", query, flags=re.IGNORECASE)
        return int(float(match.group(1).replace(",", ".")) * 1_000_000) if match else 10_000_000

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        query, trace = self._extract_query_and_trace(prompt)

        # Baseline không cần cấu trúc ReAct; chỉ đóng vai trò câu trả lời minh họa.
        if not query:
            return "Bạn nên cân nhắc vị trí, giá thuê, an ninh, chi phí điện nước và điều khoản hợp đồng trước khi thuê phòng."

        normalized_query = query.lower()
        normalized_trace = trace.lower()
        needs_search = any(term in normalized_query for term in ("tìm", "phòng trọ", "căn hộ"))
        needs_booking = any(term in normalized_query for term in ("đặt lịch", "xem phòng", "mã nt"))

        if needs_search and "action: search_apartments" not in normalized_trace:
            location = self._find_location(query)
            if not location:
                return "Thought: Tôi cần biết khu vực cần tìm phòng.\nFinal Answer: Bạn muốn tìm phòng ở khu vực nào?"
            return (
                "Thought: Tôi cần tra cứu phòng phù hợp với khu vực và ngân sách đã nêu.\n"
                f'Action: search_apartments["{location}", {self._find_budget(query)}]'
            )

        room_match = re.search(r"\bNT\d+\b", query, flags=re.IGNORECASE)
        room_id = room_match.group(0).upper() if room_match else ""
        date_match = re.search(r"(ngày\s+mai|\d{1,2}/\d{1,2}/\d{4})", query, flags=re.IGNORECASE)
        date = date_match.group(1) if date_match else "ngày mai"

        if needs_booking and "action: check_landlord_schedule" not in normalized_trace:
            if not room_id:
                return "Thought: Tôi cần mã phòng trước khi kiểm tra lịch.\nFinal Answer: Vui lòng cung cấp mã phòng bạn muốn xem."
            return (
                "Thought: Tôi cần kiểm tra lịch trống của chủ nhà trước khi đặt lịch.\n"
                f'Action: check_landlord_schedule["{room_id}", "{date}"]'
            )

        if needs_booking and "action: book_viewing_appointment" not in normalized_trace:
            time_match = re.search(r"vào\s+(.+?)(?:\s+cho\s+|\s*\(\s*sđt|$)", query, flags=re.IGNORECASE)
            name_match = re.search(r"\bcho\s+([^\s(,]+)", query, flags=re.IGNORECASE)
            phone_match = re.search(r"\b\d{9,11}\b", query)
            if not all((room_id, time_match, name_match, phone_match)):
                return "Thought: Tôi chưa có đủ dữ liệu đặt lịch.\nFinal Answer: Vui lòng cung cấp mã phòng, thời gian, tên và số điện thoại."
            return (
                "Thought: Khung giờ yêu cầu đã được kiểm tra, tôi tiến hành đặt lịch xem phòng.\n"
                f'Action: book_viewing_appointment["{room_id}", "{time_match.group(1).strip()}", '
                f'"{name_match.group(1).strip()}", "{phone_match.group(0)}"]'
            )

        if needs_booking:
            return "Thought: Tôi đã hoàn tất các công cụ cần thiết.\nFinal Answer: Đã kiểm tra lịch và đặt lịch xem phòng thành công."
        if needs_search:
            return "Thought: Tôi đã nhận được danh sách phòng từ công cụ.\nFinal Answer: Đây là các phòng phù hợp với khu vực và ngân sách của bạn."
        return "Thought: Đây là câu hỏi tư vấn thông thường.\nFinal Answer: Tôi có thể hỗ trợ bạn tìm phòng hoặc đặt lịch xem phòng."


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
