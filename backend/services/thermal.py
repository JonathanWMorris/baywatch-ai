from __future__ import annotations

from typing import Any


class ThermalService:
    def __init__(self) -> None:
        self.enabled = False
        self.palette = "ironbow"  # "ironbow", "plasma", "white_hot", "night_vision"
        self.contrast = 85

    def get_status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "palette": self.palette,
            "contrast": self.contrast,
            "sensor": "Long-Wave Infrared (LWIR) Dual RGB/Thermal Cam",
            "heat_signatures_detected": 3,
            "water_temp_contrast_delta_c": 14.2,
        }

    def set_config(self, enabled: bool, palette: str | None = None, contrast: int | None = None) -> dict[str, Any]:
        self.enabled = enabled
        if palette:
            self.palette = palette
        if contrast is not None:
            self.contrast = contrast
        return self.get_status()


thermal_service = ThermalService()
