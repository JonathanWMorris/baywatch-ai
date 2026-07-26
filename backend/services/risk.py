from __future__ import annotations

from datetime import datetime, timezone

from backend.models import Assessment

LEVELS = ["unknown", "low", "moderate", "high", "critical"]


def _number(value):
    return value if isinstance(value, (int, float)) else None


def _raise(level: str, candidate: str) -> str:
    return candidate if LEVELS.index(candidate) > LEVELS.index(level) else level


def assess_ocean_risk(
    ocean: dict,
    weather: dict,
    assessment: Assessment | dict | None = None,
) -> dict:
    """Create a cautious, data-backed baseline and merge current Gemma evidence."""
    level = "low"
    factors: list[str] = []
    wave = _number(ocean.get("wave_height_ft"))
    period = _number(ocean.get("dominant_period_sec"))
    wind = _number(weather.get("wind_speed_mph"))
    gust = _number(weather.get("wind_gust_mph"))
    visibility = _number(weather.get("visibility_m"))
    condition = str(weather.get("condition") or "").lower()
    alerts = weather.get("alerts") or []

    if wave is not None:
        factors.append(f"{wave:g} ft significant wave height")
        if wave >= 10:
            level = _raise(level, "critical")
        elif wave >= 6:
            level = _raise(level, "high")
        elif wave >= 3:
            level = _raise(level, "moderate")
    if period is not None:
        factors.append(f"{period:g} sec dominant period")
        if period >= 15 and (wave or 0) >= 4:
            level = _raise(level, "high")
        elif period >= 10:
            level = _raise(level, "moderate")
    if wind is not None:
        factors.append(f"{wind:g} mph local wind")
        if wind >= 25:
            level = _raise(level, "high")
        elif wind >= 15:
            level = _raise(level, "moderate")
    if gust is not None:
        factors.append(f"{gust:g} mph gusts")
        if gust >= 50:
            level = _raise(level, "critical")
        elif gust >= 35:
            level = _raise(level, "high")
        elif gust >= 25:
            level = _raise(level, "moderate")
    if visibility is not None and visibility < 5000:
        factors.append(f"{visibility / 1000:g} km visibility")
        level = _raise(level, "high" if visibility < 1000 else "moderate")
    if alerts:
        factors.append("active local weather alert")
        level = _raise(level, "high")
    if "thunder" in condition:
        factors.append("thunderstorm conditions")
        level = _raise(level, "high")
    elif any(term in condition for term in ("rain", "squall")):
        factors.append(condition)
        level = _raise(level, "moderate")

    if assessment:
        payload = assessment.model_dump() if isinstance(assessment, Assessment) else assessment
        gemma_level = payload.get("risk_level", "unknown")
        if gemma_level in LEVELS and gemma_level != "unknown":
            level = _raise(level, gemma_level)
        for event in payload.get("events", []):
            description = event.get("description")
            if description and description not in factors:
                factors.append(description)

    if not factors:
        factors.append("environmental observations are temporarily limited")
        level = "unknown"

    source_mode = "demo" if ocean.get("is_mock") or weather.get("is_mock") else "live"
    summary = (
        f"{level.capitalize()} observed ocean risk based on regional buoy, local weather, "
        "and the latest available Gemma scene evidence. This is not a water-safety determination."
    )
    return {
        "risk_level": level,
        "factors": factors[:6],
        "summary": summary,
        "sources": [
            f"NOAA/NDBC Station {ocean.get('station_id', '41122')}",
            "OpenWeather · Deerfield Beach Pier",
            "Gemma live video/audio" if assessment else "Gemma awaiting first live analysis",
        ],
        "source_mode": source_mode,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
