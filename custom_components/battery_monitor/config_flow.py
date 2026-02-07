# Creato da domoticafacile.it
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_THRESHOLD,
    CONF_CRITICAL_THRESHOLD,
    CONF_INCLUDE_HEURISTIC,
    CONF_SCAN_DOMAINS,
    CONF_INCLUDE_PATTERNS,
    CONF_EXCLUDE_PATTERNS,
    CONF_INCLUDE_ENTITIES,
    CONF_EXCLUDE_ENTITIES,
    CONF_IGNORE_ZERO_FOR_LOWEST,
    CONF_NOTIFY_ON_ZERO,
    DEFAULT_THRESHOLD,
    DEFAULT_CRITICAL_THRESHOLD,
    DEFAULT_INCLUDE_HEURISTIC,
    DEFAULT_SCAN_DOMAINS,
    DEFAULT_INCLUDE_PATTERNS,
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_INCLUDE_ENTITIES,
    DEFAULT_EXCLUDE_ENTITIES,
    DEFAULT_IGNORE_ZERO_FOR_LOWEST,
    DEFAULT_NOTIFY_ON_ZERO,
)

def _csv_to_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    return [s] if s else []

def _list_to_csv(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(v) for v in value)
    return str(value)

def _ensure_list(value) -> list[str]:
    
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, (tuple, set)):
        return [str(v) for v in value]
    if isinstance(value, str):
        
        return _csv_to_list(value)
    return [str(value)]


def _build_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            
            vol.Optional(
                CONF_THRESHOLD,
                default=int(defaults.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=100,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="%",
                )
            ),
            vol.Optional(
                CONF_CRITICAL_THRESHOLD,
                default=int(defaults.get(CONF_CRITICAL_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD)),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=100,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="%",
                )
            ),
            vol.Optional(
                CONF_INCLUDE_HEURISTIC,
                default=bool(defaults.get(CONF_INCLUDE_HEURISTIC, DEFAULT_INCLUDE_HEURISTIC)),
            ): bool,
            vol.Optional(
                CONF_SCAN_DOMAINS,
                default=_list_to_csv(defaults.get(CONF_SCAN_DOMAINS, DEFAULT_SCAN_DOMAINS)),
            ): str,

            
            vol.Optional(
                CONF_INCLUDE_ENTITIES,
                default=_ensure_list(defaults.get(CONF_INCLUDE_ENTITIES, DEFAULT_INCLUDE_ENTITIES)),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            ),
            vol.Optional(
                CONF_EXCLUDE_ENTITIES,
                default=_ensure_list(defaults.get(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES)),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            ),

            vol.Optional(
                CONF_IGNORE_ZERO_FOR_LOWEST,
                default=bool(defaults.get(CONF_IGNORE_ZERO_FOR_LOWEST, DEFAULT_IGNORE_ZERO_FOR_LOWEST)),
            ): bool,
            vol.Optional(
                CONF_NOTIFY_ON_ZERO,
                default=bool(defaults.get(CONF_NOTIFY_ON_ZERO, DEFAULT_NOTIFY_ON_ZERO)),
            ): bool,
        }
    )


class BatteryMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_build_schema({}))

        data = {
            CONF_THRESHOLD: int(user_input.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)),
            CONF_CRITICAL_THRESHOLD: int(user_input.get(CONF_CRITICAL_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD)),
            CONF_INCLUDE_HEURISTIC: bool(user_input.get(CONF_INCLUDE_HEURISTIC, DEFAULT_INCLUDE_HEURISTIC)),
            CONF_SCAN_DOMAINS: _csv_to_list(user_input.get(CONF_SCAN_DOMAINS, "")) or list(DEFAULT_SCAN_DOMAINS),
            
            CONF_INCLUDE_ENTITIES: _ensure_list(user_input.get(CONF_INCLUDE_ENTITIES, DEFAULT_INCLUDE_ENTITIES)),
            CONF_EXCLUDE_ENTITIES: _ensure_list(user_input.get(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES)),
            
            CONF_INCLUDE_PATTERNS: _csv_to_list(""),
            CONF_EXCLUDE_PATTERNS: _csv_to_list(""),
            CONF_IGNORE_ZERO_FOR_LOWEST: bool(user_input.get(CONF_IGNORE_ZERO_FOR_LOWEST, DEFAULT_IGNORE_ZERO_FOR_LOWEST)),
            CONF_NOTIFY_ON_ZERO: bool(user_input.get(CONF_NOTIFY_ON_ZERO, DEFAULT_NOTIFY_ON_ZERO)),
        }

        return self.async_create_entry(title="Battery Monitor", data=data)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        
        return BatteryMonitorOptionsFlow(config_entry)

class BatteryMonitorOptionsFlow(config_entries.OptionsFlow):
    """Options flow compatibile con versioni HA che:
    - NON accettano config_entry in super().__init__
    - espongono config_entry come property read-only (senza setter)
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:

        self._config_entry = config_entry

    @property
    def config_entry(self) -> config_entries.ConfigEntry:
        
        return self._config_entry

    async def async_step_init(self, user_input=None):
        current = {**self.config_entry.data, **(self.config_entry.options or {})}

        if user_input is None:
            return self.async_show_form(step_id="init", data_schema=_build_schema(current))

        options = {
            CONF_THRESHOLD: int(user_input.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)),
            CONF_CRITICAL_THRESHOLD: int(user_input.get(CONF_CRITICAL_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD)),
            CONF_INCLUDE_HEURISTIC: bool(user_input.get(CONF_INCLUDE_HEURISTIC, DEFAULT_INCLUDE_HEURISTIC)),
            CONF_SCAN_DOMAINS: _csv_to_list(user_input.get(CONF_SCAN_DOMAINS, "")) or list(DEFAULT_SCAN_DOMAINS),
            CONF_INCLUDE_ENTITIES: _ensure_list(user_input.get(CONF_INCLUDE_ENTITIES, current.get(CONF_INCLUDE_ENTITIES, DEFAULT_INCLUDE_ENTITIES))),
            CONF_EXCLUDE_ENTITIES: _ensure_list(user_input.get(CONF_EXCLUDE_ENTITIES, current.get(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES))),
            
            CONF_INCLUDE_PATTERNS: current.get(CONF_INCLUDE_PATTERNS, DEFAULT_INCLUDE_PATTERNS),
            CONF_EXCLUDE_PATTERNS: current.get(CONF_EXCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS),
            CONF_IGNORE_ZERO_FOR_LOWEST: bool(user_input.get(CONF_IGNORE_ZERO_FOR_LOWEST, DEFAULT_IGNORE_ZERO_FOR_LOWEST)),
            CONF_NOTIFY_ON_ZERO: bool(user_input.get(CONF_NOTIFY_ON_ZERO, DEFAULT_NOTIFY_ON_ZERO)),
        }

        return self.async_create_entry(title="", data=options)

