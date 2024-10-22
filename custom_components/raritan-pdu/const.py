import logging
from typing import Final

from homeassistant.const import Platform

_LOGGER = logging.getLogger(__package__)

DOMAIN: Final = "raritan_pdu"
MANUFACTURER: Final = "Raritan"

CONF_READ_COMMUNITY: Final = "read community"
CONF_WRITE_COMMUNITY: Final = "write community"
CONF_POLLING_INTERVAL: Final = "polling interval(seconds)"

MIB_SOURCE_DIR: Final = f"./custom_components/{DOMAIN}/mibs"

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]
