from backend.app import create_app


def test_health_starts_without_loading_model():
    client = create_app(testing=True).test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["live"]["dependencies"]["ready"] is True
    assert response.json["live"]["dependencies"]["python_executable"]


def test_cors_accepts_both_local_development_hosts():
    client = create_app(testing=True).test_client()
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = client.get("/api/health", headers={"Origin": origin})
        assert response.headers["Access-Control-Allow-Origin"] == origin


def test_cors_rejects_unconfigured_origin():
    client = create_app(testing=True).test_client()
    response = client.get("/api/health", headers={"Origin": "https://example.com"})
    assert "Access-Control-Allow-Origin" not in response.headers


def test_status_is_single_camera_with_deerfield_risk():
    client = create_app(testing=True).test_client()
    response = client.get("/api/status")
    assert len(response.json["cameras"]) == 1
    camera = response.json["cameras"][0]
    assert camera["id"] == "camera_live"
    assert camera["source_type"] == "youtube"
    assert response.json["live"]["environment_mode"] == "sensor_fusion"
    assert response.json["ocean"]["station_id"] == "41122"
    assert response.json["ocean_risk_assessment"]["risk_level"] != "unknown"


def test_removed_scenario_and_upload_routes_are_not_available():
    client = create_app(testing=True).test_client()
    assert client.get("/api/demo/scenarios").status_code == 404
    assert client.post("/api/analyze").status_code == 404


def test_live_control_routes(monkeypatch):
    client = create_app(testing=True).test_client()
    monkeypatch.setattr("backend.app.live_manager.start", lambda: True)
    monkeypatch.setattr("backend.app.live_manager.stop", lambda: True)
    assert client.post("/api/live/start").json["started"] is True
    assert client.post("/api/live/stop").json["was_running"] is True


def test_live_start_reports_missing_dependency(monkeypatch):
    client = create_app(testing=True).test_client()
    missing = {
        "ready": False,
        "yt_dlp": False,
        "av": True,
        "python_executable": "/wrong/python",
        "install_command": "install dependencies",
    }
    monkeypatch.setattr("backend.app.live_manager.preflight", lambda: missing)
    monkeypatch.setattr(
        "backend.app.live_manager.status",
        lambda: {"error": "Live capture dependencies missing: yt_dlp"},
    )
    response = client.post("/api/live/start")
    assert response.status_code == 503
    assert response.json["dependencies"]["yt_dlp"] is False


def test_emergency_requires_confirmation():
    client = create_app(testing=True).test_client()
    assert client.post(
        "/api/emergency/escalate", json={"confirmed": False}
    ).status_code == 400
    response = client.post(
        "/api/emergency/escalate",
        json={"confirmed": True, "camera_id": "camera_live"},
    )
    assert response.json["real_emergency_services_contacted"] is False
