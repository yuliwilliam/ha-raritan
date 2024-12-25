from typing import Any

from homeassistant.components.switch import SwitchEntityDescription, SwitchDeviceClass, SwitchEntity
from homeassistant.components.text import TextEntityDescription, TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .entity import RaritanPDUEntity
from .const import DOMAIN
from .coordinator import RaritanPDUCoordinator

OUTLET_TEXT_DESCRIPTIONS = (
    TextEntityDescription(
        key="label",
        icon="mdi:rename",
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Raritan PDU sensor platform."""
    coordinator: RaritanPDUCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for outlet in coordinator.pdu.outlets:
        for description in OUTLET_TEXT_DESCRIPTIONS:
            entities.append(RaritanPDUText(coordinator, description, outlet.index))

    async_add_entities(entities)


class RaritanPDUText(RaritanPDUEntity, TextEntity):

    def __init__(self, coordinator: RaritanPDUCoordinator, description: TextEntityDescription, outlet_index: int):
        RaritanPDUEntity.__init__(self, coordinator, description, outlet_index)

    @property
    def native_value(self):
        """Return the value reported by the text."""
        return self.coordinator.data[self.outlet_index]["label"]

    async def async_set_value(self, value: str):
        """Handle setting the value."""
        await self.outlet.set_label(value)
        await self.coordinator.async_request_refresh()
