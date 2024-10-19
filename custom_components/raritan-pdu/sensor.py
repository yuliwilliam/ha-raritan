from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, SensorEntityDescription
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfElectricPotential
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, _LOGGER
from .raritan_pdu import RaritanPDU, RaritanPDUOutlet

SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="max_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="watt_hours",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    )
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Raritan PDU sensor platform."""
    pdu: RaritanPDU = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for outlet in pdu.outlets:
        for sensor_description in SENSOR_DESCRIPTIONS:
            entities.append(RaritanPduOutletSensor(outlet, sensor_description))

    _LOGGER.info(f"Discovered {len(entities)} sensors")
    async_add_entities(entities)


class RaritanPduOutletSensor(SensorEntity):
    """Representation of an SNMP sensor for Raritan PDU."""

    def __init__(self, outlet: RaritanPDUOutlet, description: SensorEntityDescription):
        """Initialize the sensor."""
        self._outlet = outlet
        self.entity_description = description
        self._attr_unique_id = f"{outlet.label}_{description.key}"

    async def async_update(self):
        try:
            await self._outlet.update_data(self.entity_description.key)
            self._attr_native_value = self._outlet.get_data(self.entity_description.key)
        except Exception as e:
            _LOGGER.error("Failed to update SNMP data: %s", e)
