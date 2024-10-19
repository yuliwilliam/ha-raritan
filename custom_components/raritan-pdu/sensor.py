from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, SensorEntityDescription
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower, PERCENTAGE, UnitOfEnergy
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import RaritanPDUCoordinator
from .const import DOMAIN, _LOGGER

SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),
    SensorEntityDescription(
        key="active_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    SensorEntityDescription(
        key="power_factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:angle-acute",
    ),
    SensorEntityDescription(
        key="energy_delivered",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:lightning-bolt",
    )
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Raritan PDU sensor platform."""
    coordinator: RaritanPDUCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for outlet in coordinator.pdu.outlets:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(RaritanPduOutletSensor(coordinator, description, outlet.index))

    _LOGGER.info(f"Discovered {len(entities)} sensors")
    async_add_entities(entities)


class RaritanPduOutletSensor(CoordinatorEntity, SensorEntity):
    """Representation of an SNMP sensor for Raritan PDU."""

    def __init__(self, coordinator: RaritanPDUCoordinator, description: SensorEntityDescription, outlet_index: str):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.outlet_index = outlet_index
        self.entity_description = description
        self._attr_device_info = coordinator.device_info

        self._attr_unique_id = f"outlet_{self.outlet_index}_{description.key}"
        self._attr_name = f"{self.coordinator.get_data_from_pdu()[self.outlet_index]['label']} {description.key.replace('_', ' ')}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data[self.outlet_index][self.entity_description.key]
        self.async_write_ha_state()
