# Creato da domoticafacile.it
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import BatteryCoordinator


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry) -> dict[str, Any]:
    coordinator: BatteryCoordinator = entry.runtime_data
    data = coordinator.data or {}
    return {
        "entry_data": dict(entry.data),
        "entry_options": dict(entry.options),
        "summary": {k: v for k, v in data.items() if isinstance(v, (int, float, str, bool))},
        "batteries": [b.__dict__ for b in data.get("all", [])],
    }
