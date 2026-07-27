from __future__ import annotations

from typing import Any
from backend.models import utc_now
from backend.state import AppState


class ShiftHandoverManager:
    def __init__(self) -> None:
        self.active_shift = {
            "shift_id": "SHIFT-0402",
            "current_guard": "Guard Jordan",
            "incoming_guard": "Guard Sarah",
            "tower_id": "TOWER-01",
            "rotation_interval_minutes": 35,
            "seconds_remaining_in_rotation": 1420,  # ~23 mins left
            "vigilance_score": "OPTIMAL (98%)",
            "handover_notes": "Heavy rip current activity near South Sandbar. 3 preventive swimmer warnings issued.",
            "last_rotation_time": utc_now(),
        }
        self.rotation_history: list[dict[str, Any]] = []

    def get_status(self) -> dict[str, Any]:
        return {"shift": self.active_shift, "history": self.rotation_history}

    def execute_handover(self, state: AppState, incoming_guard: str, notes: str) -> dict[str, Any]:
        outgoing = self.active_shift["current_guard"]
        self.rotation_history.insert(0, {
            "shift_id": self.active_shift["shift_id"],
            "outgoing_guard": outgoing,
            "incoming_guard": incoming_guard,
            "handover_time": utc_now(),
            "notes": notes,
        })

        self.active_shift.update({
            "shift_id": f"SHIFT-{len(self.rotation_history) + 400}",
            "current_guard": incoming_guard,
            "incoming_guard": outgoing,
            "seconds_remaining_in_rotation": 2100,  # Reset 35 min rotation countdown
            "handover_notes": notes,
            "last_rotation_time": utc_now(),
        })

        msg = f"SHIFT HANDOVER: Guard vigilance rotation completed. {incoming_guard} took over Tower 1 from {outgoing}."
        state.publish("handover", msg, camera_id="camera_live")
        return {"success": True, "shift": self.active_shift}


handover_manager = ShiftHandoverManager()
