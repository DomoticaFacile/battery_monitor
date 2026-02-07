# Creato da domoticafacile.it
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from fnmatch import fnmatch
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_EXCLUDE_PATTERNS,
    CONF_INCLUDE_HEURISTIC,
    CONF_INCLUDE_PATTERNS,
    CONF_SCAN_DOMAINS,
    CONF_THRESHOLD,
    CONF_CRITICAL_THRESHOLD,
    CONF_INCLUDE_ENTITIES,
    CONF_EXCLUDE_ENTITIES,
    CONF_IGNORE_ZERO_FOR_LOWEST,
    CONF_NOTIFY_ON_ZERO,
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_INCLUDE_HEURISTIC,
    DEFAULT_INCLUDE_PATTERNS,
    DEFAULT_SCAN_DOMAINS,
    DEFAULT_THRESHOLD,
    DEFAULT_CRITICAL_THRESHOLD,
    DEFAULT_INCLUDE_ENTITIES,
    DEFAULT_EXCLUDE_ENTITIES,
    DEFAULT_IGNORE_ZERO_FOR_LOWEST,
    DEFAULT_NOTIFY_ON_ZERO,
)

_LOGGER = logging.getLogger(__name__)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip().lower()
        if s in ("unknown", "unavailable", ""):
            return None
        s = s.replace("%", "").strip()
        return float(s)
    except Exception:
        return None


def _match_any(entity_id: str, patterns: list[str]) -> bool:
    return any(fnmatch(entity_id, p) for p in patterns)


def _csv_to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    return [s] if s else []


def _is_battery_entity(state: State, heuristic: bool) -> bool:
    attrs = state.attributes or {}
    if attrs.get("device_class") == "battery":
        return True

    if not heuristic:
        return False

    eid = state.entity_id.lower()
    name = (attrs.get("friendly_name") or "").lower()
    unit = (attrs.get("unit_of_measurement") or "").strip()

    if "battery" in eid or "battery" in name or "batter" in eid or "batter" in name:
        return True

    if unit == "%" and ("level" in eid or "level" in name):
        return True

    return False


def _battery_emoji(value: float, warning_threshold: int, critical_threshold: int) -> str:
    """Ritorna un indicatore visivo in base al livello batteria.

    - <= critical_threshold  -> 🔴
    - <= warning_threshold   -> 🟡
    - altrimenti             -> 🟢

    Nota: 0% viene comunque mostrato come 🔴.
    """
    if value <= 0:
        return "🔴"
    if value <= critical_threshold:
        return "🔴"
    if value <= warning_threshold:
        return "🟡"
    return "🟢"


@dataclass
class BatterySnapshot:
    entity_id: str
    name: str
    value: float | None
    available: bool
    unit: str | None
    last_changed: str
    device_class: str | None
    device_id: str | None
    device_name: str | None


class BatteryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._last_zero_set: set[str] = set()
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Battery Monitor",
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        cfg = {**self.entry.data, **(self.entry.options or {})}

        threshold = int(cfg.get(CONF_THRESHOLD, DEFAULT_THRESHOLD))
        critical_threshold = int(cfg.get(CONF_CRITICAL_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD))
        
        if critical_threshold > threshold:
            critical_threshold = threshold
        heuristic = bool(cfg.get(CONF_INCLUDE_HEURISTIC, DEFAULT_INCLUDE_HEURISTIC))
        scan_domains = _csv_to_list(cfg.get(CONF_SCAN_DOMAINS, DEFAULT_SCAN_DOMAINS)) or ["sensor"]
        include_patterns = _csv_to_list(cfg.get(CONF_INCLUDE_PATTERNS, DEFAULT_INCLUDE_PATTERNS))
        exclude_patterns = _csv_to_list(cfg.get(CONF_EXCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS))
        include_entities = _csv_to_list(cfg.get(CONF_INCLUDE_ENTITIES, DEFAULT_INCLUDE_ENTITIES))
        exclude_entities = _csv_to_list(cfg.get(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES))
        ignore_zero_for_lowest = bool(cfg.get(CONF_IGNORE_ZERO_FOR_LOWEST, DEFAULT_IGNORE_ZERO_FOR_LOWEST))
        notify_on_zero = bool(cfg.get(CONF_NOTIFY_ON_ZERO, DEFAULT_NOTIFY_ON_ZERO))

        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)

        batteries: list[BatterySnapshot] = []

        for st in self.hass.states.async_all():
            if st.domain not in scan_domains:
                continue

            eid = st.entity_id


            if eid.startswith("sensor.battery_monitor_"):
                continue

            ent = ent_reg.async_get(eid)
            if ent is not None and getattr(ent, "platform", None) == DOMAIN:
                continue

            
            if include_entities and eid not in include_entities:
                continue
            
            if exclude_entities and eid in exclude_entities:
                continue

            
            if include_patterns and not _match_any(eid, include_patterns):
                continue
            if exclude_patterns and _match_any(eid, exclude_patterns):
                continue

            if not _is_battery_entity(st, heuristic):
                continue

            attrs = st.attributes or {}
            value = _safe_float(st.state)

            
            device_id = None
            device_name = None
            if ent and ent.device_id:
                device_id = ent.device_id
                dev = dev_reg.async_get(device_id)
                if dev:
                    device_name = dev.name_by_user or dev.name

            batteries.append(
                BatterySnapshot(
                    entity_id=eid,
                    name=str(attrs.get("friendly_name", eid)),
                    value=value,
                    available=st.state not in ("unknown", "unavailable"),
                    unit=attrs.get("unit_of_measurement"),
                    last_changed=st.last_changed.isoformat(),
                    device_class=attrs.get("device_class"),
                    device_id=device_id,
                    device_name=device_name,
                )
            )

        
        batteries.sort(key=lambda s: (s.value is None, s.value if s.value is not None else 9999))

        
        valid = [b for b in batteries if b.available and b.value is not None]

        low = [b for b in valid if b.value <= threshold]
        critical = [b for b in valid if b.value <= critical_threshold]
        zero = [b for b in valid if b.value == 0]

        
        if ignore_zero_for_lowest:
            candidates = [b for b in valid if b.value > 0]
        else:
            candidates = valid
        lowest = min(candidates, key=lambda b: b.value) if candidates else None

        
        valid_total = len(valid)
        low_percent = round((len(low) / valid_total * 100.0), 1) if valid_total else 0.0
        zero_percent = round((len(zero) / valid_total * 100.0), 1) if valid_total else 0.0

        
        low_sorted = sorted(low, key=lambda b: (b.value if b.value is not None else 9999))
        low_list_text = " | ".join(
            f"{_battery_emoji(float(b.value), threshold, critical_threshold)} {(b.device_name or b.name)}: {int(b.value)}%"
            for b in low_sorted
            if b.value is not None
        )

        
        low_device_keys: set[str] = set()
        for b in low_sorted:
            if b.device_id:
                low_device_keys.add(b.device_id)
            else:
                low_device_keys.add(b.entity_id)
        low_devices_count = len(low_device_keys)

        
        if len(zero) > 0 or len(critical) > 0:
            status = "CRITICAL"
        elif len(low) > 0:
            status = "WARNING"
        else:
            status = "OK"

        
        zero_now = {b.entity_id for b in zero}
        notification_id = f"battery_monitor_zero_{self.entry.entry_id}"

        if notify_on_zero:
            if zero_now:
                
                if zero_now != self._last_zero_set:
                    lookup = {b.entity_id: (b.device_name or b.name) for b in batteries}
                    lines = [f"- **{lookup.get(eid, eid)}** (`{eid}`)" for eid in sorted(zero_now)]
                    msg = "Rilevate batterie a **0%**:\n" + "\n".join(lines)
                    persistent_notification.async_create(
                        self.hass,
                        msg,
                        title="⚠️ Battery Monitor: batteria a 0%",
                        notification_id=notification_id,
                    )
            else:
                
                if self._last_zero_set:
                    persistent_notification.async_dismiss(self.hass, notification_id)
                    persistent_notification.async_create(
                        self.hass,
                        "Tutte le batterie precedentemente a **0%** sono tornate sopra 0%.",
                        title="✅ Battery Monitor: 0% risolto",
                        notification_id=f"battery_monitor_zero_resolved_{self.entry.entry_id}",
                    )

        self._last_zero_set = zero_now

        return {
            "critical_threshold": critical_threshold,
            "threshold": threshold,
            "total": len(batteries),
            "valid_total": valid_total,
            "low": low_sorted,
            "low_count": len(low_sorted),
            "critical": critical,
            "critical_count": len(critical),
            "low_devices_count": low_devices_count,
            "zero": zero,
            "zero_count": len(zero),
            "low_percent": low_percent,
            "zero_percent": zero_percent,
            "lowest": lowest,
            "all": batteries,
            "low_list_text": low_list_text,
            "status": status,
            "ignore_zero_for_lowest": ignore_zero_for_lowest,
            "notify_on_zero": notify_on_zero,
        }


