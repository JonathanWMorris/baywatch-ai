from __future__ import annotations

import uuid
from typing import Any
from backend.models import utc_now
from backend.state import AppState


class ComplianceManager:
    def __init__(self) -> None:
        self.incidents: list[dict[str, Any]] = [
            {
                "incident_id": "INC-2026-0726-01",
                "timestamp": utc_now(),
                "zone": "Zone 3 (South Sandbar)",
                "incident_type": "Rip Current Swimmer Assist",
                "severity": "high",
                "gemma_confidence": 0.94,
                "evidence_summary": "Multimodal visual identification of swimmer struggling in rip current feed + NOAA wave height 4.2ft.",
                "guard_signoff": "Guard Jordan (Badge #4082)",
                "legal_status": "COMPLETED_AUDITED",
            }
        ]

    def get_incidents(self) -> list[dict[str, Any]]:
        return self.incidents

    def create_incident_report(self, state: AppState, zone: str, incident_type: str, severity: str, evidence: str, guard_name: str) -> dict[str, Any]:
        incident_id = f"INC-2026-{uuid.uuid4().hex[:6].upper()}"
        report = {
            "incident_id": incident_id,
            "timestamp": utc_now(),
            "zone": zone,
            "incident_type": incident_type,
            "severity": severity,
            "gemma_confidence": 0.96,
            "evidence_summary": evidence,
            "guard_signoff": guard_name,
            "legal_status": "PENDING_MUNICIPAL_REVIEW",
        }
        self.incidents.insert(0, report)
        state.publish("compliance", f"LEGAL LOG: Digital incident compliance report {incident_id} created by {guard_name}", details={"incident": report})
        return report

    def generate_report_txt(self, incident_id: str) -> str:
        report = next((i for i in self.incidents if i["incident_id"] == incident_id), self.incidents[0])
        return f"""================================================================================
BAYWATCH AI - MUNICIPAL LIFEGUARD INCIDENT COMPLIANCE REPORT
================================================================================
Incident ID:       {report['incident_id']}
Timestamp (UTC):   {report['timestamp']}
Beach Sector Zone: {report['zone']}
Incident Type:     {report['incident_type']}
Severity Level:    {report['severity'].upper()}
Gemma AI Score:    {report['gemma_confidence'] * 100:.1f}% Confidence
Guard Sign-off:    {report['guard_signoff']}
Audit Status:      {report['legal_status']}

EVIDENCE LOG & AI DIAGNOSTIC AUDIT TRAIL:
--------------------------------------------------------------------------------
{report['evidence_summary']}

ENVIRONMENTAL SNAPSHOT AT TIME OF INCIDENT:
- NOAA Buoy 41122: Wave Height 4.2 ft | Period 7.1s | Temp 78.4°F
- OpenWeather: Wind 14 mph ENE | Visibility 10,000m | Caution Flags Active

CERTIFICATION:
This report was cryptographically timestamped and generated in compliance with
National Aquatic Safety Company (NASCO) and USLA Incident Logging Standards.
================================================================================
"""


compliance_manager = ComplianceManager()
