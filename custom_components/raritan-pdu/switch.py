from typing import Any

from homeassistant.components.switch import SwitchEntityDescription, SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RaritanPDUCoordinator

PDU_SWITCH_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="power_switch",
        name="Power switch",
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
            entities.append(RaritanPduSwitch(coordinator, description, outlet.index))

    async_add_entities(entities)


class RaritanPduSwitch(CoordinatorEntity, SwitchEntity):

    def __init__(self, coordinator: RaritanPDUCoordinator, description: SwitchEntityDescription, outlet_index: int):
        super().__init__(coordinator)

        self.outlet_index = outlet_index
        self.entity_description = description
        self._attr_device_info = coordinator.device_info

        self._attr_unique_id = f"outlet_{self.outlet_index}_{description.key}"
        outlet_label = self.coordinator.get_data_from_pdu()[self.outlet_index]['label']
        switch_name = description.key.replace('_', ' ')
        if outlet_label == f"Outlet {self.outlet_index}":
            self._attr_name = f"{outlet_label} {switch_name}"
        else:
            self._attr_name = f"Outlet {self.outlet_index} {outlet_label} {switch_name}"



    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.pdu.get_outlet_by_index(self.outlet_index).turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.pdu.get_outlet_by_index(self.outlet_index).turn_off()
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        """Get switch state."""
        return self.coordinator.data[self.outlet_index]["operational_state"] == "on"