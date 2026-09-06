# Creato da domoticafacile.it
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_CRITICAL, STATUS_OK, STATUS_WARNING
from .coordinator import BatteryCoordinator, BatterySnapshot

PARALLEL_UPDATES = 0


def _snap_list(items: list[BatterySnapshot]) -> list[dict[str, Any]]:
    return [
        {
            "entity_id": b.entity_id,
            "name": b.name,
            "device_name": b.device_name,
            "value": b.value,
            "unit": b.unit,
            "available": b.available,
            "retained": b.retained,
            "assumed_zero": b.assumed_zero,
        }
        for b in items
    ]


class BatteryBaseSensor(CoordinatorEntity[BatteryCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: BatteryCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="Battery Monitor",
            manufacturer="Domotica Facile",
            model="Battery Monitor",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def data(self) -> dict[str, Any]:
        return self.coordinator.data or {}


class BatteryStatusSensor(BatteryBaseSensor):
    _attr_device_class = None

    @property
    def icon(self) -> str:
        st = self.data.get("status")
        if st == STATUS_CRITICAL:
            return "mdi:alert-circle"
        if st == STATUS_WARNING:
            return "mdi:alert"
        return "mdi:check-circle"

    @property
    def native_value(self) -> str:
        return str(self.data.get("status", STATUS_OK))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.data
        return {
            "threshold": d.get("threshold"),
            "critical_threshold": d.get("critical_threshold"),
            "valid_total": d.get("valid_total"),
            "low_count": d.get("low_count"),
            "critical_count": d.get("critical_count"),
            "zero_count": d.get("zero_count"),
            "unavailable_count": d.get("unavailable_count"),
            "notify_on_zero": d.get("notify_on_zero"),
            "treat_unavailable_as_zero": d.get("treat_unavailable_as_zero"),
            "unavailable_retention_hours": d.get("unavailable_retention_hours"),
        }


class BatteryTotalSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        return int(self.data.get("valid_total", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"discovered_total": int(self.data.get("total", 0))}


class BatteryLowSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        return int(self.data.get("low_count", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        low: list[BatterySnapshot] = self.data.get("low", [])
        return {
            "threshold": self.data.get("threshold"),
            "entities": [b.entity_id for b in low],
            "devices": [b.device_name for b in low],
            "names": [b.name for b in low],
            "values": [b.value for b in low],
            "retained": [b.retained for b in low],
        }


class BatteryLowDevicesSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-heart-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        return int(self.data.get("low_devices_count", 0))


class BatteryZeroCountSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-alert-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        return int(self.data.get("zero_count", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        zero: list[BatterySnapshot] = self.data.get("zero", [])
        return {
            "entities": [b.entity_id for b in zero],
            "devices": [b.device_name for b in zero],
            "retained": [b.retained for b in zero],
            "assumed_zero": [b.assumed_zero for b in zero],
        }


class BatteryUnavailableCountSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-unknown"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int:
        return int(self.data.get("unavailable_count", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items: list[BatterySnapshot] = self.data.get("unavailable", [])
        return {
            "entities": [b.entity_id for b in items],
            "devices": [b.device_name for b in items],
            "last_known_values": [b.value for b in items],
        }


class BatteryLowestSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-low"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        lowest: BatterySnapshot | None = self.data.get("lowest")
        return None if lowest is None else lowest.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        lowest: BatterySnapshot | None = self.data.get("lowest")
        if lowest is None:
            return {}
        return {
            "entity_id": lowest.entity_id,
            "name": lowest.name,
            "device_name": lowest.device_name,
            "unit": lowest.unit,
            "last_changed": lowest.last_changed,
            "ignore_zero_for_lowest": self.data.get("ignore_zero_for_lowest"),
            "retained": lowest.retained,
        }


class BatteryLowPercentSensor(BatteryBaseSensor):
    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float:
        return float(self.data.get("low_percent", 0.0))


class BatteryZeroPercentSensor(BatteryBaseSensor):
    _attr_icon = "mdi:percent-outline"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float:
        return float(self.data.get("zero_percent", 0.0))


class BatteryLowListSensor(BatteryBaseSensor):
    _attr_icon = "mdi:format-list-bulleted"

    @property
    def native_value(self) -> str:
        # HA states are limited to 255 characters.
        return str(self.data.get("low_list_text", ""))[:255]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"items": _snap_list(self.data.get("low", []))}


class BatteryOverviewSensor(BatteryBaseSensor):
    _attr_icon = "mdi:battery-sync"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int:
        return int(self.data.get("valid_total", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.data
        return {
            "threshold": d.get("threshold"),
            "critical_threshold": d.get("critical_threshold"),
            "status": d.get("status"),
            "valid_total": d.get("valid_total"),
            "low_count": d.get("low_count", 0),
            "critical_count": d.get("critical_count", 0),
            "zero_count": d.get("zero_count", 0),
            "unavailable_count": d.get("unavailable_count", 0),
            "low_percent": d.get("low_percent", 0.0),
            "zero_percent": d.get("zero_percent", 0.0),
            "batteries": _snap_list(d.get("all", [])),
        }


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: BatteryCoordinator = entry.runtime_data
    async_add_entities(
        [
            BatteryStatusSensor(coordinator, "status"),
            BatteryTotalSensor(coordinator, "total"),
            BatteryLowSensor(coordinator, "low"),
            BatteryLowDevicesSensor(coordinator, "low_devices"),
            BatteryZeroCountSensor(coordinator, "zero_count"),
            BatteryUnavailableCountSensor(coordinator, "unavailable_count"),
            BatteryLowestSensor(coordinator, "lowest"),
            BatteryLowPercentSensor(coordinator, "low_percent"),
            BatteryZeroPercentSensor(coordinator, "zero_percent"),
            BatteryLowListSensor(coordinator, "low_list"),
            BatteryOverviewSensor(coordinator, "overview"),
        ]
    )
