from backend.services.risk import assess_ocean_risk


def conditions(wave=2.0, period=4.0, wind=10.0, gust=16.0, visibility=10000):
    ocean = {
        "station_id": "41122",
        "wave_height_ft": wave,
        "dominant_period_sec": period,
        "is_mock": False,
    }
    weather = {
        "wind_speed_mph": wind,
        "wind_gust_mph": gust,
        "visibility_m": visibility,
        "condition": "clear sky",
        "alerts": [],
        "is_mock": False,
    }
    return ocean, weather


def test_environment_baseline_is_available_before_gemma():
    ocean, weather = conditions()
    result = assess_ocean_risk(ocean, weather)
    assert result["risk_level"] == "low"
    assert "Gemma awaiting first live analysis" in result["sources"]


def test_environmental_hazards_raise_risk():
    ocean, weather = conditions(wave=7, period=15, gust=38)
    assert assess_ocean_risk(ocean, weather)["risk_level"] == "high"


def test_gemma_scene_evidence_can_raise_baseline():
    ocean, weather = conditions()
    assessment = {
        "risk_level": "critical",
        "events": [{"description": "Potentially unresponsive person observed."}],
    }
    result = assess_ocean_risk(ocean, weather, assessment)
    assert result["risk_level"] == "critical"
    assert "Potentially unresponsive person observed." in result["factors"]
