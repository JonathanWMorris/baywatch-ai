from backend.app import create_app
from backend.state import state


def test_watch_status_endpoint():
    client = create_app(testing=True).test_client()
    response = client.get("/api/watch/status")
    assert response.status_code == 200
    data = response.json
    assert "device_target" in data
    assert "risk_level" in data
    assert "haptic_profile" in data
    assert "quick_actions" in data
    assert len(data["quick_actions"]) >= 4


def test_watch_action_acknowledge():
    client = create_app(testing=True).test_client()
    # Post a dummy alert into state
    state.alerts.insert(0, {
        "id": "alert-watch-123",
        "camera_id": "camera_live",
        "acknowledged": False,
        "type": "rip_current",
        "severity": "high",
        "description": "Watch test alert",
    })
    response = client.post("/api/watch/action", json={"action": "acknowledge_alert", "alert_id": "alert-watch-123"})
    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["alert_id"] == "alert-watch-123"


def test_watch_action_whistle_and_dispatch():
    client = create_app(testing=True).test_client()
    resp_whistle = client.post("/api/watch/action", json={"action": "trigger_whistle", "details": {"message": "Swimmers return to shore"}})
    assert resp_whistle.status_code == 200
    assert resp_whistle.json["success"] is True

    resp_dispatch = client.post("/api/watch/action", json={"action": "dispatch_guard", "details": {"guard": "Patrol Unit 3"}})
    assert resp_dispatch.status_code == 200
    assert resp_dispatch.json["success"] is True


def test_watch_haptics_endpoint():
    client = create_app(testing=True).test_client()
    response = client.get("/api/watch/haptics")
    assert response.status_code == 200
    assert "critical" in response.json["haptic_profiles"]
    assert "pattern" in response.json["haptic_profiles"]["critical"]
