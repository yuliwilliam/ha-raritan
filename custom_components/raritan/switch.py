from typing import Any

from homeassistant.components.switch import SwitchEntityDescription, SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .entity import RaritanPDUEntity
from .const import DOMAIN
from .coordinator import RaritanPDUCoordinator

PDU_SWITCH_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="power_switch",
        device_class=SwitchDeviceClass.OUTLET,
        icon="mdi:power-socket-us",
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Raritan PDU sensor platform."""
    coordinator: RaritanPDUCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for outlet in coordinator.pdu.outlets:
        for description in PDU_SWITCH_DESCRIPTIONS:
            entities.append(RaritanPDUSwitch(coordinator, description, outlet.index))

    async_add_entities(entities)


class RaritanPDUSwitch(RaritanPDUEntity, SwitchEntity):

    def __init__(self, coordinator: RaritanPDUCoordinator, description: SwitchEntityDescription, outlet_index: int):
        RaritanPDUEntity.__init__(self, coordinator, description, outlet_index)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the outlet on."""
        await self.outlet.power_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the outlet off."""
        await self.outlet.power_off()
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        """Is the outlet on."""
        return self.coordinator.data[self.outlet_index]["operational_state"] == "on"

    @property
    def available(self) -> bool:
        """The outlet can be turned on/off when it is not in power cycling or error."""
        return self.coordinator.data[self.outlet_index]["operational_state"] == "on" or \
            self.coordinator.data[self.outlet_index]["operational_state"] == "off"
