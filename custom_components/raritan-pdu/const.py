import logging

from homeassistant.const import Platform

_LOGGER = logging.getLogger(__package__)

DOMAIN = "raritan_pdu"
MANUFACTURER = "Raritan"

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]