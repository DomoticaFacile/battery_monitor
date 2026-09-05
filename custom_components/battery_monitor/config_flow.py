# Creato da domoticafacile.it
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CRITICAL_THRESHOLD,
    CONF_EXCLUDE_ENTITIES,
    CONF_EXCLUDE_PATTERNS,
    CONF_IGNORE_ZERO_FOR_LOWEST,
    CONF_INCLUDE_ENTITIES,
    CONF_INCLUDE_HEURISTIC,
    CONF_INCLUDE_PATTERNS,
    CONF_NOTIFY_ON_ZERO,
    CONF_RETENTION_HOURS,
    CONF_SCAN_DOMAINS,
    CONF_THRESHOLD,
    CONF_TREAT_UNAVAILABLE_AS_ZERO,
    DEFAULT_CRITICAL_THRESHOLD,
    DEFAULT_EXCLUDE_ENTITIES,
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_IGNORE_ZERO_FOR_LOWEST,
    DEFAULT_INCLUDE_ENTITIES,
    DEFAULT_INCLUDE_HEURISTIC,
    DEFAULT_INCLUDE_PATTERNS,
    DEFAULT_NOTIFY_ON_ZERO,
    DEFAULT_RETENTION_HOURS,
    DEFAULT_SCAN_DOMAINS,
    DEFAULT_THRESHOLD,
    DEFAULT_TREAT_UNAVAILABLE_AS_ZERO,
    DOMAIN,
)


def _csv_to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    return [s] if s else []


def _list_to_csv(value: Any) -> str:
    return ", ".join(_csv_to_list(value))


def _percent_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="%"
        )
    )


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    scan_domains = _csv_to_list(defaults.get(CONF_SCAN_DOMAINS, DEFAULT_SCAN_DOMAINS)) or list(DEFAULT_SCAN_DOMAINS)
    entity_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=scan_domains, multiple=True)
    )
    return vol.Schema(
        {
            vol.Optional(CONF_THRESHOLD, default=int(defaults.get(CONF_THRESHOLD, DEFAULT_THRESHOLD))): _percent_selector(),
            vol.Optional(
                CONF_CRITICAL_THRESHOLD,
                default=int(defaults.get(CONF_CRITICAL_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD)),
            ): _percent_selector(),
            vol.Optional(
                CONF_INCLUDE_HEURISTIC,
                default=bool(defaults.get(CONF_INCLUDE_HEURISTIC, DEFAULT_INCLUDE_HEURISTIC)),
            ): selector.BooleanSelector(),
            vol.Optional(CONF_SCAN_DOMAINS, default=_list_to_csv(scan_domains)): selector.TextSelector(),
            vol.Optional(
                CONF_INCLUDE_ENTITIES,
                default=_csv_to_list(defaults.get(CONF_INCLUDE_ENTITIES, DEFAULT_INCLUDE_ENTITIES)),
            ): entity_selector,
            vol.Optional(
                CONF_EXCLUDE_ENTITIES,
                default=_csv_to_list(defaults.get(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES)),
            ): entity_selector,
            vol.Optional(
                CONF_INCLUDE_PATTERNS,
                default=_list_to_csv(defaults.get(CONF_INCLUDE_PATTERNS, DEFAULT_INCLUDE_PATTERNS)),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_EXCLUDE_PATTERNS,
                default=_list_to_csv(defaults.get(CONF_EXCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS)),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_IGNORE_ZERO_FOR_LOWEST,
                default=bool(defaults.get(CONF_IGNORE_ZERO_FOR_LOWEST, DEFAULT_IGNORE_ZERO_FOR_LOWEST)),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_TREAT_UNAVAILABLE_AS_ZERO,
                default=bool(defaults.get(CONF_TREAT_UNAVAILABLE_AS_ZERO, DEFAULT_TREAT_UNAVAILABLE_AS_ZERO)),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_RETENTION_HOURS,
                default=int(defaults.get(CONF_RETENTION_HOURS, DEFAULT_RETENTION_HOURS) or 0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=8760, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="h"
                )
            ),
            vol.Optional(
                CONF_NOTIFY_ON_ZERO,
                default=bool(defaults.get(CONF_NOTIFY_ON_ZERO, DEFAULT_NOTIFY_ON_ZERO)),
            ): selector.BooleanSelector(),
        }
    )


def _normalize(user_input: dict[str, Any], current: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Normalise form input into stored config; returns (data, errors)."""
    errors: dict[str, str] = {}
    threshold = int(user_input.get(CONF_THRESHOLD, DEFAULT_THRESHOLD))
    critical = int(user_input.get(CONF_CRITICAL_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD))
    if critical > threshold:
        errors[CONF_CRITICAL_THRESHOLD] = "critical_above_low"

    data = {
        CONF_THRESHOLD: threshold,
        CONF_CRITICAL_THRESHOLD: critical,
        CONF_INCLUDE_HEURISTIC: bool(user_input.get(CONF_INCLUDE_HEURISTIC, DEFAULT_INCLUDE_HEURISTIC)),
        CONF_SCAN_DOMAINS: _csv_to_list(user_input.get(CONF_SCAN_DOMAINS)) or list(DEFAULT_SCAN_DOMAINS),
        CONF_INCLUDE_ENTITIES: _csv_to_list(user_input.get(CONF_INCLUDE_ENTITIES, current.get(CONF_INCLUDE_ENTITIES))),
        CONF_EXCLUDE_ENTITIES: _csv_to_list(user_input.get(CONF_EXCLUDE_ENTITIES, current.get(CONF_EXCLUDE_ENTITIES))),
        CONF_INCLUDE_PATTERNS: _csv_to_list(user_input.get(CONF_INCLUDE_PATTERNS)),
        CONF_EXCLUDE_PATTERNS: _csv_to_list(user_input.get(CONF_EXCLUDE_PATTERNS)),
        CONF_IGNORE_ZERO_FOR_LOWEST: bool(user_input.get(CONF_IGNORE_ZERO_FOR_LOWEST, DEFAULT_IGNORE_ZERO_FOR_LOWEST)),
        CONF_TREAT_UNAVAILABLE_AS_ZERO: bool(
            user_input.get(CONF_TREAT_UNAVAILABLE_AS_ZERO, DEFAULT_TREAT_UNAVAILABLE_AS_ZERO)
        ),
        CONF_RETENTION_HOURS: max(0, int(user_input.get(CONF_RETENTION_HOURS, DEFAULT_RETENTION_HOURS) or 0)),
        CONF_NOTIFY_ON_ZERO: bool(user_input.get(CONF_NOTIFY_ON_ZERO, DEFAULT_NOTIFY_ON_ZERO)),
    }
    return data, errors


class BatteryMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 3

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            data, errors = _normalize(user_input, {})
            if not errors:
                return self.async_create_entry(title="Battery Monitor", data=data)

        return self.async_show_form(
            step_id="user", data_schema=_build_schema(user_input or {}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> BatteryMonitorOptionsFlow:
        return BatteryMonitorOptionsFlow()


class BatteryMonitorOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        current = {**self.config_entry.data, **(self.config_entry.options or {})}

        errors: dict[str, str] = {}
        if user_input is not None:
            options, errors = _normalize(user_input, current)
            if not errors:
                return self.async_create_entry(title="", data=options)
            current = {**current, **user_input}

        return self.async_show_form(step_id="init", data_schema=_build_schema(current), errors=errors)
