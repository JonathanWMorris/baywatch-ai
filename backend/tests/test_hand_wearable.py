from backend.app import create_app
from backend.services.hand_wearable import hand_service


def test_hand_wearable_gatt_spec_endpoint():
    client = create_app(testing=True).test_client()
    response = client.get("/api/hand-wearable/gatt-spec")
    assert response.status_code == 200
    data = response.json
    assert "service_uuid" in data
    assert "telemetry" in data["characteristics"]


def test_hand_wearable_binary_decoder():
    # 1013 hPa = 0x03F5, 1200ms = 0x04B0, HR=80, Battery=90, Motion=0x03 (PANIC_THRASH)
    hex_payload = "03F504B0505A03"
    decoded = hand_service.decode_binary_telemetry(hex_payload)
    assert decoded["depth_hpa"] == 1013
    assert decoded["submersion_seconds"] == 1.2
    assert decoded["heart_rate_bpm"] == 80
    assert decoded["battery_pct"] == 90
    assert decoded["motion_state"] == "PANIC_THRASH"


def test_hand_wearable_haptic_trigger():
    client = create_app(testing=True).test_client()
    response = client.post("/api/hand-wearable/haptic-trigger", json={
        "device_id": "HAND-GUARD-01",
        "pattern_id": "HAPTIC_PATTERN_WARNING_BURST",
        "intensity_pct": 90,
    })
    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["pattern_id"] == "HAPTIC_PATTERN_WARNING_BURST"


def test_hand_wearable_gesture_action():
    client = create_app(testing=True).test_client()
    resp_whistle = client.post("/api/hand-wearable/gesture-action", json={
        "device_id": "HAND-GUARD-01",
        "gesture_code": "DOUBLE_TAP_WHISTLE",
    })
    assert resp_whistle.status_code == 200
    assert resp_whistle.json["success"] is True

    resp_sos = client.post("/api/hand-wearable/gesture-action", json={
        "device_id": "HAND-GUARD-01",
        "gesture_code": "PALM_SQUEEZE_SOS",
    })
    assert resp_sos.status_code == 200
    assert resp_sos.json["action"] == "emergency_sos_triggered"


def test_hand_embedded_header_endpoint():
    client = create_app(testing=True).test_client()
    response = client.get("/api/hand-wearable/embedded-header.h")
    assert response.status_code == 200
    assert "LIFEGUARD_HAND_PROTOCOL_H" in response.text
