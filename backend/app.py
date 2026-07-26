from __future__ import annotations

import json
import logging
import os
import time

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

from backend.services.gemma import gemma
from backend.services.live import live_manager
from backend.services.ocean import get_buoy_conditions
from backend.services.risk import assess_ocean_risk
from backend.services.weather import get_weather_conditions
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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        threaded=True,
    )
