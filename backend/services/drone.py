from __future__ import annotations

from typing import Any
from backend.models import utc_now
from backend.state import AppState


class DroneDispatchManager:
    def __init__(self) -> None:
        self.drones = [
            {
                "drone_id": "RESCUE-DRONE-01",
                "model": "AeroBuoy Autonomous Lifeguard UAV",
                "status": "ready",  # "ready", "dispatched", "in_flight", "buoy_dropped", "returning"
                "battery_pct": 98,
                "payload_status": "buoy_attached",  # "buoy_attached" or "buoy_dropped"
                "current_location": {"lat": 26.31656, "lon": -80.07560, "altitude_m": 0.0},
                "target_location": None,
                "last_mission": None,
            }
        ]

    def get_status(self) -> dict[str, Any]:
        return {"drones": self.drones}

    def dispatch_drone(self, state: AppState, drone_id: str, target_lat: float, target_lon: float, target_zone: str) -> dict[str, Any]:
        drone = next((d for d in self.drones if d["drone_id"] == drone_id), self.drones[0])
        drone["status"] = "dispatched"
        drone["payload_status"] = "buoy_attached"
        drone["target_location"] = {"lat": target_lat, "lon": target_lon, "zone": target_zone}
        drone["last_mission"] = {
            "dispatched_at": utc_now(),
            "target_zone": target_zone,
            "coordinates": f"{target_lat:.5f}, {target_lon:.5f}",
        }

        state.publish(
            "drone",
            f"MAVLink DISPATCH: Autonomous Rescue Drone {drone['drone_id']} launched to {target_zone} ({target_lat:.5f}, {target_lon:.5f}) with self-inflating buoy",
            camera_id="camera_live",
            severity="critical",
            details={"drone": drone},
        )
        return {"success": True, "drone": drone, "message": f"Autonomous drone dispatched to {target_zone}"}

    def drop_buoy(self, state: AppState, drone_id: str) -> dict[str, Any]:
        drone = next((d for d in self.drones if d["drone_id"] == drone_id), self.drones[0])
        drone["payload_status"] = "buoy_dropped"
        drone["status"] = "returning"

        state.publish(
            "drone",
            f"MAVLink PAYLOAD RELEASE: Self-inflating flotation buoy dropped by {drone['drone_id']} at target coordinates!",
            camera_id="camera_live",
            severity="critical",
        )
        return {"success": True, "drone": drone, "message": "Self-inflating buoy dropped"}


drone_manager = DroneDispatchManager()
