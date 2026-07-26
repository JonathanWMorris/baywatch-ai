from __future__ import annotations

import os
import threading
import uuid
from collections import deque

from backend.models import Assessment, TimelineEvent, utc_now


class AppState:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.events: deque[dict] = deque(maxlen=250)
        self.assessments: dict[str, dict] = {}
        self.alerts: list[dict] = []
        self.warning: dict | None = None
        self.escalation: dict | None = None
        self.cameras = [
            {
                "id": "camera_live",
                "name": "Deerfield Beach Live",
                "status": "live_ready",
                "risk_level": "low",
                "media_url": None,
                "source_type": "youtube",
                "embed_url": (
                    "https://www.youtube.com/embed/"
                    f"{os.getenv('LIVE_YOUTUBE_VIDEO_ID', 'rdeoEeJ00xA')}?autoplay=1&mute=1"
                ),
                "external": False,
            },
        ]
        self.publish("system", "Baywatch AI monitoring initialized")

    def publish(self, category: str, message: str, **kwargs) -> dict:
        event = TimelineEvent(id=str(uuid.uuid4()), category=category, message=message, **kwargs).model_dump()
        with self._lock:
            self.events.appendleft(event)
        return event

    def apply_assessment(self, assessment: Assessment) -> dict:
        payload = assessment.model_dump()
        with self._lock:
            self.assessments[assessment.camera_id] = payload
            for camera in self.cameras:
                if camera["id"] == assessment.camera_id:
                    camera["risk_level"] = assessment.risk_level
                    camera["status"] = "attention" if assessment.events else "monitoring"
            for hazard in assessment.events:
                if hazard.severity in {"moderate", "high", "critical"}:
                    self.alerts.insert(0, {
                        "id": str(uuid.uuid4()), "camera_id": assessment.camera_id,
                        "acknowledged": False, "created_at": utc_now(), **hazard.model_dump(),
                    })
            if assessment.public_warning:
                self.warning = {"camera_id": assessment.camera_id, "message": assessment.public_warning, "issued": False}
        self.publish("analysis", assessment.reasoning_summary, camera_id=assessment.camera_id, severity=assessment.risk_level)
        return payload

    def snapshot(self) -> dict:
        with self._lock:
            active = [a for a in self.alerts if not a["acknowledged"]]
            levels = [c["risk_level"] for c in self.cameras]
            if any(level == "critical" for level in levels) or active:
                global_status = "active_alert"
            elif any(level in {"moderate", "high"} for level in levels):
                global_status = "elevated_conditions"
            else:
                global_status = "monitoring"
            return {
                "global_status": global_status, "cameras": list(self.cameras),
                "assessments": dict(self.assessments), "alerts": list(self.alerts),
                "warning": self.warning, "escalation": self.escalation,
                "events": list(self.events),
            }

    def acknowledge(self, alert_id: str) -> bool:
        with self._lock:
            for alert in self.alerts:
                if alert["id"] == alert_id:
                    alert["acknowledged"] = True
                    self.publish("operator", "Lifeguard acknowledged alert", camera_id=alert["camera_id"])
                    return True
        return False


state = AppState()
