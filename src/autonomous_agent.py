"""Bonus Autonomous Agent: Planning, Memory và Goal Evaluation."""

import re

from app import execute_tool, extract_booking_details, precheck_booking


MAX_AUTONOMOUS_STEPS = 5


class AutonomousRentalAgent:
    def __init__(self, goal: str, max_steps: int = MAX_AUTONOMOUS_STEPS):
        self.goal = goal
        self.max_steps = max_steps
        self.plan = []
        self.memory = []

    def _extract_search_args(self):
        location_match = re.search(
            r"(?:ở|tại|khu vực)\s+([A-Za-zÀ-ỹ0-9]+(?:\s+[A-Za-zÀ-ỹ0-9]+)?)",
            self.goal,
            flags=re.IGNORECASE,
        )
        price_match = re.search(
            r"(?:dưới|ngân sách)\s+(\d+(?:[.,]\d+)?)\s*(triệu|nghìn)?",
            self.goal,
            flags=re.IGNORECASE,
        )
        if not location_match or not price_match:
            return None

        location = re.split(
            r"\s+(?:giá|với|dưới|ngân sách)\b",
            location_match.group(1),
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        value = float(price_match.group(1).replace(",", "."))
        unit = (price_match.group(2) or "").lower()
        max_price = int(value * 1_000_000 if unit == "triệu" else value * 1_000 if unit == "nghìn" else value)
        return [location.strip(), max_price]

    def create_plan(self):
        """Tự chia goal thành chuỗi tool calls trước khi thực thi."""
        lowered = self.goal.lower()
        plan = []

        if any(marker in lowered for marker in ("tìm", "phòng trọ", "căn hộ", "giá dưới")):
            search_args = self._extract_search_args()
            if not search_args:
                return []
            plan.append(
                {
                    "task": "Tìm phòng phù hợp",
                    "tool": "search_apartments",
                    "args": search_args,
                }
            )

        if any(marker in lowered for marker in ("đặt lịch", "xem phòng", "lịch hẹn")):
            if precheck_booking(self.goal):
                return []

            room_id, date_time, customer_name, phone = extract_booking_details(self.goal)
            date_match = re.search(
                r"(ngày\s+mai|\d{1,2}/\d{1,2}/\d{4})",
                date_time,
                flags=re.IGNORECASE,
            )
            schedule_date = date_match.group(1) if date_match else date_time
            plan.extend(
                [
                    {
                        "task": "Kiểm tra lịch chủ nhà",
                        "tool": "check_landlord_schedule",
                        "args": [room_id, schedule_date],
                    },
                    {
                        "task": "Đặt lịch xem phòng",
                        "tool": "book_viewing_appointment",
                        "args": [room_id, date_time, customer_name, phone],
                    },
                ]
            )

        self.plan = plan
        return plan

    def _remember(self, step: int, item: dict, observation: str, status: str):
        self.memory.append(
            {
                "step": step,
                "task": item["task"],
                "tool": item["tool"],
                "observation": observation,
                "status": status,
            }
        )
        print(f"💾 Memory: step {step} | {item['tool']} | {status}")

    def run(self):
        print(f"\n🚀 [AUTONOMOUS AGENT] Goal: {self.goal}")
        plan = self.create_plan()

        if not plan:
            print("🛡️ Goal Evaluation: Không đủ dữ liệu để lập kế hoạch.")
            return self.memory
        if len(plan) > self.max_steps:
            print("🛡️ Goal Evaluation: Kế hoạch vượt giới hạn an toàn.")
            return self.memory

        print("📋 Plan:")
        for index, item in enumerate(plan, start=1):
            print(f"  {index}. {item['task']} -> {item['tool']}")

        for step, item in enumerate(plan, start=1):
            print(f"\n--- Autonomous Step {step}/{len(plan)} ---")
            observation = execute_tool(item["tool"], list(item["args"]))
            print(f"🛠️ Action: {item['tool']}({', '.join(map(str, item['args']))})")
            print(f"👁️ Observation: {observation}")

            if observation.startswith("ERROR") or "LỖI" in observation:
                self._remember(step, item, observation, "failed")
                print("🎯 Goal Evaluation: Dừng vì tool thất bại.")
                return self.memory

            if item["tool"] == "check_landlord_schedule":
                _, requested_time, _, _ = extract_booking_details(self.goal)
                clock = re.search(r"\b\d{1,2}:\d{2}\b", requested_time or "")
                if clock and clock.group(0) not in observation:
                    self._remember(step, item, observation, "needs_replan")
                    print("🎯 Goal Evaluation: Giờ yêu cầu không trống, cần lập kế hoạch lại.")
                    return self.memory

            self._remember(step, item, observation, "completed")

        print(f"🎯 Goal Evaluation: Hoàn thành {len(self.memory)}/{len(plan)} bước.")
        return self.memory


if __name__ == "__main__":
    DEMO_GOAL = (
        "Tìm phòng trọ ở Cầu Giấy giá dưới 6 triệu, sau đó đặt lịch xem phòng "
        "NT01 vào 10:00 sáng ngày mai cho Phát (SĐT: 0987654321)."
    )
    AutonomousRentalAgent(DEMO_GOAL).run()
