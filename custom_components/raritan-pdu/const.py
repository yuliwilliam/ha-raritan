import logging
from typing import Final

from homeassistant.const import Platform

_LOGGER = logging.getLogger(__package__)

DOMAIN: Final = "raritan_pdu"
MANUFACTURER: Final = "Raritan"

CONF_COMMUNITY: Final = "community"

MIB_SOURCE_DIR: Final = f"./custom_components/{DOMAIN}/mibs"

UPDATE_INTERVAL: float = 1.0

# PLATFORMS = [Platform.SENSOR, Platform.SWITCH]
PLATFORMS = [Platform.SENSOR]
