from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from backend.services.cache import TTLValue

LOGGER = logging.getLogger(__name__)
NDBC_URL = "https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
_cache = TTLValue(300)

DEMO_OCEAN = {
    "station_id": "41122", "source": "NOAA/NDBC", "wave_height_ft": 2.0,
    "dominant_period_sec": 4.0, "average_period_sec": 2.8, "wave_direction_deg": 120,
    "wind_speed_mph": None, "wind_gust_mph": None, "water_temp_f": 87.0,
    "air_temp_f": 83.0, "pressure_hpa": None, "observation_time": None,
    "is_mock": True, "status_message": "NOAA unavailable; displaying Deerfield Beach demo conditions.",
}


def _number(value: str):
    if value in {"MM", ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_ndbc(text: str, station_id: str) -> dict:
    lines = [line.split() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        raise ValueError("NDBC response did not contain observations")
    headers = [item.lstrip("#") for item in lines[0]]
    for row in lines[2:]:
        if len(row) < len(headers):
            continue
        record = dict(zip(headers, row))
        # Prefer the newest row containing wave data; the latest partial row often has MM.
        if record.get("WVHT") == "MM" and any(r.get("WVHT") != "MM" for r in [dict(zip(headers, x)) for x in lines[2:10] if len(x) >= len(headers)]):
            continue
        def converted(key, factor=1.0, offset=0.0):
            value = _number(record.get(key, "MM"))
            return None if value is None else round(value * factor + offset, 1)
        try:
            observed = datetime(int(record["YY"]), int(record["MM"]), int(record["DD"]), int(record["hh"]), int(record["mm"]), tzinfo=timezone.utc).isoformat()
        except (KeyError, ValueError):
            observed = None
        return {
            "station_id": station_id, "source": "NOAA/NDBC",
            "wave_height_ft": converted("WVHT", 3.28084), "dominant_period_sec": converted("DPD"),
            "average_period_sec": converted("APD"), "wave_direction_deg": converted("MWD"),
            "wind_speed_mph": converted("WSPD", 2.23694), "wind_gust_mph": converted("GST", 2.23694),
            "water_temp_f": converted("WTMP", 1.8, 32), "air_temp_f": converted("ATMP", 1.8, 32),
            "pressure_hpa": converted("PRES"), "observation_time": observed, "is_mock": False,
            "status_message": None,
        }
    raise ValueError("No usable NDBC observation found")


def get_buoy_conditions(station_id: str = "41122", force: bool = False) -> dict:
    def load():
        try:
            response = requests.get(NDBC_URL.format(station_id=station_id), timeout=5)
            response.raise_for_status()
            return parse_ndbc(response.text, station_id)
        except Exception as exc:
            LOGGER.warning("NDBC fetch failed: %s", exc)
            return {**DEMO_OCEAN, "station_id": station_id}
    return load() if force else _cache.get_or_load(load)
