"""Raritan PDU Integration."""
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

from .raritan_pdu import RaritanPDU
from .const import _LOGGER, DOMAIN, PLATFORMS, CONF_COMMUNITY



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Raritan PDU from a config entry."""
    # Set up the sensor platform

    pdu = RaritanPDU(entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_COMMUNITY])
    if not await pdu.authenticate():
        _LOGGER.error("Failed to connect to Raritan PDU at %s", entry.data[CONF_HOST])
        raise ConfigEntryNotReady("Unable to connect")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = pdu

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Raritan PDU config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS)
    return True
