from __future__ import annotations

from typing import Any
from backend.models import utc_now
from backend.state import AppState


HAPTIC_PATTERNS = {
    "critical": {
        "pattern": [400, 100, 400, 100, 800, 200, 400],
        "intensity": "heavy",
        "label": "Emergency Alert Vibration",
        "description": "Rapid pulse with sustained burst for critical swimmer or surf hazard",
    },
    "high": {
        "pattern": [300, 100, 300, 100, 300],
        "intensity": "strong",
        "label": "High Warning Vibration",
        "description": "Triple strong tap pattern for elevated beach hazard",
    },
    "moderate": {
        "pattern": [200, 150, 200],
        "intensity": "medium",
        "label": "Caution Vibration",
        "description": "Double gentle tap pattern for condition changes",
    },
    "low": {
        "pattern": [100],
        "intensity": "light",
        "label": "Status Pulse",
        "description": "Single subtle tick for normal monitoring",
    },
}


def get_watch_status(state: AppState, ocean_risk: dict | None = None, weather: dict | None = None, ocean: dict | None = None) -> dict[str, Any]:
    snapshot = state.snapshot()
    active_alerts = [a for a in snapshot["alerts"] if not a.get("acknowledged")]
    latest_alert = active_alerts[0] if active_alerts else None

    risk_level = (ocean_risk or {}).get("risk_level", "low")
    if latest_alert and latest_alert.get("severity") in {"high", "critical"}:
        risk_level = latest_alert.get("severity")

    haptic = HAPTIC_PATTERNS.get(risk_level, HAPTIC_PATTERNS["low"])

    quick_actions = [
        {
            "id": "acknowledge_alert",
            "label": "Acknowledge",
            "icon": "check-circle",
            "enabled": bool(latest_alert),
            "alert_id": latest_alert["id"] if latest_alert else None,
        },
        {
            "id": "trigger_whistle",
            "label": "Whistle + Announce",
            "icon": "volume-2",
            "enabled": True,
        },
        {
            "id": "dispatch_guard",
            "label": "Dispatch Patrol",
            "icon": "user-plus",
            "enabled": True,
        },
        {
            "id": "ping_tower",
            "label": "Ping Tower",
            "icon": "radio",
            "enabled": True,
        },
        {
            "id": "request_sos",
            "label": "SOS Escalation",
            "icon": "alert-triangle",
            "enabled": True,
            "danger": True,
        },
    ]

    wave_info = (ocean or {}).get("wave_height_ft")
    water_temp = (ocean or {}).get("water_temp_f")
    wind_info = (weather or {}).get("wind_speed_mph")

    return {
        "timestamp": utc_now(),
        "device_target": "Lifeguard Smart Watch (Wear OS / watchOS)",
        "global_status": snapshot["global_status"],
        "risk_level": risk_level,
        "active_alerts_count": len(active_alerts),
        "latest_alert": latest_alert,
        "haptic_profile": haptic,
        "ocean_summary": {
            "wave_height": f"{wave_info} ft" if wave_info is not None else "N/A",
            "water_temp": f"{water_temp} °F" if water_temp is not None else "N/A",
            "wind_speed": f"{wind_info} mph" if wind_info is not None else "N/A",
            "sources": (ocean_risk or {}).get("sources", []),
        },
        "quick_actions": quick_actions,
        "warning_draft": snapshot.get("warning"),
        "escalation_status": snapshot.get("escalation"),
    }


def handle_watch_action(state: AppState, action: str, camera_id: str | None = None, alert_id: str | None = None, details: dict | None = None) -> dict[str, Any]:
    camera_id = camera_id or "camera_live"
    details = details or {}

    if action == "acknowledge_alert":
        target_id = alert_id
        if not target_id:
            active = [a for a in state.alerts if not a.get("acknowledged")]
            if active:
                target_id = active[0]["id"]
        if target_id and state.acknowledge(target_id):
            state.publish("watch", "Lifeguard acknowledged alert from Smartwatch", camera_id=camera_id, details={"alert_id": target_id})
            return {"success": True, "action": action, "alert_id": target_id, "message": "Alert acknowledged from watch"}
        return {"success": False, "action": action, "error": "No alert found to acknowledge"}

    elif action == "trigger_whistle":
        msg = details.get("message") or (state.warning or {}).get("message") or "Attention swimmers: please exercise caution near rip currents."
        state.warning = {"camera_id": camera_id, "message": msg, "issued": True}
        state.publish("watch", "Lifeguard triggered public whistle + announcement from Smartwatch", camera_id=camera_id, details={"message": msg, "source": "smartwatch"})
        return {"success": True, "action": action, "message": msg}

    elif action == "dispatch_guard":
        state.publish("watch", "WATCH ACTION: Backup patrol guard dispatched from Smartwatch wrist button", camera_id=camera_id, severity="high", details={"guard": details.get("guard", "Unit 1")})
        return {"success": True, "action": action, "message": "Patrol reinforcement dispatched"}

    elif action == "ping_tower":
        state.publish("watch", "WATCH ACTION: Lifeguard smartwatch pinged main lifeguard tower", camera_id=camera_id, details={"location": "Deerfield Beach Tower 2"})
        return {"success": True, "action": action, "message": "Tower ping sent"}

    elif action == "request_sos":
        state.escalation = {
            "camera_id": camera_id,
            "severity": "critical",
            "reason": details.get("reason", "Immediate lifeguard SOS triggered from Smartwatch"),
            "status": "wrist_sos_triggered",
        }
        state.publish("watch", "SIMULATED SOS: Smartwatch wrist panic trigger activated!", camera_id=camera_id, severity="critical")
        return {"success": True, "action": action, "message": "Simulated SOS emergency requested"}

    else:
        return {"success": False, "action": action, "error": f"Unknown watch action: {action}"}
