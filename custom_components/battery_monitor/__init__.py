# Creato da domoticafacile.it
from __future__ import annotations

import logging
import os

import homeassistant.helpers.config_validation as cv
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Battery Monitor."""

    images_path = os.path.join(os.path.dirname(__file__), "images")

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/battery_monitor_images",
                images_path,
                cache_headers=True,
            )
        ]
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Battery Monitor from config entry."""

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Battery Monitor."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
