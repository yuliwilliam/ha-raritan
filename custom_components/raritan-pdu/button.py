from typing import Any

from homeassistant.components.button import ButtonEntityDescription, ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RaritanPDUCoordinator

PDU_BUTTON_DESCRIPTIONS = (
    ButtonEntityDescription(
        key="power_cycle",
        name="Power cycle",
        device_class=ButtonDeviceClass.RESTART,
        icon="mdi:restart",
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Raritan PDU sensor platform."""
    coordinator: RaritanPDUCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for outlet in coordinator.pdu.outlets:
        for description in PDU_BUTTON_DESCRIPTIONS:
            entities.append(RaritanPduSwitch(coordinator, description, outlet.index))

    async_add_entities(entities)


class RaritanPduSwitch(CoordinatorEntity, ButtonEntity):

    def __init__(self, coordinator: RaritanPDUCoordinator, description: ButtonEntityDescription, outlet_index: int):
        super().__init__(coordinator)

        self.outlet_index = outlet_index
        self.entity_description = description
        self._attr_device_info = coordinator.device_info

        self._attr_unique_id = f"outlet_{self.outlet_index}_{description.key}"
        self._attr_name = f"{self.coordinator.pdu.get_outlet_by_index(self.outlet_index).get_outlet_index_and_label()} {description.key.replace('_', ' ')}"

    async def async_press(self, **kwargs: Any) -> None:
        """Power cycle outlet"""
        await self.coordinator.pdu.get_outlet_by_index(self.outlet_index).power_cycle()
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """The outlet can be power cycled when it is on."""
        return self.coordinator.data[self.outlet_index]["operational_state"] == "on"
