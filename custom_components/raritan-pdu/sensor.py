from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, SensorEntityDescription
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower, PERCENTAGE, UnitOfEnergy
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, _LOGGER, MANUFACTURER
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
        key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),
    SensorEntityDescription(
        key="active_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
    ),
    SensorEntityDescription(
        key="power_factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:angle-acute",
    ),
    # SensorEntityDescription(
    #     key="watt_hours",
    #     device_class=SensorDeviceClass.ENERGY,
    #     native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
    #     state_class=SensorStateClass.TOTAL_INCREASING,
    #     icon="mdi:lightning-bolt",
    # )
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Raritan PDU sensor platform."""
    pdu: RaritanPDU = hass.data[DOMAIN][entry.entry_id]
    device_info = DeviceInfo(
        manufacturer=MANUFACTURER,
        identifiers={(DOMAIN, pdu.unique_id)},
        name=pdu.name
    )

    entities = []
    for outlet in pdu.outlets:
        for sensor_description in SENSOR_DESCRIPTIONS:
            entities.append(RaritanPduOutletSensor(outlet, sensor_description, device_info))

    _LOGGER.info(f"Discovered {len(entities)} sensors")
    async_add_entities(entities)


class RaritanPduOutletSensor(SensorEntity):
    """Representation of an SNMP sensor for Raritan PDU."""

    def __init__(self, outlet: RaritanPDUOutlet, description: SensorEntityDescription, device_info: DeviceInfo):
        """Initialize the sensor."""
        self._outlet = outlet
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{outlet.label}_{description.key}"

    async def async_update(self):
        try:
            await self._outlet.update_data(self.entity_description.key)
            self._attr_native_value = self._outlet.get_data(self.entity_description.key)
        except Exception as e:
            _LOGGER.error("Failed to update SNMP data: %s", e)
