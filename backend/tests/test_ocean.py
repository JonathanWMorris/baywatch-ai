from backend.services.ocean import parse_ndbc

SAMPLE = """#YY MM DD hh mm WDIR WSPD GST WVHT DPD APD MWD PRES ATMP WTMP DEWP VIS PTDY TIDE
#yr mo dy hr mn degT m/s m/s m sec sec degT hPa degC degC degC nmi hPa ft
2026 07 26 18 30 330 9.0 12.0 MM MM MM MM 1018.1 15.7 16.6 14.4 MM MM MM
2026 07 26 18 20 330 9.0 11.0 1.7 19 5.4 133 1018.2 15.7 16.6 14.5 MM MM MM
"""

def test_parse_ndbc_uses_latest_complete_wave_row():
    result = parse_ndbc(SAMPLE, "41122")
    assert result["wave_height_ft"] == 5.6
    assert result["dominant_period_sec"] == 19
    assert result["wind_speed_mph"] == 20.1
    assert result["water_temp_f"] == 61.9
    assert result["is_mock"] is False
