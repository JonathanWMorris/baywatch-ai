from __future__ import annotations

from pathlib import Path

SCENARIOS = [
    ("normal_beach", "Normal Beach", "camera_1", "normal-beach.mp4", "Low risk; no active hazard"),
    ("distress_shout", "Distress Shout", "camera_2", "distress-shout.mp4", "Possible distress vocalization"),
    ("swimmer_distress", "Possible Swimmer Distress", "camera_2", "swimmer-distress.mp4", "Lifeguard attention recommended"),
    ("pulled_by_surf", "Person Pulled by Surf", "camera_2", "pulled-by-surf.mp4", "Possible movement away from shore"),
    ("motionless_person", "Motionless Person", "camera_3", "motionless-person.mp4", "Critical lifeguard review"),
    ("dangerous_surf", "Dangerous Surf", "camera_1", "dangerous-surf.mp4", "Public warning suggested"),
]


def get_scenarios(asset_dir: Path) -> list[dict]:
    return [{
        "id": sid, "name": name, "camera_id": camera, "media_file": filename,
        "expected_theme": theme, "available": (asset_dir / filename).is_file(),
        "media_url": f"/demo-assets/{filename}" if (asset_dir / filename).is_file() else None,
    } for sid, name, camera, filename, theme in SCENARIOS]

