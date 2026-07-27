from __future__ import annotations

from typing import Any
from backend.models import utc_now
from backend.state import AppState


class SirenControlManager:
    def __init__(self) -> None:
        self.strobe_active = False
        self.siren_active = False
        self.last_triggered_by = None
        self.mode = "standby"

    def get_status(self) -> dict[str, Any]:
        return {
            "strobe_active": self.strobe_active,
            "siren_active": self.siren_active,
            "mode": self.mode,
            "controller": "IP Modbus Relay Controller #1 (Tower 1-4 Master Strobe)",
            "last_triggered_by": self.last_triggered_by,
        }

    def trigger_alarm(self, state: AppState, mode: str, operator_name: str = "Guard Jordan") -> dict[str, Any]:
        self.mode = mode
        self.last_triggered_by = operator_name

        if mode == "evacuate_beach":
            self.strobe_active = True
            self.siren_active = True
            msg = f"SIREN / PA RELAY: PHYSICAL BEACH EVACUATION SIREN & STROBES ACTIVATED by {operator_name}!"
            state.publish("siren", msg, camera_id="camera_live", severity="critical")
        elif mode == "warning_strobe":
            self.strobe_active = True
            self.siren_active = False
            msg = f"SIREN / PA RELAY: Tower High-Intensity Warning Strobes Activated by {operator_name}"
            state.publish("siren", msg, camera_id="camera_live", severity="high")
        else:
            self.strobe_active = False
            self.siren_active = False
            msg = f"SIREN / PA RELAY: Siren and Strobe Relays reset to standby by {operator_name}"
            state.publish("siren", msg, camera_id="camera_live")

        return self.get_status()


siren_manager = SirenControlManager()
