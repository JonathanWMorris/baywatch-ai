from __future__ import annotations

import importlib.util
import logging
import os
import sys
import tempfile
import threading
import time
import wave
from datetime import datetime, timezone
from pathlib import Path

from backend.services.gemma import gemma
from backend.services.ocean import get_buoy_conditions
from backend.services.weather import get_weather_conditions
from backend.state import state
from backend.tools.lifeguard_tools import execute_assessment_tools

LOGGER = logging.getLogger(__name__)

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class YouTubeLiveCapture:
    """Resolve and capture a small public YouTube live window using yt-dlp + PyAV."""

    def __init__(self, video_id: str):
        self.video_id = video_id

    @property
    def watch_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"

    def resolve_stream(self) -> dict:
        import yt_dlp

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "format": "best[height<=720]/best",
        }
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(self.watch_url, download=False)
        formats = [
            item
            for item in info.get("formats", [])
            if item.get("url")
            and item.get("vcodec") not in {None, "none"}
            and item.get("acodec") not in {None, "none"}
        ]
        hls = [item for item in formats if "m3u8" in (item.get("protocol") or "")]
        candidates = hls or formats
        if not candidates and info.get("url"):
            candidates = [info]
        if not candidates:
            raise RuntimeError("YouTube did not expose a combined audio/video stream")
        selected = max(
            candidates,
            key=lambda item: (
                min(item.get("height") or 0, 720),
                item.get("tbr") or 0,
            ),
        )
        return {
            "url": selected["url"],
            "title": info.get("title", "YouTube live camera"),
            "is_live": bool(info.get("is_live") or info.get("live_status") == "is_live"),
            "format_id": selected.get("format_id"),
        }

    def capture(
        self,
        output_dir: str,
        duration_seconds: int = 12,
        stop_event: threading.Event | None = None,
    ) -> tuple[str, str | None, dict]:
        import av
        from av.audio.resampler import AudioResampler

        metadata = self.resolve_stream()
        stream_url = metadata.pop("url")
        source = av.open(
            stream_url,
            options={"rw_timeout": "15000000", "reconnect": "1"},
        )
        video_stream = next(iter(source.streams.video), None)
        audio_stream = next(iter(source.streams.audio), None)
        if video_stream is None:
            source.close()
            raise RuntimeError("Resolved YouTube stream has no video track")

        video_path = str(Path(output_dir, "live-window.mp4"))
        audio_path = str(Path(output_dir, "live-window.wav"))
        output = av.open(video_path, "w")
        encoder = output.add_stream("libx264", rate=2)
        width = min(video_stream.codec_context.width or 640, 640)
        height_source = video_stream.codec_context.height or 360
        height = max(2, int(height_source * width / (video_stream.codec_context.width or 640)) // 2 * 2)
        encoder.width, encoder.height, encoder.pix_fmt = width, height, "yuv420p"

        audio_file = wave.open(audio_path, "wb") if audio_stream else None
        resampler = AudioResampler(format="s16", layout="mono", rate=16000) if audio_stream else None
        if audio_file:
            audio_file.setnchannels(1)
            audio_file.setsampwidth(2)
            audio_file.setframerate(16000)

        started = time.monotonic()
        media_origin: float | None = None
        last_video_at = -1.0
        video_pts = 0
        video_frames = 0
        audio_samples = 0
        streams = [video_stream] + ([audio_stream] if audio_stream else [])
        try:
            done = False
            for packet in source.demux(streams):
                if stop_event and stop_event.is_set():
                    break
                if time.monotonic() - started >= duration_seconds + 20:
                    break
                for frame in packet.decode():
                    frame_time = float(frame.time) if frame.time is not None else None
                    if media_origin is None and frame_time is not None:
                        media_origin = frame_time
                    media_elapsed = (
                        frame_time - media_origin
                        if frame_time is not None and media_origin is not None
                        else time.monotonic() - started
                    )
                    if media_elapsed >= duration_seconds:
                        done = True
                        break
                    if isinstance(frame, av.VideoFrame):
                        if last_video_at < 0 or media_elapsed - last_video_at >= 0.5:
                            resized = frame.reformat(width=width, height=height, format="yuv420p")
                            resized.pts = video_pts
                            video_pts += 1
                            for encoded in encoder.encode(resized):
                                output.mux(encoded)
                            video_frames += 1
                            last_video_at = media_elapsed
                    elif audio_file and isinstance(frame, av.AudioFrame):
                        for converted in resampler.resample(frame):
                            pcm = converted.to_ndarray().reshape(-1).astype("<i2", copy=False)
                            audio_file.writeframes(pcm.tobytes())
                            audio_samples += len(pcm)
                if done:
                    break
            for encoded in encoder.encode():
                output.mux(encoded)
        finally:
            source.close()
            output.close()
            if audio_file:
                audio_file.close()

        if video_frames == 0 and stop_event and stop_event.is_set():
            raise InterruptedError("Live capture stopped by operator")
        if video_frames == 0:
            raise RuntimeError("No video frames were captured from the live stream")
        if audio_samples == 0:
            Path(audio_path).unlink(missing_ok=True)
            audio_path = None
        metadata.update(
            {
                "video_frames": video_frames,
                "audio_seconds": round(audio_samples / 16000, 1),
                "captured_at": iso_now(),
            }
        )
        return video_path, audio_path, metadata


class LiveAnalysisManager:
    camera_id = "camera_live"

    def __init__(self) -> None:
        self.video_id = os.getenv("LIVE_YOUTUBE_VIDEO_ID", "rdeoEeJ00xA")
        self.interval = max(30, int(os.getenv("LIVE_ANALYSIS_INTERVAL_SECONDS", "60")))
        self.capture_seconds = max(5, min(30, int(os.getenv("LIVE_CAPTURE_SECONDS", "12"))))
        self.capture_service = YouTubeLiveCapture(self.video_id)
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._phase = "stopped"
        self._error: str | None = None
        self._last_capture: dict | None = None
        self._last_assessment: dict | None = None
        self._next_analysis_at: str | None = None

    def status(self) -> dict:
        with self._lock:
            return {
                "enabled": bool(
                    self._thread and self._thread.is_alive() and not self._stop.is_set()
                ),
                "phase": self._phase,
                "video_id": self.video_id,
                "watch_url": self.capture_service.watch_url,
                "embed_url": f"https://www.youtube.com/embed/{self.video_id}?autoplay=1&mute=1",
                "interval_seconds": self.interval,
                "capture_seconds": self.capture_seconds,
                "last_capture": self._last_capture,
                "last_assessment": self._last_assessment,
                "next_analysis_at": self._next_analysis_at,
                "error": self._error,
                "environment_mode": "sensor_fusion",
                "dependencies": self.dependencies(),
            }

    @staticmethod
    def dependencies() -> dict:
        modules = {
            "yt_dlp": importlib.util.find_spec("yt_dlp") is not None,
            "av": importlib.util.find_spec("av") is not None,
        }
        return {
            **modules,
            "ready": all(modules.values()),
            "python_executable": sys.executable,
            "install_command": (
                "uv pip install --python .venv/bin/python -r requirements.txt"
            ),
        }

    def preflight(self) -> dict:
        dependencies = self.dependencies()
        with self._lock:
            if not dependencies["ready"]:
                missing = ", ".join(
                    name for name in ("yt_dlp", "av") if not dependencies[name]
                )
                self._error = (
                    f"Live capture dependencies missing: {missing}. "
                    f"Backend interpreter: {dependencies['python_executable']}. "
                    f"Run: {dependencies['install_command']}"
                )
            elif self._error and self._error.startswith(
                "Live capture dependencies missing:"
            ):
                self._error = None
        return dependencies

    def _camera_status(self, status: str) -> None:
        with state._lock:
            for camera in state.cameras:
                if camera["id"] == self.camera_id:
                    camera["status"] = status

    def start(self) -> bool:
        dependencies = self.preflight()
        if not dependencies["ready"]:
            return False
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop.clear()
            self._phase = "starting"
            self._error = None
            self._thread = threading.Thread(target=self._run, name="youtube-live-analysis", daemon=True)
            self._thread.start()
        self._camera_status("live_starting")
        state.publish("live", "External YouTube live analysis enabled", camera_id=self.camera_id)
        return True

    def stop(self) -> bool:
        with self._lock:
            running = bool(self._thread and self._thread.is_alive())
            self._stop.set()
            self._phase = "stopping" if running else "stopped"
            self._next_analysis_at = None
        self._camera_status("live_ready")
        state.publish("live", "External YouTube live analysis stopped", camera_id=self.camera_id)
        return running

    def _run(self) -> None:
        while not self._stop.is_set():
            cycle_started = time.monotonic()
            try:
                with self._lock:
                    self._phase = "capturing"
                    self._error = None
                    self._next_analysis_at = None
                self._camera_status("capturing")
                state.publish("live", f"Capturing {self.capture_seconds}s live video/audio window", camera_id=self.camera_id)
                with tempfile.TemporaryDirectory(prefix="baywatch-live-") as folder:
                    video_path, audio_path, capture = self.capture_service.capture(
                        folder, self.capture_seconds, self._stop
                    )
                    if self._stop.is_set():
                        break
                    with self._lock:
                        self._last_capture = capture
                        self._phase = "analyzing"
                    self._camera_status("analyzing")
                    state.publish("analysis", "Gemma live visual/audio analysis started", camera_id=self.camera_id)
                    ocean = get_buoy_conditions(
                        os.getenv("NDBC_STATION_ID", "41122")
                    )
                    weather = get_weather_conditions(
                        float(os.getenv("BEACH_LATITUDE", "26.31656")),
                        float(os.getenv("BEACH_LONGITUDE", "-80.0756")),
                    )
                    assessment = gemma.analyze(
                        self.camera_id,
                        video_path,
                        audio_path,
                        ocean,
                        weather,
                    )
                    state.apply_assessment(assessment)
                    execute_assessment_tools(assessment, state)
                    with self._lock:
                        self._last_assessment = assessment.model_dump()
            except InterruptedError:
                break
            except Exception as exc:
                LOGGER.exception("Live analysis cycle failed")
                with self._lock:
                    self._error = str(exc)
                self._camera_status("degraded")
                state.publish(
                    "live_error",
                    "Live capture unavailable; the YouTube view remains active and analysis will retry.",
                    camera_id=self.camera_id,
                    details={"error": str(exc)},
                )
            wait_seconds = max(0.0, self.interval - (time.monotonic() - cycle_started))
            if self._stop.is_set():
                break
            with self._lock:
                self._phase = "waiting"
                self._next_analysis_at = datetime.fromtimestamp(
                    time.time() + wait_seconds, timezone.utc
                ).isoformat()
            self._camera_status("live_waiting")
            self._stop.wait(wait_seconds)
        with self._lock:
            self._phase = "stopped"
            self._next_analysis_at = None
        self._camera_status("live_ready")


live_manager = LiveAnalysisManager()