class BatteryBaseSensor(CoordinatorEntity[BatteryCoordinator], SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: BatteryCoordinator, unique_id: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_name = name


class BatteryTotalSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery"
    _attr_native_unit_of_measurement = None

    @property
    def native_value(self) -> int:
        
        return int(self.coordinator.data.get("valid_total", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "discovered_total": int(self.coordinator.data.get("total", 0)),
        }


class BatteryLowSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-alert"
    _attr_native_unit_of_measurement = None

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("low_count", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        low = self.coordinator.data.get("low", [])
        return {
            "threshold": self.coordinator.data.get("threshold"),
            "entities": [b.entity_id for b in low],
            "devices": [b.device_name for b in low],
            "names": [b.name for b in low],
            "values": [b.value for b in low],
        }


class BatteryZeroCountSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-alert-variant"
    _attr_native_unit_of_measurement = None

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("zero_count", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        zero = self.coordinator.data.get("zero", [])
        return {
            "entities": [b.entity_id for b in zero],
            "devices": [b.device_name for b in zero],
        }


class BatteryLowDevicesSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-heart-variant"
    _attr_native_unit_of_measurement = None

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("low_devices_count", 0))


class BatteryLowPercentSensor(BatteryBaseSensor):
    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float:
        return float(self.coordinator.data.get("low_percent", 0.0))


class BatteryZeroPercentSensor(BatteryBaseSensor):
    _attr_icon = "mdi:percent-outline"
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float:
        return float(self.coordinator.data.get("zero_percent", 0.0))


class BatteryLowestSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-low"
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        lowest = self.coordinator.data.get("lowest")
        return None if not lowest else lowest.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        lowest = self.coordinator.data.get("lowest")
        if not lowest:
            return {}
        return {
            "entity_id": lowest.entity_id,
            "name": lowest.name,
            "device_name": lowest.device_name,
            "unit": lowest.unit,
            "last_changed": lowest.last_changed,
            "ignore_zero_for_lowest": self.coordinator.data.get("ignore_zero_for_lowest"),
        }


class BatteryLowListSensor(BatteryBaseSensor):
    _attr_icon = "mdi:format-list-bulleted"
    _attr_native_unit_of_measurement = None
    _attr_state_class = None

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("low_list_text", "")


class BatteryStatusSensor(BatteryBaseSensor):
    _attr_native_unit_of_measurement = None
    _attr_state_class = None

    @property
    def icon(self) -> str:
        st = self.coordinator.data.get("status")
        if st == "CRITICAL":
            return "mdi:alert-circle"
        if st == "WARNING":
            return "mdi:alert"
        return "mdi:check-circle"

    @property
    def native_value(self) -> str:
        return str(self.coordinator.data.get("status", "OK"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "critical_threshold": self.coordinator.data.get("critical_threshold"),
            "threshold": self.coordinator.data.get("threshold"),
            "valid_total": self.coordinator.data.get("valid_total"),
            "low_count": self.coordinator.data.get("low_count"),
            "critical_count": self.coordinator.data.get("critical_count"),
            "zero_count": self.coordinator.data.get("zero_count"),
            "notify_on_zero": self.coordinator.data.get("notify_on_zero"),
        }


class BatteryOverviewSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-sync"
    _attr_native_unit_of_measurement = None

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("valid_total", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        batteries = self.coordinator.data.get("all", [])
        return {
            "critical_threshold": self.coordinator.data.get("critical_threshold"),
            "threshold": self.coordinator.data.get("threshold"),
            "status": self.coordinator.data.get("status"),
            "valid_total": self.coordinator.data.get("valid_total"),
            "low_count": self.coordinator.data.get("low_count", 0),
            "critical_count": self.coordinator.data.get("critical_count", 0),
            "zero_count": self.coordinator.data.get("zero_count", 0),
            "low_percent": self.coordinator.data.get("low_percent", 0.0),
            "zero_percent": self.coordinator.data.get("zero_percent", 0.0),
            "batteries": [
                {
                    "entity_id": b.entity_id,
                    "name": b.name,
                    "device_name": b.device_name,
                    "value": b.value,
                    "unit": b.unit,
                    "available": b.available,
                }
                for b in batteries
            ],
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = BatteryCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    uid = entry.entry_id
    async_add_entities(
        [
            BatteryStatusSensor(coordinator, f"{uid}_status", "Battery Monitor Status"),
            BatteryTotalSensor(coordinator, f"{uid}_total", "Battery Monitor Total"),
            BatteryLowSensor(coordinator, f"{uid}_low", "Battery Monitor Low"),
            BatteryLowDevicesSensor(coordinator, f"{uid}_low_devices", "Battery Monitor Low Devices"),
            BatteryZeroCountSensor(coordinator, f"{uid}_zero_count", "Battery Monitor Zero Count"),
            BatteryLowestSensor(coordinator, f"{uid}_lowest", "Battery Monitor Lowest"),
            BatteryLowPercentSensor(coordinator, f"{uid}_low_percent", "Battery Monitor Low Percent"),
            BatteryZeroPercentSensor(coordinator, f"{uid}_zero_percent", "Battery Monitor Zero Percent"),
            BatteryLowListSensor(coordinator, f"{uid}_low_list", "Battery Monitor Low List"),
            BatteryOverviewSensor(coordinator, f"{uid}_overview", "Battery Monitor Overview"),
        ]
    )
