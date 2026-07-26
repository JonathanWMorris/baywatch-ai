from __future__ import annotations

from backend.models import Assessment
from backend.state import AppState

ALLOWED_TOOLS = {
    "alert_lifeguard", "generate_public_warning", "request_emergency_escalation",
}

TOOL_SCHEMAS = [
    {"name": "alert_lifeguard", "description": "Display a lifeguard attention alert.", "parameters": {"type": "object", "properties": {"camera_id": {"type": "string"}, "severity": {"type": "string"}, "message": {"type": "string"}}, "required": ["camera_id", "severity", "message"]}},
    {"name": "generate_public_warning", "description": "Prepare a short public safety announcement for human approval.", "parameters": {"type": "object", "properties": {"camera_id": {"type": "string"}, "hazard": {"type": "string"}, "message": {"type": "string"}}, "required": ["camera_id", "hazard", "message"]}},
    {"name": "request_emergency_escalation", "description": "Recommend, but never automatically contact, emergency services.", "parameters": {"type": "object", "properties": {"camera_id": {"type": "string"}, "severity": {"type": "string"}, "reason": {"type": "string"}}, "required": ["camera_id", "severity", "reason"]}},
]


def execute_assessment_tools(assessment: Assessment, state: AppState) -> list[dict]:
    requested = list(assessment.tool_calls)
    # recommended_actions is a resilient fallback when the model emitted valid JSON but
    # omitted the richer tool_calls field.
    for action in assessment.recommended_actions:
        if action in ALLOWED_TOOLS and not any(item.name == action for item in requested):
            requested.append(type("Request", (), {"name": action, "arguments": {}})())

    results = []
    for request in requested:
        if request.name not in ALLOWED_TOOLS:
            state.publish("tool_error", f"Blocked unknown tool: {request.name}", camera_id=assessment.camera_id)
            continue
        args = dict(request.arguments)
        args.setdefault("camera_id", assessment.camera_id)
        if request.name == "alert_lifeguard":
            args.setdefault("severity", assessment.risk_level)
            args.setdefault("message", assessment.reasoning_summary)
            result = {"status": "lifeguard_alert_created"}
        elif request.name == "generate_public_warning":
            message = args.get("message") or assessment.public_warning
            if message:
                state.warning = {"camera_id": assessment.camera_id, "message": message, "issued": False}
            result = {"status": "warning_prepared", "requires_operator": True}
        else:
            state.escalation = {
                "camera_id": assessment.camera_id, "severity": args.get("severity", assessment.risk_level),
                "reason": args.get("reason", assessment.reasoning_summary), "status": "recommended",
            }
            result = {"status": "escalation_recommended", "requires_operator": True}
        state.publish("tool", f"Gemma tool: {request.name}", camera_id=assessment.camera_id, details={"arguments": args, "result": result})
        results.append({"name": request.name, "arguments": args, "result": result})
    return results

