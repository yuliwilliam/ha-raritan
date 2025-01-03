"""Raritan PDU Integration."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import RaritanPDUCoordinator
from .raritan_pdu import RaritanPDU
from .const import _LOGGER, DOMAIN, PLATFORMS, CONF_READ_COMMUNITY, CONF_WRITE_COMMUNITY, CONF_POLLING_INTERVAL, \
    CONF_HOST, CONF_PORT


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Raritan PDU from a config entry."""
    # Set up the sensor platform

    pdu = RaritanPDU(entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_READ_COMMUNITY],
                     entry.data[CONF_WRITE_COMMUNITY])
    if not await pdu.authenticate():
        _LOGGER.error("Failed to connect to Raritan PDU at %s", entry.data[CONF_HOST])
        raise ConfigEntryNotReady("Unable to connect")

    # initial update
    await pdu.update_data()
    raritan_pdu_coordinator = RaritanPDUCoordinator(hass, pdu, entry.data[CONF_POLLING_INTERVAL])
    await raritan_pdu_coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = raritan_pdu_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Raritan PDU config entry."""
    unload_ok = True
    for platform in PLATFORMS:
        unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, platform)

    return unload_ok
