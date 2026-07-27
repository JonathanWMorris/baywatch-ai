<p align="center">
  <a href="https://www.youtube.com/watch?v=05r-rRZtRaw">
     <img src="https://www.youtube.com/watch?v=05r-rRZtRaw" alt="Watch the video" width="600">
  </a>
</p>


# Baywatch AI

**A Gemma-powered second set of eyes and ears for lifeguards.**

A lifeguard can only look in one direction at a time—but danger can happen
anywhere. Baywatch AI monitors a live beach camera, listens to its native audio,
combines those observations with nearby ocean and local weather measurements,
and brings situations that may deserve attention to a trained lifeguard.

Baywatch AI is decision support. It does not diagnose drowning, determine
whether a person is unconscious, guarantee that water is safe, or automatically
contact emergency services.

## The Problem

Lifeguards must monitor swimmers, surf, hazardous behavior, changing weather,
and calls for help at the same time. Important evidence can occur outside the
direction they are currently watching.

## Our Solution

The hackathon demo centers on one public Deerfield Beach live stream and a
glanceable command dashboard. Google Gemma 4 E4B performs:

```text
Perception + native audio understanding + sensor fusion
           + decision support + tool selection
```

This is not a chatbot wrapper. Live video frames and audio enter the same
assessment as environmental measurements. Validated results drive visible
alerts, public-warning recommendations, and human-confirmed escalation
controls.

## Why Deerfield Beach

The selected public camera overlooks Deerfield Beach, Florida. Environmental
inputs are geographically matched to that view:

- NOAA/NDBC Station 41122 — Hollywood Beach, Florida
- OpenWeather conditions at Deerfield Beach International Fishing Pier
  (`26.31656, -80.07560`)

Station 41122 is an offshore observation point near the monitored beach, not a
measurement of conditions at the exact camera location. Baywatch AI labels
data sources and simulated fallbacks so operators can interpret them properly.

## Why Gemma 4

The `google/gemma-4-E4B-it` checkpoint supports video-frame sequences, native
audio, multimodal instruction following, structured generation, and function
calling. Model integration is isolated in a reusable service. The UI receives
an evidence-based summary, never hidden chain-of-thought.

## Architecture

```text
Deerfield live video + embedded audio ─┐
NOAA/NDBC Station 41122 ───────────────┼─> Flask ─> Gemma 4 E4B
OpenWeather at Deerfield Pier ─────────┘              │
                                                      v
                                         validated hazard assessment
                                          + ocean risk assessment
                                                      │
                        ┌─────────────────────────────┼──────────────┐
                        v                             v              v
                lifeguard alert              warning draft   escalation review
                        └─────────────────────────────┼──────────────┘
                                                      v
                                           React command dashboard
```

## Multimodal Live Analysis

The dashboard embeds the public YouTube stream. Press **Start live analysis**
to capture a short video/audio window. The backend samples the video, preserves
native audio when present, fetches cached environmental observations, and sends
the combined input to Gemma. Capture and inference never overlap; a new cycle
begins only after the previous one has completed.

If stream extraction or one inference cycle fails, the visible stream remains
available, the dashboard shows a degraded state, and analysis retries without
crashing the application.

## Native Audio Understanding

Gemma receives captured audio directly rather than relying exclusively on
speech-to-text. It can consider speech resembling calls for help, shouting,
abnormal vocal distress, and relevant acoustic context. Missing audio degrades
gracefully and does not prevent visual analysis.

## Environmental Sensor Fusion

- **NOAA/NDBC:** what the nearby ocean is physically doing.
- **OpenWeather:** what the local atmosphere is doing at the beach.
- **Camera and microphone:** what is happening locally right now.
- **Gemma:** what the combined evidence may mean for lifeguard attention.

The dashboard's **Ocean Risk Assessment** combines a deterministic environmental
baseline with Gemma's current scene assessment. Levels are `LOW`, `MODERATE`,
`HIGH`, and `CRITICAL`; they are attention levels, never declarations that
swimming is safe or unsafe.

## NOAA/NDBC Integration

The backend parses real-time text observations from Station 41122, handles
missing `MM` values, normalizes units, and caches results for five minutes.
Available measurements include wave height and period, wave direction, wind,
gusts, and water temperature. If NOAA is unavailable, realistic Florida demo
values are returned with `is_mock: true`.

