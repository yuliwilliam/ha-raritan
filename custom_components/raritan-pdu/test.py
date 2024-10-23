import asyncio
from time import sleep

from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, UnitOfElectricCurrent

from raritan_pdu import RaritanPDU, RaritanPDUOutlet
from sensor import RaritanPDUSensor


class Mock:
    def __init__(self, pdu):
        self.pdu = pdu

async def main():

    device = RaritanPDU("192.168.40.14", 161, "public", "private")
    await device.authenticate()
    await device.update_data()
    # # print(device.get_data())
    #
    # outlet: RaritanPDUOutlet = device.outlets[10]
    # print(outlet.get_data())
    # result = await outlet.power_cycle()
    # print(outlet.get_data())
    #
    # asyncio.sleep(2)
    # await device.update_data()
    # print(outlet.get_data())


    desc =       SensorEntityDescription(
        key="current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    )

    # raritan_pdu_coordinator = RaritanPDUCoordinator(hass, pdu, entry.data[CONF_POLLING_INTERVAL])

    sensor = RaritanPDUSensor(Mock(device), desc, 17)
    print(sensor.name)





if __name__ == '__main__':
    asyncio.run(main())
