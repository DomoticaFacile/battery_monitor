# Creato da domoticafacile.it
DOMAIN = "battery_monitor"

CONF_THRESHOLD = "threshold"
CONF_INCLUDE_HEURISTIC = "include_heuristic"
CONF_SCAN_DOMAINS = "scan_domains"
CONF_EXCLUDE_PATTERNS = "exclude_patterns"
CONF_INCLUDE_PATTERNS = "include_patterns"


CONF_INCLUDE_ENTITIES = "include_entities"
CONF_EXCLUDE_ENTITIES = "exclude_entities"


CONF_IGNORE_ZERO_FOR_LOWEST = "ignore_zero_for_lowest"
CONF_NOTIFY_ON_ZERO = "notify_on_zero"

DEFAULT_THRESHOLD = 20
DEFAULT_INCLUDE_HEURISTIC = True
DEFAULT_SCAN_DOMAINS = ["sensor"]
DEFAULT_EXCLUDE_PATTERNS = []
DEFAULT_INCLUDE_PATTERNS = []

DEFAULT_INCLUDE_ENTITIES: list[str] = []
DEFAULT_EXCLUDE_ENTITIES: list[str] = []

DEFAULT_IGNORE_ZERO_FOR_LOWEST = True
DEFAULT_NOTIFY_ON_ZERO = True