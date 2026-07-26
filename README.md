# Baywatch AI

**A Gemma-powered second set of eyes and ears for lifeguards.**

A lifeguard can only look in one direction at a time. Baywatch AI uses Google Gemma 4 E4B to watch separate beach cameras, listen to native audio, combine local observations with NOAA buoy and OpenWeather measurements, and bring situations that may deserve attention to a trained lifeguard.

Baywatch AI is decision support. It does not diagnose drowning, determine whether a person is unconscious, guarantee that water is safe, or automatically contact emergency services.

## The Problem

Lifeguards monitor swimmers, waves, changing weather, hazardous behavior, and calls for help simultaneously. Important evidence can occur outside the direction they are currently watching.

## Our Solution

Baywatch AI provides independent camera views and a glanceable command center. Gemma performs:

```text
Perception + multimodal reasoning + sensor fusion + decision support + tool selection
```

This is not a chatbot wrapper. Video frames and native audio enter the same assessment as environmental measurements. Validated results drive visible alerts, public-warning recommendations, and human-confirmed escalation controls.

## Why Santa Cruz

Santa Cruz combines crowded recreation, powerful Pacific surf, rocks, cliffs, shore break, and rapidly changing marine conditions. The prototype monitors Santa Cruz Main Beach and uses NOAA/NDBC Station 46042 in Monterey Bay.

## Why Gemma 4

The local `google/gemma-4-E4B-it` checkpoint supports video-frame sequences, native audio, multimodal instruction following, structured generation, and function calling. Baywatch AI keeps model integration behind one reusable service and never exposes hidden reasoning; the UI receives only an evidence-based summary.

## Architecture

```text
Camera clips + embedded/standalone audio ─┐
NOAA/NDBC Station 46042 ─────────────────┼─> Flask ─> Gemma 4 E4B ─> validated assessment
OpenWeather at the monitored beach ──────┘                         ├─> lifeguard alert
                                                                  ├─> warning draft
                                                                  └─> escalation recommendation
                                                                         ↓
                                                              React command dashboard
```

Multiple cameras remain separate by design. Geometric stitching is future work.

## Multimodal Video Analysis

Upload a video from any camera card. The Gemma processor samples frames and reasons about behavior and local surf observations. Bounding boxes are deliberately not required for the prototype.

## Native Audio Understanding

Gemma receives standalone audio directly rather than relying exclusively on speech-to-text, allowing it to consider speech, shouting, and relevant acoustic context. Video clips may also contain audio, although a separate extracted audio file offers the most reliable native-audio demonstration. Audio should be under 30 seconds.

## Environmental Sensor Fusion

- **NOAA/NDBC:** what the ocean is physically doing—wave height, period, direction, wind, and temperature.
- **OpenWeather:** local atmosphere—temperature, gusts, visibility, and conditions at the beach.
- **Camera and microphone:** what is happening locally now.
- **Gemma:** what the combined evidence may mean for lifeguard attention.

## NOAA/NDBC Integration

The backend parses real-time text observations from Station 46042, handles missing `MM` values, normalizes units, and caches results for five minutes. Failure returns clearly marked realistic demo readings.

## OpenWeather Integration

Current conditions are requested by the monitored beach coordinates and cached for ten minutes. A missing key, timeout, or API error returns marked demo readings without interrupting analysis.

## Gemma Tool Calling

Gemma can request allowlisted tools to alert the lifeguard, prepare a warning, or recommend emergency escalation. Every selection, argument object, result, and timestamp appears in the live timeline. Unknown tools are blocked.

## Lifeguard Alerts

Alerts use cautious language such as “possible swimmer distress” and show evidence and confidence. The operator can acknowledge an alert, issue a warning, or open escalation review.

## Public Warning System

Gemma drafts short, calm messages. An operator must press **Whistle + announce**; the browser generates an attention whistle, pauses, speaks the message, and logs the action.

## Human-in-the-Loop Safety

The escalation panel only simulates a 911 call. It is clearly labeled, requires a human click, and never contacts emergency services. Baywatch AI augments trained lifeguards rather than replacing them.

## Demo Mode

Place authorized clips in [`demo_assets`](demo_assets/README.md) using the documented filenames. Available scenarios become selectable automatically; missing scenarios remain visibly disabled. Scenario metadata selects media and camera context but never hardcodes Gemma's assessment.

Suggested 2–3 minute flow:

1. Show three cameras and the fused NOAA/OpenWeather panels.
2. Start a distress clip and point out Gemma's native video/audio analysis.
3. Show evidence, risk, and the tool event in the live timeline.
4. Press **Whistle + announce**.
5. Show the human-confirmed simulated emergency control.

## Running Locally

Requirements: Node 20+, Python 3.13, approximately 20 GB free disk space for model weights, and enough unified/GPU memory for E4B-it.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m backend.app
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Flask starts without loading Gemma; the first analysis downloads/loads the checkpoint and may take several minutes. Later analyses reuse it.

```bash
python -m pytest backend/tests
cd frontend && npm run build
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPENWEATHER_API_KEY` | Optional current-weather credential; missing values use marked demo data |
| `HF_TOKEN` | Optional Hugging Face token |
| `GEMMA_MODEL_ID` | Defaults to `google/gemma-4-E4B-it` |
| `DEMO_MODE` | Enables hackathon demo behavior |
| `BEACH_LATITUDE`, `BEACH_LONGITUDE` | Monitored beach coordinates |
| `NDBC_STATION_ID` | Defaults to `46042` |
| `FRONTEND_ORIGIN` | Allowed frontend origin |
| `PORT` | Flask port, default `8000` (avoids macOS AirPlay on 5000) |

Never commit `.env`, API keys, tokens, model weights, or private media.

## Limitations

This one-day prototype is not a certified surveillance or rescue system. Model output can be late, incomplete, or wrong; perspective and beach noise can obscure evidence. It has no identity recognition, precise localization, person tracking, real dispatch integration, or safety guarantee.

## Future Work

Production evaluation with lifeguards, privacy and retention controls, edge optimization, camera health monitoring, bounding boxes, tracking, cross-camera association, geometric stitching, deterministic surf measurements, redundant inference, and integration with approved emergency workflows.

## Team

Built for the CruzHacks Gemma 4 Hackathon by the Baywatch AI team.
