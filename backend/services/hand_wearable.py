from __future__ import annotations

import struct
from typing import Any
from backend.models import utc_now
from backend.state import AppState

# BLE GATT Service and Characteristic UUID Specifications for Lifeguard Hand Embedded Units
GATT_SPEC = {
    "service_uuid": "0000FA10-0000-1000-8000-00805F9B34FB",
    "name": "Lifeguard Hand Wearable & Tactical Glove Service",
    "characteristics": {
        "telemetry": {
            "uuid": "0000FA11-0000-1000-8000-00805F9B34FB",
            "properties": ["READ", "NOTIFY"],
            "byte_format": ">HHBBBBh",
            "c_struct": "struct __attribute__((packed)) {\n    uint16_t depth_hpa;\n    uint16_t submersion_ms;\n    uint8_t  heart_rate;\n    uint8_t  battery_pct;\n    uint8_t  motion_state;\n    uint8_t  flags;\n    int16_t  rssi;\n};",
            "description": "Hand depth pressure, submersion timer, vitals, accelerometer state, skin contact",
        },
        "haptic_control": {
            "uuid": "0000FA12-0000-1000-8000-00805F9B34FB",
            "properties": ["WRITE", "WRITE_WITHOUT_RESPONSE"],
            "byte_format": ">BBHH",
            "c_struct": "struct __attribute__((packed)) {\n    uint8_t pattern_id;\n    uint8_t motor_intensity_pct;\n    uint16_t duration_ms;\n    uint16_t frequency_hz;\n};",
            "description": "Triggers ERM/LRA haptic vibration motor on lifeguard's hand/wrist",
        },
        "gesture_input": {
            "uuid": "0000FA13-0000-1000-8000-00805F9B34FB",
            "properties": ["NOTIFY"],
            "byte_format": ">B",
            "c_struct": "uint8_t gesture_code; // 0x01: Palm Squeeze SOS, 0x02: Double Tap Whistle, 0x03: Wave Ack",
            "description": "Hand gesture inputs (palm squeeze, double tap, wave acknowledge)",
        },
    },
}

# C Header definitions for microcontrollers (nRF52840, STM32, ESP32-S3)
C_HEADER_CODE = """/*
 * Baywatch AI - Lifeguard Hand Embedded Hardware Protocol Header
 * Target: Nordic nRF52840, STM32 Marine SoCs, ESP32-S3
 * Service UUID: 0000FA10-0000-1000-8000-00805F9B34FB
 */

#ifndef LIFEGUARD_HAND_PROTOCOL_H
#define LIFEGUARD_HAND_PROTOCOL_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Motion States
#define MOTION_IDLE         0x00
#define MOTION_PATROL       0x01
#define MOTION_SWIMMING     0x02
#define MOTION_PANIC_THRASH 0x03
#define MOTION_IMMOBILE     0x04

// Hand Gesture Codes
#define GESTURE_NONE               0x00
#define GESTURE_PALM_SQUEEZE_SOS   0x01
#define GESTURE_DOUBLE_TAP_WHISTLE 0x02
#define GESTURE_WAVE_ACKNOWLEDGE   0x03

// Haptic Pattern IDs for Hand Motor
#define HAPTIC_PATTERN_TICK          0x01
#define HAPTIC_PATTERN_DOUBLE_PULSE  0x02
#define HAPTIC_PATTERN_WARNING_BURST 0x03
#define HAPTIC_PATTERN_SOS_EMERGENCY 0x04

// C Telemetry Payload Struct (7 Bytes Packed)
typedef struct __attribute__((packed)) {
    uint16_t depth_hpa;        // Hydrostatic pressure (hPa)
    uint16_t submersion_ms;   // Submersion timer (milliseconds)
    uint8_t  heart_rate;       // Pulse rate (BPM)
    uint8_t  battery_pct;      // Battery level (0-100%)
    uint8_t  motion_state;     // Motion state code
} HandTelemetryPayload_t;

// C Haptic Control Packet (6 Bytes Packed)
typedef struct __attribute__((packed)) {
    uint8_t  pattern_id;           // Target haptic rhythm
    uint8_t  motor_intensity_pct;  // Motor PWM duty cycle (0-100%)
    uint16_t duration_ms;          // Pulse sequence duration
    uint16_t frequency_hz;         // Resonant frequency (LRA)
} HandHapticCommand_t;

#ifdef __cplusplus
}
#endif

#endif // LIFEGUARD_HAND_PROTOCOL_H
"""


