# Creato da domoticafacile.it
from datetime import timedelta

DOMAIN = "battery_monitor"

CONF_THRESHOLD = "threshold"
CONF_CRITICAL_THRESHOLD = "critical_threshold"
CONF_INCLUDE_HEURISTIC = "include_heuristic"
CONF_SCAN_DOMAINS = "scan_domains"
CONF_EXCLUDE_PATTERNS = "exclude_patterns"
CONF_INCLUDE_PATTERNS = "include_patterns"

CONF_INCLUDE_ENTITIES = "include_entities"
CONF_EXCLUDE_ENTITIES = "exclude_entities"

CONF_IGNORE_ZERO_FOR_LOWEST = "ignore_zero_for_lowest"
CONF_NOTIFY_ON_ZERO = "notify_on_zero"
CONF_TREAT_UNAVAILABLE_AS_ZERO = "treat_unavailable_as_zero"

# Defaults
DEFAULT_THRESHOLD = 20
DEFAULT_CRITICAL_THRESHOLD = 10
DEFAULT_INCLUDE_HEURISTIC = True
DEFAULT_SCAN_DOMAINS: list[str] = ["sensor"]
DEFAULT_EXCLUDE_PATTERNS: list[str] = []
DEFAULT_INCLUDE_PATTERNS: list[str] = []

DEFAULT_INCLUDE_ENTITIES: list[str] = []
DEFAULT_EXCLUDE_ENTITIES: list[str] = []

DEFAULT_IGNORE_ZERO_FOR_LOWEST = True
DEFAULT_NOTIFY_ON_ZERO = True
DEFAULT_TREAT_UNAVAILABLE_AS_ZERO = False

# How long the last valid value of a battery is retained after it becomes
# unavailable (or disappears from the state machine).
RETAIN_UNAVAILABLE_FOR = timedelta(hours=24)

# Fallback poll interval; updates are normally event driven.
UPDATE_INTERVAL = timedelta(minutes=5)
# Debounce for state-change driven refreshes.
REFRESH_DEBOUNCE_SECONDS = 2.0

STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_CRITICAL = "CRITICAL"
