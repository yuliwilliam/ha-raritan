from __future__ import annotations

from typing import Optional

from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .raritan_pdu import RaritanPDUOutlet
from .coordinator import RaritanPDUCoordinator


class RaritanPDUEntity(CoordinatorEntity, Entity):
    """Dyson entity base class."""

    def __init__(self, coordinator: RaritanPDUCoordinator,
                 description: SensorEntityDescription | SwitchEntityDescription | ButtonEntityDescription,
                 outlet_index: int):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self.outlet_index = outlet_index

        # outlet_index = 0 when this is a PDU level sensor
        self.outlet: RaritanPDUOutlet = None
        if self.outlet_index > 0:
            self.outlet = self.coordinator.pdu.get_outlet_by_index(self.outlet_index)

    @property
    def has_entity_name(self) -> bool:
        """Return if the name of the entity is describing only the entity itself."""
        return True

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.entity_description.name is not None:
            return self.entity_description.name

        formatted_description_key = self.entity_description.key.replace('_', ' ')
        if self.outlet is not None:
            outlet_label = self.outlet.sensor_data['label']
            name_prefix = f"Outlet {self.outlet_index}"
            if outlet_label != f"Outlet {self.outlet_index}":
                name_prefix = f"{name_prefix} {outlet_label}"

            return f"{name_prefix} {formatted_description_key}"
        else:
            return formatted_description_key

    @property
    def unique_id(self) -> str:
        """Return the entity unique id."""
        return f"{self.coordinator.pdu.name}-outlet-{self.outlet_index}-{self.entity_description.key}"

    @property
    def device_info(self) -> dict:
        """Return device info of the entity."""
        return self.coordinator.device_info
