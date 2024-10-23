from __future__ import annotations

from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .raritan_pdu import RaritanPDUOutlet
from .coordinator import RaritanPDUCoordinator
from .const import _LOGGER


class RaritanPDUEntity(CoordinatorEntity, Entity):
    """Dyson entity base class."""

    def __init__(self, coordinator: RaritanPDUCoordinator, description: EntityDescription, outlet_index: int):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self.outlet_index = outlet_index

        # outlet_index = 0 when this is a PDU level sensor
        self.outlet: RaritanPDUOutlet = None
        if self.outlet_index > 0:
            self.outlet = self.coordinator.pdu.get_outlet_by_index(self.outlet_index)

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        default_name = self.entity_description.key.replace('_', ' ')
        _LOGGER.debug(f"description {self.entity_description.key}, {default_name}, {self.entity_description.name}")
        if self.outlet is not None:
            outlet_label = self.outlet.sensor_data['label']
            name_prefix = f"Outlet {self.outlet_index}"
            if outlet_label != f"Outlet {self.outlet_index}":
                name_prefix = f"{self.coordinator.pdu.name} {name_prefix} {outlet_label}"
            return f"{self.coordinator.pdu.name} {name_prefix} {default_name}"
        else:
            return default_name

    @property
    def unique_id(self) -> str:
        """Return the entity unique id."""
        return f"{self.coordinator.pdu.name}-outlet-{self.outlet_index}-{self.entity_description.key}".replace(
            " ", "-").lower()

    @property
    def device_info(self) -> dict:
        """Return device info of the entity."""
        return self.coordinator.device_info
