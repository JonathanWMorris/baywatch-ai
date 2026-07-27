from backend.app import create_app
from backend.services.iot import decode_lorawan_hex_payload


def test_lorawan_hex_payload_decoder():
    # Byte 0: 0x01 (wearable), Byte 1: 22 (submersion 22s), Byte 2: 120 (120 BPM), Byte 3: 95 (95% battery), Byte 4: 0x02 (drowning_critical)
    payload_hex = "0116785f02"
    decoded = decode_lorawan_hex_payload(payload_hex)
    assert decoded["device_type"] == "wearable_submersion_tracker"
    assert decoded["submersion_seconds"] == 22.0
    assert decoded["heart_rate_bpm"] == 120
    assert decoded["battery_pct"] == 95
    assert decoded["alert_status"] == "drowning_critical"


def test_iot_devices_list_endpoint():
    client = create_app(testing=True).test_client()
    response = client.get("/api/iot/devices")
    assert response.status_code == 200
    data = response.json
    assert "devices" in data
    assert len(data["devices"]) >= 3


def test_iot_telemetry_ingestion_endpoint():
    client = create_app(testing=True).test_client()
    payload = {
        "device_id": "WEARABLE-TRACKER-04",
        "device_type": "wearable_submersion_tracker",
        "zone": "Zone 2 (North Patrol)",
        "submersion_seconds": 18.5,
        "heart_rate_bpm": 138,
        "battery_pct": 82,
        "signal_rssi_dbm": -58,
        "protocol": "mqtt",
        "alert_status": "drowning_critical",
    }
    response = client.post("/api/iot/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json["status"] == "processed"
    assert response.json["device"]["alert_status"] == "drowning_critical"


def test_iot_simulation_endpoint():
    client = create_app(testing=True).test_client()
    response = client.post("/api/iot/simulate", json={"device_id": "EDGE-BUOY-01", "alert_type": "submerged_warning"})
    assert response.status_code == 200
    assert response.json["status"] == "processed"
