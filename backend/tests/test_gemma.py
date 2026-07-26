import pytest
from backend.services.gemma import GemmaService

def test_extract_json_accepts_fenced_response():
    assert GemmaService._extract_json('prefix```json\n{"risk_level":"low"}\n```suffix')["risk_level"] == "low"

def test_extract_json_rejects_missing_object():
    with pytest.raises(Exception):
        GemmaService._extract_json("not structured")

