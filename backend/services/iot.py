from __future__ import annotations

import struct
from typing import Any
from backend.models import IoTDeviceTelemetry, utc_now
from backend.state import AppState


INITIAL_DEVICES = [
    {
        "device_id": "EDGE-BUOY-01",
        "name": "Deerfield Pier Edge AI Camera Buoy",
        "device_type": "edge_vision_buoy",
        "zone": "Zone 1 (Deerfield Pier)",
        "protocol": "lorawan",
        "status": "online",
        "submersion_seconds": 0.0,
        "battery_pct": 94,
        "signal_rssi_dbm": -68,
        "alert_status": "normal",
        "firmware": "v2.4.1-edge-yolo",
        "last_seen": utc_now(),
    },
    {
        "device_id": "WEARABLE-TRACKER-04",
        "name": "Lifeguard Swimmer Wristband Tracker #4",
        "device_type": "wearable_submersion_tracker",
        "zone": "Zone 2 (North Patrol)",
        "protocol": "mqtt",
        "status": "online",
        "submersion_seconds": 0.0,
        "heart_rate_bpm": 82,
        "battery_pct": 88,
        "signal_rssi_dbm": -55,
        "alert_status": "normal",
        "firmware": "v1.8.0-wear-submersion",
        "last_seen": utc_now(),
    },
    {
        "device_id": "SONAR-POD-02",
        "name": "Subsurface Acoustic Drowning Sonar",
        "device_type": "sonar_pod",
        "zone": "Zone 1 (Deep Water)",
        "protocol": "cellular_nbiot",
        "status": "online",
        "submersion_seconds": 0.0,
        "battery_pct": 98,
        "signal_rssi_dbm": -72,
        "alert_status": "normal",
        "firmware": "v3.1.0-sonar-pulse",
        "last_seen": utc_now(),
    },
]


def decode_lorawan_hex_payload(hex_str: str) -> dict[str, Any]:
    """
    Decodes a compact 5-byte LoRaWAN binary payload:
    Byte 0: Device Type (0x01: Wearable Tracker, 0x02: Edge Buoy, 0x03: Sonar)
    Byte 1: Submersion time in seconds (uint8)
    Byte 2: Heart rate in BPM (uint8)
    Byte 3: Battery percentage (uint8)
    Byte 4: Alert status code (0x00: Normal, 0x01: Submerged Warning, 0x02: Drowning Critical)
    """
    try:
        raw_bytes = bytes.fromhex(hex_str)
        if len(raw_bytes) < 5:
            return {}
        dev_type_byte, submersion, hr, battery, status_byte = struct.unpack(">BBBBB", raw_bytes[:5])
        type_map = {1: "wearable_submersion_tracker", 2: "edge_vision_buoy", 3: "sonar_pod"}
        status_map = {0: "normal", 1: "submerged_warning", 2: "drowning_critical", 3: "heartrate_distress"}

        return {
            "device_type": type_map.get(dev_type_byte, "wearable_submersion_tracker"),
            "submersion_seconds": float(submersion),
            "heart_rate_bpm": hr if hr > 0 else None,
            "battery_pct": battery,
            "alert_status": status_map.get(status_byte, "normal"),
        }
    except Exception:
        return {}


class IoTManager:
    def __init__(self) -> None:
        self.devices: dict[str, dict[str, Any]] = {d["device_id"]: dict(d) for d in INITIAL_DEVICES}
        self.telemetry_history: list[dict[str, Any]] = []

    def get_devices(self) -> list[dict[str, Any]]:
        return list(self.devices.values())

    def ingest_telemetry(self, state: AppState, telemetry: IoTDeviceTelemetry) -> dict[str, Any]:
        data = telemetry.model_dump()
        if telemetry.raw_payload_hex:
            decoded = decode_lorawan_hex_payload(telemetry.raw_payload_hex)
            data.update({k: v for k, v in decoded.items() if v is not None})

        device_id = data["device_id"]
        device = self.devices.get(device_id, {
            "device_id": device_id,
            "name": f"Embedded Device {device_id}",
            "firmware": "v1.0.0-embedded",
        })

        device.update({
            "device_type": data["device_type"],
            "zone": data["zone"],
            "protocol": data["protocol"],
            "status": "online",
            "submersion_seconds": data["submersion_seconds"],
            "heart_rate_bpm": data.get("heart_rate_bpm"),
            "battery_pct": data["battery_pct"],
            "signal_rssi_dbm": data["signal_rssi_dbm"],
            "alert_status": data["alert_status"],
            "last_seen": utc_now(),
        })
        self.devices[device_id] = device
        self.telemetry_history.insert(0, data)

        # Trigger lifeguard alert if drowning or submersion warning is detected by the embedded node
        if data["alert_status"] in {"submerged_warning", "drowning_critical"}:
            severity = "critical" if data["alert_status"] == "drowning_critical" or data["submersion_seconds"] > 15 else "high"
            submersion_info = f"{data['submersion_seconds']:.1f}s submersion" if data["submersion_seconds"] > 0 else "distress motion pattern"

            alert_desc = f"EMBEDDED HARDWARE ALERT ({device['name']} - {data['zone']}): {submersion_info} detected via {data['protocol'].upper()} sensor node."

            state.alerts.insert(0, {
                "id": f"iot-alert-{device_id}",
                "camera_id": "camera_live",
                "acknowledged": False,
                "type": "iot_drowning_telemetry",
                "severity": severity,
                "description": alert_desc,
                "evidence": [
                    f"Sensor: {device['name']}",
                    f"Submersion Duration: {data['submersion_seconds']} sec",
                    f"Heart Rate: {data.get('heart_rate_bpm', 'N/A')} BPM",
                    f"Protocol: {data['protocol'].upper()} (RSSI: {data['signal_rssi_dbm']} dBm)",
                    f"Zone: {data['zone']}",
                ],
                "confidence": 0.96,
                "created_at": utc_now(),
            })

            state.publish(
                "iot",
                f"EMBEDDED IOT ALERT: {device['name']} triggered {data['alert_status'].upper()}",
                camera_id="camera_live",
                severity=severity,
                details={"telemetry": data},
            )

        return {"status": "processed", "device": device, "telemetry": data}

    def simulate_event(self, state: AppState, device_id: str, alert_type: str) -> dict[str, Any]:
        if device_id not in self.devices:
            device_id = "WEARABLE-TRACKER-04"

        device = self.devices[device_id]
        submersion = 24.0 if alert_type == "drowning_critical" else 12.0
        alert_status = "drowning_critical" if alert_type == "drowning_critical" else "submerged_warning"

        telemetry = IoTDeviceTelemetry(
            device_id=device_id,
            device_type=device["device_type"],
            zone=device["zone"],
            submersion_seconds=submersion,
            heart_rate_bpm=145 if alert_type == "drowning_critical" else 110,
            battery_pct=device["battery_pct"],
            signal_rssi_dbm=-62,
            protocol=device["protocol"],
            raw_payload_hex="0118916402",  # Demo compact binary packet
            alert_status=alert_status,
        )
        return self.ingest_telemetry(state, telemetry)


iot_manager = IoTManager()
