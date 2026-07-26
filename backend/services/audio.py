from __future__ import annotations

import logging
import wave
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def extract_audio_track(video_path: str, output_dir: str, max_seconds: int = 30) -> str | None:
    """Extract up to 30 seconds of embedded audio as 16 kHz mono PCM for Gemma."""
    output = Path(output_dir, f"{Path(video_path).stem}-audio.wav")
    try:
        import av
        from av.audio.resampler import AudioResampler

        with av.open(video_path) as container:
            stream = next(iter(container.streams.audio), None)
            if stream is None:
                return None
            resampler = AudioResampler(format="s16", layout="mono", rate=16000)
            limit, written = max_seconds * 16000, 0
            with wave.open(str(output), "wb") as target:
                target.setnchannels(1)
                target.setsampwidth(2)
                target.setframerate(16000)
                for frame in container.decode(stream):
                    for converted in resampler.resample(frame):
                        pcm = converted.to_ndarray().reshape(-1).astype("<i2", copy=False)
                        pcm = pcm[: max(0, limit - written)]
                        if not len(pcm):
                            break
                        target.writeframes(pcm.tobytes())
                        written += len(pcm)
                    if written >= limit:
                        break
        if written:
            return str(output)
        output.unlink(missing_ok=True)
    except Exception as exc:
        LOGGER.info("No usable embedded audio extracted from %s: %s", video_path, exc)
        output.unlink(missing_ok=True)
    return None

