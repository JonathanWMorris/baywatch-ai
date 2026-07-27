from backend.app import create_app


def test_tower_grid_endpoints():
    client = create_app(testing=True).test_client()
    res = client.get("/api/towers")
    assert res.status_code == 200
    assert len(res.json["towers"]) >= 4

    update_res = client.post("/api/towers/TOWER-03/risk", json={"risk_level": "critical"})
    assert update_res.status_code == 200
    assert update_res.json["risk_level"] == "critical"


def test_drone_dispatch_endpoints():
    client = create_app(testing=True).test_client()
    status_res = client.get("/api/drone/status")
    assert status_res.status_code == 200
    assert "drones" in status_res.json

    dispatch_res = client.post("/api/drone/dispatch", json={"drone_id": "RESCUE-DRONE-01", "latitude": 26.3152, "longitude": -80.0758, "zone": "Zone 3"})
    assert dispatch_res.status_code == 200
    assert dispatch_res.json["success"] is True

    drop_res = client.post("/api/drone/drop-buoy", json={"drone_id": "RESCUE-DRONE-01"})
    assert drop_res.status_code == 200
    assert drop_res.json["drone"]["payload_status"] == "buoy_dropped"


def test_thermal_status_and_config():
    client = create_app(testing=True).test_client()
    res = client.get("/api/thermal/status")
    assert res.status_code == 200

    cfg_res = client.post("/api/thermal/config", json={"enabled": True, "palette": "plasma", "contrast": 90})
    assert cfg_res.status_code == 200
    assert cfg_res.json["palette"] == "plasma"


def test_mesh_status():
    client = create_app(testing=True).test_client()
    res = client.get("/api/mesh/status")
    assert res.status_code == 200
    assert res.json["mesh_active"] is True
    assert len(res.json["nodes"]) >= 3


def test_compliance_report_and_export():
    client = create_app(testing=True).test_client()
    incidents_res = client.get("/api/compliance/incidents")
    assert incidents_res.status_code == 200

    create_res = client.post("/api/compliance/report", json={
        "zone": "Zone 1",
        "incident_type": "Swimmer Rescue",
        "severity": "critical",
        "evidence": "Swimmer submersion timer > 20s",
        "guard_name": "Guard Jordan",
    })
    assert create_res.status_code == 200
    incident_id = create_res.json["incident_id"]

    export_res = client.get(f"/api/compliance/export/{incident_id}")
    assert export_res.status_code == 200
    assert "MUNICIPAL LIFEGUARD INCIDENT COMPLIANCE REPORT" in export_res.text


def test_siren_and_handover_endpoints():
    client = create_app(testing=True).test_client()
    siren_res = client.post("/api/siren/trigger", json={"mode": "evacuate_beach", "operator": "Guard Jordan"})
    assert siren_res.status_code == 200
    assert siren_res.json["strobe_active"] is True

    handover_res = client.post("/api/handover/rotate", json={"incoming_guard": "Guard Sarah", "notes": "Shift rotation completed"})
    assert handover_res.status_code == 200
    assert handover_res.json["shift"]["current_guard"] == "Guard Sarah"