## OpenWeather Integration

Current conditions are requested using the Deerfield Pier coordinates and
cached for ten minutes. A missing API key, timeout, or API error returns clearly
marked demo readings without interrupting live analysis.

## Gemma Tool Calling

Gemma can request allowlisted tools to alert the lifeguard, prepare a public
warning, or recommend emergency escalation. Every tool selection, arguments,
result, and timestamp appears in the activity timeline. Unknown tools are
blocked.

## Lifeguard Alerts

Alerts use cautious language such as “possible swimmer distress” and show
observable evidence and model confidence. The operator can acknowledge an
alert, issue a warning, or open escalation review.

## Public Warning System

Gemma drafts short, calm messages. An operator must press **Whistle + announce**;
the browser generates an attention whistle, pauses, speaks the message, and
logs the action.

## Human-in-the-Loop Safety

The escalation panel only simulates a 911 call. It is clearly labeled, requires
a human click, and never contacts emergency services. Baywatch AI augments
trained lifeguards rather than replacing them.

## Judge Demo Flow

1. Show the live Deerfield Beach stream and matched NOAA/OpenWeather panels.
2. Start live analysis and point out the captured video plus native audio.
3. Show the Ocean Risk factors and Gemma analysis timeline.
4. When an attention event appears, show its evidence and tool call.
5. Press **Whistle + announce** to demonstrate operator-controlled TTS.
6. Show that emergency escalation remains simulated and human-confirmed.

The system remains useful for the demo if weather credentials or an
environmental service are unavailable because every fallback is visibly marked.

## Running Locally

Requirements: Node 20+, Python 3.13, `ffmpeg`, approximately 20 GB of free disk
space for model weights, and enough unified/GPU memory for E4B-it.

```bash
python3.13 -m venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
.venv/bin/python -m backend.app
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Flask runs on port `8001`. It starts without
loading Gemma; the first live analysis downloads or loads the checkpoint and
may take several minutes. Later cycles reuse the model.

If port 8001 is unexpectedly occupied:

```bash
lsof -nP -iTCP:8001 -sTCP:LISTEN
```

Stop only the identified stale Baywatch backend, then start Flask again.

Run the automated checks with:

```bash
.venv/bin/python -m pytest backend/tests
cd frontend && npm test -- --run && npm run build
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPENWEATHER_API_KEY` | Optional credential; missing values use marked demo weather |
| `HF_TOKEN` | Optional Hugging Face token |
| `GEMMA_MODEL_ID` | Defaults to `google/gemma-4-E4B-it` |
| `BEACH_LATITUDE`, `BEACH_LONGITUDE` | Defaults to Deerfield Pier coordinates |
| `NDBC_STATION_ID` | Defaults to nearby Station `41122` |
| `FRONTEND_ORIGINS` | Allowed frontend origins; defaults to localhost/127.0.0.1 on port 5173 |
| `PORT` | Flask port, default `8001` |
| `LIVE_YOUTUBE_VIDEO_ID` | Defaults to the selected Deerfield public stream |
| `LIVE_ANALYSIS_INTERVAL_SECONDS` | Start-to-start interval; minimum 30 seconds |
| `LIVE_CAPTURE_SECONDS` | Captured media window, constrained to 5–30 seconds |

During development, Vite proxies `/api` to Flask on port 8001. Set
`VITE_API_URL` only when frontend and backend are hosted separately.
`VITE_BACKEND_PROXY_TARGET` can override the development proxy target.

Never commit `.env`, API keys, tokens, model weights, or private media.

## Limitations

This one-day prototype is not a certified surveillance or rescue system. Public
stream latency, changing YouTube delivery, perspective, distance, beach noise,
and model error can make output late, incomplete, or wrong. Nearby buoy readings
do not perfectly describe shore conditions. The system has no identity
recognition, precise localization, person tracking, real dispatch integration,
or safety guarantee.

## Future Work

Production evaluation with lifeguards, privacy and retention controls, edge
optimization, camera-health monitoring, bounding boxes, person tracking,
additional independent camera feeds, geometric stitching, deterministic surf
measurements, redundant inference, and approved emergency-workflow integration.

## Team

Built for the CruzHacks Gemma 4 Hackathon by the Baywatch AI team.
