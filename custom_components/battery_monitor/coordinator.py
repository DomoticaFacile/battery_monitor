# Creato da domoticafacile.it
from __future__ import annotations

import logging
from dataclasses import dataclass
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatch
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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
    REFRESH_DEBOUNCE_SECONDS,
    STORAGE_SAVE_DELAY,
    STORAGE_VERSION,
    STATUS_CRITICAL,
    STATUS_OK,
    STATUS_WARNING,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

_INVALID_STATES = (STATE_UNKNOWN, STATE_UNAVAILABLE, "", "none")

# Keywords that, combined with a "%" unit, strongly indicate a battery level.
_STRICT_BATTERY_KEYWORDS = ("battery_percent", "battery_level", "battery level", "battery_state", "batt_level")
# Keywords that indicate the entity is about the battery but is NOT a level.
_EXCLUDE_KEYWORDS = ("charging", "current", "power", "load", "voltage", "energy", "temperature", "health", "cycles")

_NOTIFICATION_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "zero_title": "⚠️ Battery Monitor: battery at 0%",
        "zero_body": "Batteries detected at **0%**:",
        "unavailable_hint": "(unavailable, last known 0%)",
        "resolved_title": "✅ Battery Monitor: 0% resolved",
        "resolved_body": "All batteries previously at **0%** are now above 0%.",
    },
    "it": {
        "zero_title": "⚠️ Battery Monitor: batteria a 0%",
        "zero_body": "Rilevate batterie a **0%**:",
        "unavailable_hint": "(non disponibile, ultimo valore noto 0%)",
        "resolved_title": "✅ Battery Monitor: 0% risolto",
        "resolved_body": "Tutte le batterie che erano a **0%** sono tornate sopra lo 0%.",
    },
}


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip().lower()
        if s in _INVALID_STATES:
            return None
        return float(s.replace("%", "").strip())
    except (TypeError, ValueError):
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


def _is_battery_entity(state: State, heuristic: bool, registry_device_class: str | None = None) -> bool:
    """Decide whether a state represents a battery level."""
    attrs = state.attributes or {}
    device_class = attrs.get("device_class") or registry_device_class
    if device_class == "battery":
        return True

    if not heuristic:
        return False

    eid = state.entity_id.lower()
    name = str(attrs.get("friendly_name") or "").lower()
    text = f"{eid} {name}"
    unit = str(attrs.get("unit_of_measurement") or "").strip()
    if unit != "%":
        # The heuristic only ever accepts percentage values.
        return False

    if any(k in text for k in _STRICT_BATTERY_KEYWORDS):
        return True

    if any(k in text for k in _EXCLUDE_KEYWORDS):
        return False

    return "battery" in text or "batteria" in text


def battery_emoji(value: float, warning_threshold: int, critical_threshold: int) -> str:
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
    retained: bool = False  # value comes from the retention cache
    assumed_zero: bool = False  # unavailable and treated as 0% by option

    @property
    def display_name(self) -> str:
        return self.device_name or self.name


class BatteryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Scans the state machine and aggregates battery information."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._last_zero_set: set[str] = set()
        self._last_valid_snapshots: dict[str, tuple[BatterySnapshot, datetime]] = {}
        self._unsub_state: CALLBACK_TYPE | None = None
        self._store: Store = Store(hass, STORAGE_VERSION, self._storage_key(entry))
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Battery Monitor",
            update_interval=UPDATE_INTERVAL,
        )
        self._debouncer = Debouncer(
            hass,
            _LOGGER,
            cooldown=REFRESH_DEBOUNCE_SECONDS,
            immediate=False,
            function=self.async_request_refresh,
        )
        self._scan_domains = set(self._config().get("scan_domains_list", ["sensor"]))
        self._unsub_state = hass.bus.async_listen(EVENT_STATE_CHANGED, self._handle_state_change)

    # ------------------------------------------------------------------ config
    def _config(self) -> dict[str, Any]:
        cfg = {**self.entry.data, **(self.entry.options or {})}
        cfg["scan_domains_list"] = _csv_to_list(cfg.get(CONF_SCAN_DOMAINS, DEFAULT_SCAN_DOMAINS)) or ["sensor"]
        return cfg

    # ---------------------------------------------------------------- storage
    @staticmethod
    def _storage_key(entry: ConfigEntry) -> str:
        return f"{DOMAIN}.{entry.entry_id}"

    async def async_load_storage(self) -> None:
        """Restore last known values and notification state from disk."""
        try:
            data = await self._store.async_load()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Battery Monitor: could not load stored data: %s", err)
            return
        if not data:
            return
        for eid, item in (data.get("snapshots") or {}).items():
            try:
                snap = BatterySnapshot(**item["snapshot"])
                seen_at = datetime.fromisoformat(item["seen_at"])
                self._last_valid_snapshots[eid] = (snap, seen_at)
            except (KeyError, TypeError, ValueError):
                continue
        self._last_zero_set = set(data.get("last_zero_set") or [])
        _LOGGER.debug("Battery Monitor: restored %d cached values", len(self._last_valid_snapshots))

    def _storage_data(self) -> dict[str, Any]:
        return {
            "snapshots": {
                eid: {"snapshot": asdict(snap), "seen_at": seen_at.isoformat()}
                for eid, (snap, seen_at) in self._last_valid_snapshots.items()
            },
            "last_zero_set": sorted(self._last_zero_set),
        }

    @callback
    def _schedule_save(self) -> None:
        self._store.async_delay_save(self._storage_data, STORAGE_SAVE_DELAY)

    @staticmethod
    async def async_remove_storage(hass: HomeAssistant, entry: ConfigEntry) -> None:
        await Store(hass, STORAGE_VERSION, BatteryCoordinator._storage_key(entry)).async_remove()

    # ------------------------------------------------------------- listeners
    @callback
    def _handle_state_change(self, event: Event) -> None:
        entity_id: str = event.data.get("entity_id", "")
        domain = entity_id.split(".", 1)[0]
        if domain not in self._scan_domains:
            return
        if entity_id.startswith(f"{domain}.{DOMAIN}_"):
            return
        old: State | None = event.data.get("old_state")
        new: State | None = event.data.get("new_state")
        # Only refresh when the value actually changed (not just attributes).
        if old is not None and new is not None and old.state == new.state:
            return
        self.hass.async_create_task(self._debouncer.async_call())

    @callback
    def async_shutdown_listeners(self) -> None:
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        self._debouncer.async_cancel()

    # ----------------------------------------------------------------- update
    async def _async_update_data(self) -> dict[str, Any]:
        cfg = self._config()

        threshold = int(cfg.get(CONF_THRESHOLD, DEFAULT_THRESHOLD))
        critical_threshold = int(cfg.get(CONF_CRITICAL_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD))
        critical_threshold = min(critical_threshold, threshold)
        heuristic = bool(cfg.get(CONF_INCLUDE_HEURISTIC, DEFAULT_INCLUDE_HEURISTIC))
        scan_domains = cfg["scan_domains_list"]
        self._scan_domains = set(scan_domains)
        include_patterns = _csv_to_list(cfg.get(CONF_INCLUDE_PATTERNS, DEFAULT_INCLUDE_PATTERNS))
        exclude_patterns = _csv_to_list(cfg.get(CONF_EXCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS))
        include_entities = set(_csv_to_list(cfg.get(CONF_INCLUDE_ENTITIES, DEFAULT_INCLUDE_ENTITIES)))
        exclude_entities = set(_csv_to_list(cfg.get(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES)))
        ignore_zero_for_lowest = bool(cfg.get(CONF_IGNORE_ZERO_FOR_LOWEST, DEFAULT_IGNORE_ZERO_FOR_LOWEST))
        notify_on_zero = bool(cfg.get(CONF_NOTIFY_ON_ZERO, DEFAULT_NOTIFY_ON_ZERO))
        treat_unavailable_as_zero = bool(
            cfg.get(CONF_TREAT_UNAVAILABLE_AS_ZERO, DEFAULT_TREAT_UNAVAILABLE_AS_ZERO)
        )
        retention_hours = int(cfg.get(CONF_RETENTION_HOURS, DEFAULT_RETENTION_HOURS) or 0)
        retention: timedelta | None = timedelta(hours=retention_hours) if retention_hours > 0 else None

        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)
        now = datetime.now(timezone.utc)

        # Purge cache entries: expired (if a retention period is set) or whose
        # entity has been removed from Home Assistant (absent from both the
        # state machine and the entity registry).
        cache_changed = False
        for eid, (_, seen_at) in list(self._last_valid_snapshots.items()):
            expired = retention is not None and now - seen_at > retention
            removed = self.hass.states.get(eid) is None and ent_reg.async_get(eid) is None
            if expired or removed:
                self._last_valid_snapshots.pop(eid, None)
                cache_changed = True

        batteries: list[BatterySnapshot] = []
        seen: set[str] = set()

        for st in self.hass.states.async_all():
            if st.domain not in scan_domains:
                continue
            eid = st.entity_id

            ent = ent_reg.async_get(eid)
            if ent is not None and ent.platform == DOMAIN:
                continue
            if include_entities and eid not in include_entities:
                continue
            if eid in exclude_entities:
                continue
            if include_patterns and not _match_any(eid, include_patterns):
                continue
            if exclude_patterns and _match_any(eid, exclude_patterns):
                continue

            reg_dc = None
            if ent is not None:
                reg_dc = ent.device_class or ent.original_device_class
            if not _is_battery_entity(st, heuristic, reg_dc):
                continue

            attrs = st.attributes or {}
            available = st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
            value = _safe_float(st.state) if available else None

            device_id = None
            device_name = None
            if ent and ent.device_id:
                device_id = ent.device_id
                dev = dev_reg.async_get(device_id)
                if dev:
                    device_name = dev.name_by_user or dev.name

            snap = BatterySnapshot(
                entity_id=eid,
                name=str(attrs.get("friendly_name", eid)),
                value=value,
                available=available,
                unit=attrs.get("unit_of_measurement"),
                last_changed=st.last_changed.isoformat(),
                device_class=attrs.get("device_class") or reg_dc,
                device_id=device_id,
                device_name=device_name,
            )

            if available and value is not None:
                prev = self._last_valid_snapshots.get(eid)
                if prev is None or prev[0].value != value:
                    cache_changed = True
                self._last_valid_snapshots[eid] = (snap, now)
            else:
                snap = self._apply_retention(snap, treat_unavailable_as_zero)

            batteries.append(snap)
            seen.add(eid)

        # Entities that disappeared from the state machine but are still cached.
        for eid, (cached, _) in self._last_valid_snapshots.items():
            if eid in seen:
                continue
            batteries.append(
                BatterySnapshot(
                    **{**cached.__dict__, "available": False, "retained": True}
                )
            )

        batteries.sort(key=lambda s: (s.value is None, s.value if s.value is not None else 9999, s.entity_id))

        valid = [b for b in batteries if b.value is not None]
        unavailable = [b for b in batteries if not b.available]
        low = [b for b in valid if b.value <= threshold]
        critical = [b for b in valid if b.value <= critical_threshold]
        zero = [b for b in valid if b.value == 0]

        candidates = [b for b in valid if b.value > 0] if ignore_zero_for_lowest else valid
        lowest = min(candidates, key=lambda b: b.value) if candidates else None

        valid_total = len(valid)
        low_percent = round(len(low) / valid_total * 100.0, 1) if valid_total else 0.0
        zero_percent = round(len(zero) / valid_total * 100.0, 1) if valid_total else 0.0

        low_list_text = " | ".join(
            f"{battery_emoji(b.value, threshold, critical_threshold)} {b.display_name}: {int(b.value)}%"
            for b in low
        )

        low_device_keys = {b.device_id or b.entity_id for b in low}

        if zero or critical:
            status = STATUS_CRITICAL
        elif low:
            status = STATUS_WARNING
        else:
            status = STATUS_OK

        zero_changed = self._handle_zero_notifications(notify_on_zero, batteries, zero)
        if cache_changed or zero_changed:
            self._schedule_save()

        return {
            "critical_threshold": critical_threshold,
            "threshold": threshold,
            "total": len(batteries),
            "valid_total": valid_total,
            "low": low,
            "low_count": len(low),
            "critical": critical,
            "critical_count": len(critical),
            "low_devices_count": len(low_device_keys),
            "zero": zero,
            "zero_count": len(zero),
            "unavailable": unavailable,
            "unavailable_count": len(unavailable),
            "low_percent": low_percent,
            "zero_percent": zero_percent,
            "lowest": lowest,
            "all": batteries,
            "low_list_text": low_list_text,
            "status": status,
            "ignore_zero_for_lowest": ignore_zero_for_lowest,
            "notify_on_zero": notify_on_zero,
            "treat_unavailable_as_zero": treat_unavailable_as_zero,
            "unavailable_retention_hours": retention_hours,
        }

    # --------------------------------------------------------------- helpers
    def _apply_retention(self, snap: BatterySnapshot, treat_unavailable_as_zero: bool) -> BatterySnapshot:
        """Fill in a value for an unavailable entity from cache or option."""
        cached = self._last_valid_snapshots.get(snap.entity_id)
        if cached is not None:
            snap.value = cached[0].value
            snap.retained = True
            return snap
        if treat_unavailable_as_zero:
            snap.value = 0.0
            snap.assumed_zero = True
        return snap

    def _texts(self) -> dict[str, str]:
        lang = (self.hass.config.language or "en").split("-")[0].lower()
        return _NOTIFICATION_TEXTS.get(lang, _NOTIFICATION_TEXTS["en"])

    def _handle_zero_notifications(
        self, notify_on_zero: bool, batteries: list[BatterySnapshot], zero: list[BatterySnapshot]
    ) -> bool:
        """Manage the 0% persistent notification. Returns True if the tracked set changed."""
        zero_now = {b.entity_id for b in zero}
        by_id = {b.entity_id: b for b in batteries}

        # Entities previously at 0% that are now unavailable with no value
        # (cache expired and option disabled): keep them pending, never
        # report them as "resolved" until they really come back above 0%.
        pending = {
            eid
            for eid in self._last_zero_set
            if eid in by_id and not by_id[eid].available and by_id[eid].value is None
        }
        tracked = zero_now | pending

        changed = tracked != self._last_zero_set
        if not notify_on_zero:
            self._last_zero_set = tracked
            return changed

        nid = f"battery_monitor_zero_{self.entry.entry_id}"
        nid_resolved = f"battery_monitor_zero_resolved_{self.entry.entry_id}"
        t = self._texts()

        if tracked:
            if tracked != self._last_zero_set:
                lines = []
                for eid in sorted(tracked):
                    b = by_id.get(eid)
                    label = b.display_name if b else eid
                    hint = f" {t['unavailable_hint']}" if (b and not b.available) else ""
                    lines.append(f"- **{label}** (`{eid}`){hint}")
                persistent_notification.async_create(
                    self.hass,
                    f"{t['zero_body']}\n" + "\n".join(lines),
                    title=t["zero_title"],
                    notification_id=nid,
                )
        elif self._last_zero_set:
            persistent_notification.async_dismiss(self.hass, nid)
            persistent_notification.async_create(
                self.hass, t["resolved_body"], title=t["resolved_title"], notification_id=nid_resolved
            )

        self._last_zero_set = tracked
        return changed
