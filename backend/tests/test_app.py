import io
from backend.app import create_app
from backend.models import Assessment, EnvironmentAssessment, HazardEvent, ToolRequest

def test_health_starts_without_loading_model():
    client = create_app(testing=True).test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"

def test_analysis_reaches_alert_and_tool_timeline(monkeypatch):
    assessment = Assessment(
        camera_id="camera_2", risk_level="high",
        events=[HazardEvent(type="possible_swimmer_distress", severity="high", description="Repeated submersion observed.", evidence=["repeated submersion"], confidence=.84)],
        environment=EnvironmentAssessment(risk_level="high", summary="Elevated ocean risk."),
        recommended_actions=["alert_lifeguard"],
        tool_calls=[ToolRequest(name="alert_lifeguard", arguments={"severity": "high", "message": "Review camera 2"})],
        public_warning="Attention. Please exit the water near Tower 2 and follow lifeguard instructions.",
        reasoning_summary="Repeated submersion was observed during elevated surf conditions.",
    )
    monkeypatch.setattr("backend.app.gemma.analyze", lambda *args, **kwargs: assessment)
    monkeypatch.setattr("backend.app.get_buoy_conditions", lambda *args, **kwargs: {"is_mock": True})
    monkeypatch.setattr("backend.app.get_weather_conditions", lambda *args, **kwargs: {"is_mock": True})
    client = create_app(testing=True).test_client()
    response = client.post("/api/analyze", data={"camera_id": "camera_2", "video": (io.BytesIO(b"video"), "clip.mp4")})
    assert response.status_code == 200
    assert response.json["assessment"]["risk_level"] == "high"
    snapshot = client.get("/api/status").json
    assert any(alert["type"] == "possible_swimmer_distress" for alert in snapshot["alerts"])
    assert any(event["category"] == "tool" for event in snapshot["events"])

def test_emergency_requires_confirmation():
    client = create_app(testing=True).test_client()
    assert client.post("/api/emergency/escalate", json={"confirmed": False}).status_code == 400
    response = client.post("/api/emergency/escalate", json={"confirmed": True, "camera_id": "camera_2"})
    assert response.json["real_emergency_services_contacted"] is False

