from __future__ import annotations

from typing import Any
from backend.models import utc_now


MESH_NODES = [
    {
        "node_id": "MESH-NODE-ALPHA",
        "name": "Tower 1 Mesh Relay Buoy",
        "frequency": "915 MHz LoRa",
        "hops": 0,
        "snr_db": 11.5,
        "battery_pct": 96,
        "status": "active_relay",
    },
    {
        "node_id": "MESH-NODE-BRAVO",
        "name": "South Jetty Meshtastic Pod",
        "frequency": "915 MHz LoRa",
        "hops": 1,
        "snr_db": 8.2,
        "battery_pct": 89,
        "status": "active_relay",
    },
    {
        "node_id": "MESH-NODE-CHARLIE",
        "name": "Inlet Channel Offshore Node",
        "frequency": "915 MHz LoRa",
        "hops": 2,
        "snr_db": 6.8,
        "battery_pct": 91,
        "status": "active_relay",
    },
]


class MeshNetworkManager:
    def __init__(self) -> None:
        self.nodes = list(MESH_NODES)
        self.mesh_active = True
        self.internet_fallback_active = False

    def get_status(self) -> dict[str, Any]:
        return {
            "mesh_active": self.mesh_active,
            "internet_fallback_active": self.internet_fallback_active,
            "total_nodes": len(self.nodes),
            "nodes": self.nodes,
            "last_heartbeat": utc_now(),
        }


mesh_manager = MeshNetworkManager()
