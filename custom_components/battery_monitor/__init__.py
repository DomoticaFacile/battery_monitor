# Creato da domoticafacile.it
from __future__ import annotations

import logging
import os
import shutil

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]

# Creato da domoticafacile.it
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg")


def _install_images(hass: HomeAssistant) -> None:
    """Copia le immagini dell'integrazione in /config/www/images/battery_monitor."""
    source_dir = os.path.join(os.path.dirname(__file__), "images")
    target_dir = os.path.join(hass.config.path("www"), "images", "battery_monitor")

    if not os.path.isdir(source_dir):
        _LOGGER.warning("Cartella immagini non trovata: %s", source_dir)
        return

    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception as err:
        _LOGGER.error("Impossibile creare la cartella target %s: %s", target_dir, err)
        return

    copied = 0
    skipped = 0
    found = 0

    for file_name in os.listdir(source_dir):
        source_file = os.path.join(source_dir, file_name)

        if not os.path.isfile(source_file):
            continue

        if not file_name.lower().endswith(_IMAGE_EXTS):
            continue

        found += 1
        target_file = os.path.join(target_dir, file_name)

        # Creato da domoticafacile.it
        if os.path.exists(target_file):
            skipped += 1
            continue

        try:
            shutil.copy2(source_file, target_file)
            copied += 1
            _LOGGER.info("Copiato %s in www/images/battery_monitor", file_name)
        except Exception as err:
            _LOGGER.error("Errore copiando %s: %s", file_name, err)

    if found == 0:
        _LOGGER.warning("Nessuna immagine trovata in %s (estensioni: %s)", source_dir, _IMAGE_EXTS)
    else:
        _LOGGER.info(
            "Installazione immagini Battery Monitor completata: trovate=%s, copiate=%s, già presenti=%s, target=%s",
            found,
            copied,
            skipped,
            target_dir,
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    await hass.async_add_executor_job(_install_images, hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.async_add_executor_job(_install_images, hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

