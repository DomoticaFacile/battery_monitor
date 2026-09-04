# Creato da domoticafacile.it
from __future__ import annotations

import logging
import os

import homeassistant.helpers.config_validation as cv
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import BatteryCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type BatteryMonitorConfigEntry = ConfigEntry[BatteryCoordinator]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Battery Monitor (static images for dashboards)."""
    images_path = os.path.join(os.path.dirname(__file__), "images")

    await hass.http.async_register_static_paths(
        [StaticPathConfig("/battery_monitor_images", images_path, cache_headers=True)]
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BatteryMonitorConfigEntry) -> bool:
    """Set up Battery Monitor from a config entry."""
    coordinator = BatteryCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Reload the entry when options change so they take effect immediately.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    # Stop listening to state changes when the entry is unloaded.
    entry.async_on_unload(coordinator.async_shutdown_listeners)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: BatteryMonitorConfigEntry) -> bool:
    """Unload Battery Monitor."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
