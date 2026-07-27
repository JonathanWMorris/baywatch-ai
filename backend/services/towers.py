from __future__ import annotations

from typing import Any
from backend.models import utc_now


TOWERS = [
    {
        "tower_id": "TOWER-01",
        "name": "Tower 1 - Pier North",
        "zone": "Zone 1 (Deerfield Pier)",
        "latitude": 26.31750,
        "longitude": -80.07540,
        "assigned_guard": "Guard Sarah",
        "status": "active",
        "risk_level": "moderate",
        "camera_feed": "Deerfield Pier North Stream",
        "embed_url": "https://www.youtube.com/embed/rdeoEeJ00xA?autoplay=1&mute=1",
    },
    {
        "tower_id": "TOWER-02",
        "name": "Tower 2 - Main Pavilion",
        "zone": "Zone 2 (Central Beach)",
        "latitude": 26.31656,
        "longitude": -80.07560,
        "assigned_guard": "Guard Jordan",
        "status": "active",
        "risk_level": "low",
        "camera_feed": "Central Pavilion Stream",
        "embed_url": "https://www.youtube.com/embed/rdeoEeJ00xA?autoplay=1&mute=1",
    },
    {
        "tower_id": "TOWER-03",
        "name": "Tower 3 - South Sandbar",
        "zone": "Zone 3 (South Shore)",
        "latitude": 26.31520,
        "longitude": -80.07580,
        "assigned_guard": "Guard Alex",
        "status": "active",
        "risk_level": "high",
        "camera_feed": "South Sandbar Rip-Cam",
        "embed_url": "https://www.youtube.com/embed/rdeoEeJ00xA?autoplay=1&mute=1",
    },
    {
        "tower_id": "TOWER-04",
        "name": "Tower 4 - Inlet Channel",
        "zone": "Zone 4 (North Inlet)",
        "latitude": 26.31900,
        "longitude": -80.07510,
        "assigned_guard": "Guard Marcus",
        "status": "active",
        "risk_level": "low",
        "camera_feed": "Inlet Channel Cam",
        "embed_url": "https://www.youtube.com/embed/rdeoEeJ00xA?autoplay=1&mute=1",
    },
]


class TowerGridManager:
    def __init__(self) -> None:
        self.towers = {t["tower_id"]: dict(t) for t in TOWERS}

    def get_towers(self) -> list[dict[str, Any]]:
        return list(self.towers.values())

    def update_tower_risk(self, tower_id: str, risk_level: str) -> dict[str, Any]:
        if tower_id in self.towers:
            self.towers[tower_id]["risk_level"] = risk_level
            self.towers[tower_id]["last_updated"] = utc_now()
        return self.towers.get(tower_id, {})


tower_manager = TowerGridManager()
