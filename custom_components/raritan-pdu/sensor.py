from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, SensorEntityDescription
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfElectricPotential
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, _LOGGER

from raritan_pdu import RaritanPDU, RaritanPDUOutlet


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
            sensor_description.key = f"{outlet.label} {sensor_description.key}"
            entities.append(RaritanPduOutletSensor(outlet, sensor_description))

    async_add_entities(entities)


class RaritanPduOutletSensor( SensorEntity):
    """Representation of an SNMP sensor for Raritan PDU."""

    def __init__(self, outlet: RaritanPDUOutlet, description: SensorEntityDescription):
        """Initialize the sensor."""
        self._outlet = outlet
        self.entity_description = description
        self._state = None

    async def async_update(self):
        try:
            data_name = self.entity_description.key.split(" ")[1]
            await self._outlet.update_data(data_name)
            self._state = self._outlet.get_data(data_name)
        except Exception as e:
            _LOGGER.error("Failed to update SNMP data: %s", e)