class HandWearableService:
    def __init__(self) -> None:
        self.hand_devices: dict[str, dict[str, Any]] = {
            "HAND-GUARD-01": {
                "device_id": "HAND-GUARD-01",
                "name": "Lifeguard Tactical Glove / Hand Node #1",
                "guard_name": "Guard Jordan",
                "location": "Shoreline Sector A",
                "depth_hpa": 1013,  # Sea level atmospheric pressure
                "submersion_seconds": 0.0,
                "heart_rate_bpm": 76,
                "battery_pct": 92,
                "motion_state": "PATROL",
                "last_gesture": "NONE",
                "last_haptic_sent": "HAPTIC_PATTERN_TICK",
                "signal_rssi_dbm": -52,
                "last_seen": utc_now(),
            }
        }

    def decode_binary_telemetry(self, raw_hex: str) -> dict[str, Any]:
        """
        Decodes a 7-byte binary telemetry packet from a hand-embedded device:
        - Bytes 0-1: Hydrostatic pressure (uint16 hPa)
        - Bytes 2-3: Submersion time in ms (uint16)
        - Byte 4: Heart rate (uint8)
        - Byte 5: Battery % (uint8)
        - Byte 6: Motion state (uint8)
        """
        try:
            raw_bytes = bytes.fromhex(raw_hex)
            if len(raw_bytes) < 7:
                return {}
            hpa, sub_ms, hr, bat, motion_code = struct.unpack(">HHBBB", raw_bytes[:7])
            motion_map = {0: "IDLE", 1: "PATROL", 2: "SWIMMING", 3: "PANIC_THRASH", 4: "IMMOBILE"}

            return {
                "depth_hpa": hpa,
                "submersion_seconds": round(sub_ms / 1000.0, 2),
                "heart_rate_bpm": hr,
                "battery_pct": bat,
                "motion_state": motion_map.get(motion_code, "IDLE"),
            }
        except Exception:
            return {}

    def process_telemetry(self, state: AppState, device_id: str, telemetry: dict[str, Any]) -> dict[str, Any]:
        device = self.hand_devices.get(device_id, {
            "device_id": device_id,
            "name": f"Hand Device {device_id}",
            "guard_name": "Patrol Guard",
            "location": "Shoreline Sector B",
        })

        raw_hex = telemetry.get("raw_hex")
        if raw_hex:
            decoded = self.decode_binary_telemetry(raw_hex)
            telemetry.update(decoded)

        device.update({
            "depth_hpa": telemetry.get("depth_hpa", device.get("depth_hpa", 1013)),
            "submersion_seconds": telemetry.get("submersion_seconds", device.get("submersion_seconds", 0.0)),
            "heart_rate_bpm": telemetry.get("heart_rate_bpm", device.get("heart_rate_bpm", 76)),
            "battery_pct": telemetry.get("battery_pct", device.get("battery_pct", 95)),
            "motion_state": telemetry.get("motion_state", device.get("motion_state", "PATROL")),
            "signal_rssi_dbm": telemetry.get("signal_rssi_dbm", device.get("signal_rssi_dbm", -55)),
            "last_seen": utc_now(),
        })
        self.hand_devices[device_id] = device

        # Check for guard distress or extended submersion
        if device["submersion_seconds"] > 15.0 or device["motion_state"] == "PANIC_THRASH":
            alert_msg = f"HAND EMBEDDED DISTRESS ALERT ({device['name']} - {device['guard_name']}): {device['submersion_seconds']}s submersion or panic motion detected on hand sensor."
            state.alerts.insert(0, {
                "id": f"hand-alert-{device_id}",
                "camera_id": "camera_live",
                "acknowledged": False,
                "type": "hand_device_distress",
                "severity": "critical",
                "description": alert_msg,
                "evidence": [
                    f"Lifeguard Hand Node: {device['name']} ({device['guard_name']})",
                    f"Submersion Duration: {device['submersion_seconds']} sec",
                    f"Motion State: {device['motion_state']}",
                    f"Vitals: {device['heart_rate_bpm']} BPM",
                ],
                "confidence": 0.98,
                "created_at": utc_now(),
            })
            state.publish("hand_device", alert_msg, camera_id="camera_live", severity="critical")

        return {"status": "success", "device": device}

    def trigger_haptic(self, device_id: str, pattern_id: str, intensity: int = 100, duration_ms: int = 500) -> dict[str, Any]:
        device = self.hand_devices.get(device_id)
        if not device:
            device = list(self.hand_devices.values())[0]

        device["last_haptic_sent"] = pattern_id
        return {
            "success": True,
            "device_id": device["device_id"],
            "pattern_id": pattern_id,
            "intensity_pct": intensity,
            "duration_ms": duration_ms,
            "haptic_payload_hex": f"03{intensity:02X}{duration_ms:04X}",
            "message": f"Haptic pulse '{pattern_id}' dispatched to lifeguard hand motor",
        }

    def process_gesture(self, state: AppState, device_id: str, gesture_code: str) -> dict[str, Any]:
        device = self.hand_devices.get(device_id)
        if not device:
            device = list(self.hand_devices.values())[0]

        device["last_gesture"] = gesture_code

        if gesture_code == "PALM_SQUEEZE_SOS":
            state.escalation = {
                "camera_id": "camera_live",
                "severity": "critical",
                "reason": f"Emergency Palm Squeeze SOS triggered from lifeguard hand device ({device['guard_name']})",
                "status": "palm_sos_triggered",
            }
            state.publish("hand_device", f"GESTURE ACTION: Emergency Palm Squeeze SOS triggered by {device['guard_name']} from hand device", severity="critical")
            return {"success": True, "gesture": gesture_code, "action": "emergency_sos_triggered"}

        elif gesture_code == "DOUBLE_TAP_WHISTLE":
            state.warning = {
                "camera_id": "camera_live",
                "message": "Attention beachgoers: please return to shore immediately.",
                "issued": True,
            }
            state.publish("hand_device", f"GESTURE ACTION: Double-tap whistle announcement triggered by {device['guard_name']} from hand device")
            return {"success": True, "gesture": gesture_code, "action": "whistle_announced"}

        elif gesture_code == "WAVE_ACKNOWLEDGE":
            active = [a for a in state.alerts if not a.get("acknowledged")]
            if active:
                state.acknowledge(active[0]["id"])
                state.publish("hand_device", f"GESTURE ACTION: Alert acknowledged via hand wave gesture by {device['guard_name']}")
                return {"success": True, "gesture": gesture_code, "action": "alert_acknowledged", "alert_id": active[0]["id"]}
            return {"success": True, "gesture": gesture_code, "action": "no_active_alert"}

        return {"success": False, "error": f"Unknown gesture code: {gesture_code}"}


hand_service = HandWearableService()
