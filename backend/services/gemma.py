from __future__ import annotations

import json
import logging
import os
import re
import threading
from pathlib import Path

from pydantic import ValidationError

from backend.models import Assessment
from backend.tools.lifeguard_tools import TOOL_SCHEMAS

LOGGER = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Baywatch AI, a multimodal decision-support system for trained lifeguards.
Analyze only observable evidence. Never claim certainty that a person is drowning, unconscious, dead, or that water is safe.
Use phrases such as possible distress, potentially unresponsive, and lifeguard attention recommended.
Return only one JSON object matching the requested schema. Do not include chain-of-thought.
Public warnings must be short, calm, specific, and authoritative. Emergency escalation is only a recommendation requiring human confirmation.
"""


class GemmaService:
    def __init__(self) -> None:
        self.model_id = os.getenv("GEMMA_MODEL_ID", "google/gemma-4-E4B-it")
        self.model = None
        self.processor = None
        self.device = "unloaded"
        self.error: str | None = None
        self._lock = threading.Lock()

    def status(self) -> dict:
        return {"model_id": self.model_id, "loaded": self.model is not None, "device": self.device, "error": self.error}

    def load(self) -> None:
        if self.model is not None:
            return
        with self._lock:
            if self.model is not None:
                return
            try:
                import torch
                from transformers import AutoModelForMultimodalLM, AutoProcessor

                self.processor = AutoProcessor.from_pretrained(self.model_id, token=os.getenv("HF_TOKEN") or None)
                self.model = AutoModelForMultimodalLM.from_pretrained(
                    self.model_id, dtype="auto", low_cpu_mem_usage=True, token=os.getenv("HF_TOKEN") or None,
                )
                if torch.backends.mps.is_available():
                    self.model.to("mps")
                    self.device = "mps"
                else:
                    self.device = "cpu"
                self.model.eval()
                self.error = None
                LOGGER.info("Loaded %s on %s", self.model_id, self.device)
            except Exception as exc:
                self.error = str(exc)
                LOGGER.exception("Unable to load Gemma")
                raise

    @staticmethod
    def _extract_json(raw: str) -> dict:
        cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            if start < 0:
                raise
            depth, quoted, escaped = 0, False, False
            for index in range(start, len(cleaned)):
                char = cleaned[index]
                if quoted:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        quoted = False
                elif char == '"':
                    quoted = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return json.loads(cleaned[start:index + 1])
            raise

    def _prompt(self, camera_id: str, ocean: dict, weather: dict) -> str:
        schema = Assessment.model_json_schema()
        return f"""Analyze this camera observation and fuse every supplied sensor source.
Camera ID: {camera_id}
Sensor fusion input:
{json.dumps({'ocean_conditions': ocean, 'local_weather': weather}, default=str)}
Available action tools (request them only when justified):
{json.dumps(TOOL_SCHEMAS)}
Return this assessment schema, including tool_calls with name and arguments when action is warranted:
{json.dumps(schema)}
The reasoning_summary must contain only a concise evidence-and-conclusion summary."""

    @staticmethod
    def _response_text(parsed_response, raw: str) -> str:
        if isinstance(parsed_response, str):
            return parsed_response
        if isinstance(parsed_response, dict):
            content = parsed_response.get("content") or parsed_response.get("text")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict) and isinstance(item.get("text"), str):
                        parts.append(item["text"])
                if parts:
                    return "\n".join(parts)
            return json.dumps(parsed_response)
        return raw

    def analyze(self, camera_id: str, video_path: str | None, audio_path: str | None, ocean: dict, weather: dict) -> Assessment:
        if not video_path and not audio_path:
            raise ValueError("At least one video or audio input is required")
        try:
            self.load()
            content = []
            if video_path:
                content.append({"type": "video", "video": str(Path(video_path).resolve())})
            content.append({"type": "text", "text": self._prompt(camera_id, ocean, weather)})
            if audio_path:
                content.append({"type": "audio", "audio": str(Path(audio_path).resolve())})
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ]
            inputs = self.processor.apply_chat_template(
                messages, tokenize=True, return_dict=True, return_tensors="pt",
                add_generation_prompt=True, enable_thinking=False,
            ).to(self.model.device)
            input_len = inputs["input_ids"].shape[-1]
            outputs = self.model.generate(**inputs, max_new_tokens=700, do_sample=False)
            raw = self.processor.decode(outputs[0][input_len:], skip_special_tokens=False)
            parsed_response = self.processor.parse_response(
                outputs[0][input_len:], prefix=inputs["input_ids"][0]
            )
            final_text = self._response_text(parsed_response, raw)
            LOGGER.debug("Raw Gemma response: %s", raw)
            payload = self._extract_json(final_text)
            payload["camera_id"] = camera_id
            return Assessment.model_validate(payload)
        except (ValidationError, json.JSONDecodeError) as exc:
            LOGGER.warning("Malformed Gemma response: %s", exc)
            return Assessment(
                camera_id=camera_id, analysis_status="degraded", risk_level="unknown",
                reasoning_summary="Gemma returned an invalid structured assessment; lifeguard review is recommended.",
                errors=["Invalid structured model response"],
            )
        except Exception as exc:
            LOGGER.exception("Gemma inference failed")
            return Assessment(
                camera_id=camera_id, analysis_status="failed", risk_level="unknown",
                reasoning_summary="Multimodal analysis is temporarily unavailable. Continue direct lifeguard monitoring.",
                errors=[str(exc)],
            )


gemma = GemmaService()
