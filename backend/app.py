from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from backend.demo import get_scenarios
from backend.services.audio import extract_audio_track
from backend.services.gemma import gemma
from backend.services.ocean import get_buoy_conditions
from backend.services.weather import get_weather_conditions
from backend.state import state
from backend.tools.lifeguard_tools import execute_assessment_tools

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "demo_assets"


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(TESTING=testing, MAX_CONTENT_LENGTH=250 * 1024 * 1024)
    Path(app.instance_path, "uploads").mkdir(parents=True, exist_ok=True)

    @app.after_request
    def cors(response):
        response.headers["Access-Control-Allow-Origin"] = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "gemma": gemma.status()})

    @app.get("/api/status")
    def status():
        ocean = get_buoy_conditions(os.getenv("NDBC_STATION_ID", "46042"))
        weather = get_weather_conditions(float(os.getenv("BEACH_LATITUDE", "36.9639")), float(os.getenv("BEACH_LONGITUDE", "-122.0179")))
        return jsonify({**state.snapshot(), "ocean": ocean, "weather": weather, "gemma": gemma.status()})

    @app.get("/api/environment/buoy")
    def buoy():
        return jsonify(get_buoy_conditions(request.args.get("station_id", os.getenv("NDBC_STATION_ID", "46042"))))

    @app.get("/api/environment/weather")
    def weather():
        lat = float(request.args.get("latitude", os.getenv("BEACH_LATITUDE", "36.9639")))
        lon = float(request.args.get("longitude", os.getenv("BEACH_LONGITUDE", "-122.0179")))
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

    def run_analysis(camera_id_override: str | None = None):
        camera_id = camera_id_override or request.form.get("camera_id", "camera_1")
        video, audio = request.files.get("video"), request.files.get("audio")
        paths = {"video": None, "audio": None}
        for kind, upload in (("video", video), ("audio", audio)):
            if upload and upload.filename:
                filename = f"{uuid.uuid4()}-{secure_filename(upload.filename)}"
                path = Path(app.instance_path, "uploads", filename)
                upload.save(path)
                paths[kind] = str(path)
        if not any(paths.values()):
            return jsonify({"error": "Provide a video or audio file"}), 400
        if paths["video"] and not paths["audio"]:
            paths["audio"] = extract_audio_track(paths["video"], str(Path(app.instance_path, "uploads")))
            if paths["audio"]:
                state.publish("audio", "Embedded audio extracted for native Gemma analysis", camera_id=camera_id)
        ocean_data = get_buoy_conditions(os.getenv("NDBC_STATION_ID", "46042"))
        weather_data = get_weather_conditions(float(os.getenv("BEACH_LATITUDE", "36.9639")), float(os.getenv("BEACH_LONGITUDE", "-122.0179")))
        state.publish("analysis", "Gemma multimodal analysis started", camera_id=camera_id)
        assessment = gemma.analyze(camera_id, paths["video"], paths["audio"], ocean_data, weather_data)
        state.apply_assessment(assessment)
        tool_results = execute_assessment_tools(assessment, state)
        return jsonify({"assessment": assessment.model_dump(), "tool_results": tool_results})

    @app.post("/api/analyze")
    def analyze():
        return run_analysis()

    @app.post("/api/cameras/<camera_id>/analyze")
    def analyze_camera(camera_id: str):
        return run_analysis(camera_id)

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

    @app.get("/api/demo/scenarios")
    def scenarios():
        return jsonify(get_scenarios(ASSET_DIR))

    @app.post("/api/demo/scenarios/<scenario_id>/start")
    def start_scenario(scenario_id: str):
        scenario = next((item for item in get_scenarios(ASSET_DIR) if item["id"] == scenario_id), None)
        if not scenario:
            return jsonify({"error": "Scenario not found"}), 404
        if not scenario["available"]:
            return jsonify({"error": f"Add {scenario['media_file']} to demo_assets first"}), 409
        for camera in state.cameras:
            if camera["id"] == scenario["camera_id"]:
                camera["media_url"] = scenario["media_url"]
                camera["status"] = "analyzing"
        state.publish("demo", f"Scenario started: {scenario['name']}", camera_id=scenario["camera_id"])
        return jsonify(scenario)

    @app.get("/demo-assets/<path:filename>")
    def demo_asset(filename: str):
        return send_from_directory(ASSET_DIR, filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        threaded=True,
    )
