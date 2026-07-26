from __future__ import annotations

import logging
import os

import requests

from backend.services.cache import TTLValue

LOGGER = logging.getLogger(__name__)
_cache = TTLValue(600)
DEMO_WEATHER = {
    "source": "OpenWeather", "temperature_f": 84.0, "feels_like_f": 91.0,
    "wind_speed_mph": 12.0, "wind_gust_mph": 18.0, "wind_direction_deg": 105,
    "visibility_m": 10000, "humidity_percent": 76, "pressure_hpa": 1015,
    "condition": "partly cloudy", "alerts": [], "is_mock": True,
    "status_message": "OpenWeather unavailable; displaying Deerfield Beach demo weather.",
}


def get_weather_conditions(latitude: float, longitude: float, force: bool = False) -> dict:
    def load():
        key = os.getenv("OPENWEATHER_API_KEY")
        if not key:
            return dict(DEMO_WEATHER)
        try:
            response = requests.get("https://api.openweathermap.org/data/2.5/weather", params={
                "lat": latitude, "lon": longitude, "appid": key, "units": "imperial",
            }, timeout=5)
            response.raise_for_status()
            data = response.json()
            main, wind = data.get("main", {}), data.get("wind", {})
            return {
                "source": "OpenWeather", "temperature_f": main.get("temp"),
                "feels_like_f": main.get("feels_like"), "wind_speed_mph": wind.get("speed"),
                "wind_gust_mph": wind.get("gust"), "wind_direction_deg": wind.get("deg"),
                "visibility_m": data.get("visibility"), "humidity_percent": main.get("humidity"),
                "pressure_hpa": main.get("pressure"),
                "condition": (data.get("weather") or [{}])[0].get("description", "unknown"),
                "alerts": [], "is_mock": False, "status_message": None,
            }
        except Exception as exc:
            LOGGER.warning("OpenWeather fetch failed: %s", exc)
            return dict(DEMO_WEATHER)
    return load() if force else _cache.get_or_load(load)
