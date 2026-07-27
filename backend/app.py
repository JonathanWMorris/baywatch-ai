from __future__ import annotations

import json
import logging
import os
import time

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

from backend.models import IoTDeviceTelemetry
from backend.services.compliance import compliance_manager
from backend.services.drone import drone_manager
from backend.services.gemma import gemma
from backend.services.hand_wearable import C_HEADER_CODE, GATT_SPEC, hand_service
from backend.services.handover import handover_manager
from backend.services.iot import iot_manager
from backend.services.live import live_manager
from backend.services.mesh import mesh_manager
from backend.services.ocean import get_buoy_conditions
from backend.services.risk import assess_ocean_risk
from backend.services.siren import siren_manager
from backend.services.thermal import thermal_service
from backend.services.towers import tower_manager
from backend.services.weather import get_weather_conditions
from backend.services.watch import HAPTIC_PATTERNS, get_watch_status, handle_watch_action
from backend.state import state

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(TESTING=testing, MAX_CONTENT_LENGTH=250 * 1024 * 1024)

    @app.after_request
    def cors(response):
        configured_origins = os.getenv("FRONTEND_ORIGINS")
        if configured_origins is None:
            configured_origins = os.getenv(
                "FRONTEND_ORIGIN",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        allowed_origins = {
            origin.strip() for origin in configured_origins.split(",") if origin.strip()
        }
        # Existing installations used a singular local origin. Treat localhost
        # and 127.0.0.1 as paired aliases without widening non-local origins.
        if "http://localhost:5173" in allowed_origins:
            allowed_origins.add("http://127.0.0.1:5173")
        if "http://127.0.0.1:5173" in allowed_origins:
            allowed_origins.add("http://localhost:5173")
        request_origin = request.headers.get("Origin")
        if request_origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = request_origin
            response.headers.add("Vary", "Origin")
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "gemma": gemma.status(), "live": live_manager.status()})

    @app.get("/api/status")
    def status():
        ocean = get_buoy_conditions(os.getenv("NDBC_STATION_ID", "41122"))
        weather = get_weather_conditions(
            float(os.getenv("BEACH_LATITUDE", "26.31656")),
            float(os.getenv("BEACH_LONGITUDE", "-80.0756")),
        )
        snapshot = state.snapshot()
        assessment = snapshot["assessments"].get(live_manager.camera_id)
        ocean_risk = assess_ocean_risk(ocean, weather, assessment)
        snapshot["cameras"] = [
            {
                **camera,
                "risk_level": (
                    ocean_risk["risk_level"]
                    if camera["id"] == live_manager.camera_id
                    else camera["risk_level"]
                ),
            }
            for camera in snapshot["cameras"]
        ]
        if ocean_risk["risk_level"] == "critical":
            snapshot["global_status"] = "active_alert"
        elif (
            ocean_risk["risk_level"] in {"moderate", "high"}
            and snapshot["global_status"] == "monitoring"
        ):
            snapshot["global_status"] = "elevated_conditions"
        return jsonify({
            **snapshot,
            "ocean": ocean,
            "weather": weather,
            "ocean_risk_assessment": ocean_risk,
            "gemma": gemma.status(),
            "live": live_manager.status(),
        })

    @app.get("/api/live/status")
    def live_status():
        return jsonify(live_manager.status())

    @app.post("/api/live/start")
    def live_start():
        dependencies = live_manager.preflight()
        if not dependencies["ready"]:
            return jsonify({
                "error": live_manager.status()["error"],
                "dependencies": dependencies,
            }), 503
        started = live_manager.start()
        return jsonify({**live_manager.status(), "started": started})

    @app.post("/api/live/stop")
    def live_stop():
        was_running = live_manager.stop()
        return jsonify({**live_manager.status(), "was_running": was_running})

    @app.get("/api/environment/buoy")
    def buoy():
        return jsonify(get_buoy_conditions(request.args.get("station_id", os.getenv("NDBC_STATION_ID", "41122"))))

    @app.get("/api/environment/weather")
    def weather():
        lat = float(request.args.get("latitude", os.getenv("BEACH_LATITUDE", "26.31656")))
        lon = float(request.args.get("longitude", os.getenv("BEACH_LONGITUDE", "-80.0756")))
        return jsonify(get_weather_conditions(lat, lon))

    @app.get("/api/events")
    def events():
        return jsonify(state.snapshot()["events"])

    @app.get("/api/events/stream")
    def event_stream():
        def generate():
            while True:
                yield f"event: status\ndata: {json.dumps(state.snapshot())}\n\n"
                time.sleep(2)
        return Response(generate(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})

    @app.post("/api/alerts/<alert_id>/acknowledge")
    def acknowledge(alert_id: str):
        return (jsonify({"acknowledged": True}) if state.acknowledge(alert_id) else (jsonify({"error": "Alert not found"}), 404))

    @app.post("/api/warnings/announce")
    def announce():
        data = request.get_json(silent=True) or {}
        message = data.get("message") or (state.warning or {}).get("message")
        if not message:
            return jsonify({"error": "No warning is prepared"}), 400
        state.warning = {"camera_id": data.get("camera_id"), "message": message, "issued": True}
        state.publish("operator", "Whistle and public announcement issued", camera_id=data.get("camera_id"), details={"message": message})
        return jsonify(state.warning)

    @app.post("/api/emergency/escalate")
    def escalate():
        data = request.get_json(silent=True) or {}
        if not data.get("confirmed"):
            return jsonify({"error": "Human confirmation is required"}), 400
        state.publish("operator", "SIMULATED 911 call initiated", camera_id=data.get("camera_id"), severity="critical")
        state.escalation = None
        return jsonify({"status": "simulated", "real_emergency_services_contacted": False})

    @app.get("/api/watch/status")
    def watch_status():
        ocean = get_buoy_conditions(os.getenv("NDBC_STATION_ID", "41122"))
        weather = get_weather_conditions(
            float(os.getenv("BEACH_LATITUDE", "26.31656")),
            float(os.getenv("BEACH_LONGITUDE", "-80.0756")),
        )
        snapshot = state.snapshot()
        assessment = snapshot["assessments"].get(live_manager.camera_id)
        ocean_risk = assess_ocean_risk(ocean, weather, assessment)
        return jsonify(get_watch_status(state, ocean_risk, weather, ocean))

    @app.post("/api/watch/action")
    def watch_action():
        data = request.get_json(silent=True) or {}
        action = data.get("action")
        if not action:
            return jsonify({"error": "Action parameter is required"}), 400
        result = handle_watch_action(
            state,
            action=action,
            camera_id=data.get("camera_id"),
            alert_id=data.get("alert_id"),
            details=data.get("details"),
        )
        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code

    @app.get("/api/watch/haptics")
    def watch_haptics():
        return jsonify({"haptic_profiles": HAPTIC_PATTERNS})

    @app.get("/api/iot/devices")
    def iot_devices():
        return jsonify({
            "devices": iot_manager.get_devices(),
            "telemetry_count": len(iot_manager.telemetry_history),
        })

    @app.post("/api/iot/telemetry")
    def iot_telemetry():
        data = request.get_json(silent=True) or {}
        try:
            telemetry = IoTDeviceTelemetry(**data)
            res = iot_manager.ingest_telemetry(state, telemetry)
            return jsonify(res), 200
        except Exception as err:
            return jsonify({"error": f"Invalid IoT telemetry payload: {err}"}), 400

    @app.post("/api/iot/simulate")
    def iot_simulate():
        data = request.get_json(silent=True) or {}
        device_id = data.get("device_id", "WEARABLE-TRACKER-04")
        alert_type = data.get("alert_type", "drowning_critical")
        res = iot_manager.simulate_event(state, device_id, alert_type)
        return jsonify(res), 200

    @app.get("/api/hand-wearable/gatt-spec")
    def hand_gatt_spec():
        return jsonify(GATT_SPEC)

    @app.get("/api/hand-wearable/devices")
    def hand_devices():
        return jsonify({"devices": list(hand_service.hand_devices.values())})

    @app.post("/api/hand-wearable/telemetry")
    def hand_telemetry():
        data = request.get_json(silent=True) or {}
        device_id = data.get("device_id", "HAND-GUARD-01")
        res = hand_service.process_telemetry(state, device_id, data)
        return jsonify(res), 200

    @app.post("/api/hand-wearable/haptic-trigger")
    def hand_haptic_trigger():
        data = request.get_json(silent=True) or {}
        device_id = data.get("device_id", "HAND-GUARD-01")
        pattern_id = data.get("pattern_id", "HAPTIC_PATTERN_DOUBLE_PULSE")
        intensity = int(data.get("intensity_pct", 100))
        duration = int(data.get("duration_ms", 500))
        res = hand_service.trigger_haptic(device_id, pattern_id, intensity, duration)
        return jsonify(res), 200

    @app.post("/api/hand-wearable/gesture-action")
    def hand_gesture_action():
        data = request.get_json(silent=True) or {}
        device_id = data.get("device_id", "HAND-GUARD-01")
        gesture_code = data.get("gesture_code")
        if not gesture_code:
            return jsonify({"error": "gesture_code is required"}), 400
        res = hand_service.process_gesture(state, device_id, gesture_code)
        return jsonify(res), 200 if res.get("success") else 400

    @app.get("/api/hand-wearable/embedded-header.h")
    def hand_embedded_header():
        return Response(C_HEADER_CODE, mimetype="text/x-chdr", headers={"Content-Disposition": "inline; filename=lifeguard_hand_protocol.h"})

    # 1. Multi-Tower & Shore Zone Grid Mapping
    @app.get("/api/towers")
    def get_towers():
        return jsonify({"towers": tower_manager.get_towers()})

    @app.post("/api/towers/<tower_id>/risk")
    def update_tower_risk(tower_id: str):
        data = request.get_json(silent=True) or {}
        risk = data.get("risk_level", "moderate")
        return jsonify(tower_manager.update_tower_risk(tower_id, risk))

    # 2. Autonomous Rescue Drone (UAV) & Buoy Dispatch
    @app.get("/api/drone/status")
    def drone_status():
        return jsonify(drone_manager.get_status())

    @app.post("/api/drone/dispatch")
    def drone_dispatch():
        data = request.get_json(silent=True) or {}
        drone_id = data.get("drone_id", "RESCUE-DRONE-01")
        lat = float(data.get("latitude", 26.31520))
        lon = float(data.get("longitude", -80.07580))
        zone = data.get("zone", "Zone 3 (South Sandbar)")
        return jsonify(drone_manager.dispatch_drone(state, drone_id, lat, lon, zone))

    @app.post("/api/drone/drop-buoy")
    def drone_drop_buoy():
        data = request.get_json(silent=True) or {}
        drone_id = data.get("drone_id", "RESCUE-DRONE-01")
        return jsonify(drone_manager.drop_buoy(state, drone_id))

    # 3. Thermal IR Night Vision Mode
    @app.get("/api/thermal/status")
    def thermal_status():
        return jsonify(thermal_service.get_status())

    @app.post("/api/thermal/config")
    def thermal_config():
        data = request.get_json(silent=True) or {}
        return jsonify(thermal_service.set_config(
            enabled=data.get("enabled", True),
            palette=data.get("palette"),
            contrast=data.get("contrast"),
        ))

    # 4. Off-Grid Resilient Mesh Networks
    @app.get("/api/mesh/status")
    def mesh_status():
        return jsonify(mesh_manager.get_status())

    # 5. Automated Legal & Incident Compliance Logger
    @app.get("/api/compliance/incidents")
    def compliance_incidents():
        return jsonify({"incidents": compliance_manager.get_incidents()})

    @app.post("/api/compliance/report")
    def compliance_report():
        data = request.get_json(silent=True) or {}
        return jsonify(compliance_manager.create_incident_report(
            state,
            zone=data.get("zone", "Zone 3 (South Sandbar)"),
            incident_type=data.get("incident_type", "Rip Current Assist"),
            severity=data.get("severity", "high"),
            evidence=data.get("evidence", "Multimodal evidence logged."),
            guard_name=data.get("guard_name", "Guard Jordan"),
        ))

    @app.get("/api/compliance/export/<incident_id>")
    def compliance_export(incident_id: str):
        txt = compliance_manager.generate_report_txt(incident_id)
        return Response(txt, mimetype="text/plain", headers={"Content-Disposition": f"attachment; filename={incident_id}_compliance.txt"})

    # 6. Physical Tower PA Strobe & Siren Relay Controller
    @app.get("/api/siren/status")
    def siren_status():
        return jsonify(siren_manager.get_status())

    @app.post("/api/siren/trigger")
    def siren_trigger():
        data = request.get_json(silent=True) or {}
        mode = data.get("mode", "evacuate_beach")
        operator = data.get("operator", "Guard Jordan")
        return jsonify(siren_manager.trigger_alarm(state, mode, operator))

    # 7. Tower Shift Handover & Vigilance Rotation Module
    @app.get("/api/handover/status")
    def handover_status():
        return jsonify(handover_manager.get_status())

    @app.post("/api/handover/rotate")
    def handover_rotate():
        data = request.get_json(silent=True) or {}
        incoming = data.get("incoming_guard", "Guard Sarah")
        notes = data.get("notes", "Tower handover completed smoothly.")
        return jsonify(handover_manager.execute_handover(state, incoming, notes))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        threaded=True,
    )
