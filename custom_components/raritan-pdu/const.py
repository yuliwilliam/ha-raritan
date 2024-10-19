import logging

from homeassistant.const import Platform

_LOGGER = logging.getLogger(__package__)

DOMAIN = "raritan_pdu"
MANUFACTURER = "Raritan"

CONF_COMMUNITY = "community"

MIB_SOURCE_DIR = f"./custom_components/{DOMAIN}/mibs"

# PLATFORMS = [Platform.SENSOR, Platform.SWITCH]
PLATFORMS = [Platform.SENSOR]