from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "moderate", "high", "critical", "unknown"]
Severity = Literal["low", "moderate", "high", "critical"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HazardEvent(BaseModel):
    type: str
    severity: Severity
    description: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)


class AudioObservation(BaseModel):
    type: str
    description: str
    confidence: float = Field(default=0, ge=0, le=1)


class EnvironmentAssessment(BaseModel):
    risk_level: RiskLevel = "unknown"
    factors: list[str] = Field(default_factory=list)
    summary: str = "Environmental assessment unavailable."


class ToolRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


class Assessment(BaseModel):
    camera_id: str
    analysis_status: Literal["complete", "degraded", "failed"] = "complete"
    risk_level: RiskLevel = "unknown"
    events: list[HazardEvent] = Field(default_factory=list)
    audio_observations: list[AudioObservation] = Field(default_factory=list)
    environment: EnvironmentAssessment = Field(default_factory=EnvironmentAssessment)
    recommended_actions: list[str] = Field(default_factory=list)
    tool_calls: list[ToolRequest] = Field(default_factory=list)
    public_warning: str | None = None
    reasoning_summary: str
    errors: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=utc_now)


class TimelineEvent(BaseModel):
    id: str
    timestamp: str = Field(default_factory=utc_now)
    category: str
    message: str
    camera_id: str | None = None
    severity: str | None = None
    details: dict = Field(default_factory=dict)


class IoTDeviceTelemetry(BaseModel):
    device_id: str
    device_type: Literal["edge_vision_buoy", "wearable_submersion_tracker", "sonar_pod", "drone_scout"]
    zone: str = "Zone 1 (Deerfield Pier)"
    latitude: float = 26.31656
    longitude: float = -80.07560
    submersion_seconds: float = 0.0
    heart_rate_bpm: int | None = None
    battery_pct: int = 100
    signal_rssi_dbm: int = -65
    protocol: Literal["lorawan", "mqtt", "cellular_nbiot"] = "lorawan"
    raw_payload_hex: str | None = None
    alert_status: Literal["normal", "submerged_warning", "drowning_critical", "heartrate_distress"] = "normal"
    timestamp: str = Field(default_factory=utc_now)


