from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass, SensorEntityDescription, RestoreSensor, \
    UNIT_CONVERTERS
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower, PERCENTAGE, UnitOfEnergy, \
    UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import RaritanPDUCoordinator
from .const import DOMAIN, _LOGGER

PDU_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="cpu_temperature",
        name="CPU temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
)

# SensorEntityDescription.name will be assigned based on outlet label inside the sensor class
OUTLET_SENSOR_DESCRIPTIONS = (
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
    # To add new outlet sensor, uncomment/update the corresponding line in RaritanPDUOutlet.sensor_data
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Raritan PDU sensor platform."""
    coordinator: RaritanPDUCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for outlet in coordinator.pdu.outlets:
        for description in OUTLET_SENSOR_DESCRIPTIONS:
            entities.append(RaritanPduSensor(coordinator, description, outlet.index))

    for description in PDU_SENSOR_DESCRIPTIONS:
        entities.append(RaritanPduSensor(coordinator, description, 0))

    _LOGGER.info(f"Discovered {len(entities)} sensors")
    async_add_entities(entities)


class RaritanPduSensor(CoordinatorEntity, RestoreSensor):
    """Representation of an SNMP sensor for Raritan PDU."""

    def __init__(self, coordinator: RaritanPDUCoordinator, description: SensorEntityDescription, outlet_index: int):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.outlet_index = outlet_index
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self.is_outlet_sensor = self.outlet_index > 0  # outlet_index = 0 when this is a PDU level sensor

        if self.is_outlet_sensor:
            self._attr_unique_id = f"outlet_{self.outlet_index}_{description.key}"
            outlet_label = self.coordinator.pdu.get_data()[self.outlet_index]['label']
            sensor_name = description.key.replace('_', ' ')
            if outlet_label == f"Outlet {self.outlet_index}":
                self._attr_name = f"{outlet_label} {sensor_name}"
            else:
                self._attr_name = f"Outlet {self.outlet_index} {outlet_label} {sensor_name}"
        else:
            self._attr_unique_id = f"pdu_{description.key}"
            self._attr_name = description.name

    async def async_added_to_hass(self):
        """Restore the previous state when the entity is added to Home Assistant."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()

        _LOGGER.debug(f"Restoring sensor {self._attr_unique_id}'s to {str(last_state)}")

        # For now, only need to restore energy delivered
        if last_state is not None and self.is_outlet_sensor and self.entity_description.key == "energy_delivered":
            # Restore the last known state
            value = float(last_state.state)

            # state is stored in suggested_unit_of_measurement
            converter = UNIT_CONVERTERS[self.entity_description.device_class]
            converted_value = converter.convert(
                value,
                self.entity_description.suggested_unit_of_measurement,
                self.entity_description.native_unit_of_measurement,
            )

            _LOGGER.debug(f"Restored sensor {self._attr_unique_id}'s to {converted_value}")
            self.coordinator.pdu.get_outlet_by_index(self.outlet_index).initialize_energy_delivered(converted_value)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.is_outlet_sensor:
            self._attr_native_value = self.coordinator.data[self.outlet_index][self.entity_description.key]
        else:
            self._attr_native_value = self.coordinator.data[self.entity_description.key]

        self.async_write_ha_state()
