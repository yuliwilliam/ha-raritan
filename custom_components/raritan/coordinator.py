from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .raritan_pdu import RaritanPDU
from .const import _LOGGER, DOMAIN, MANUFACTURER


class RaritanPDUCoordinator(DataUpdateCoordinator):
    def __init__(
            self,
            hass: HomeAssistant,
            pdu: RaritanPDU,
            polling_interval: int,
    ) -> None:
        """Initialise a custom coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_interval),
        )
        self.pdu: RaritanPDU = pdu
        self.device_id = self.pdu.unique_id
        self.device_info = self.build_device_info()

    def build_device_info(self) -> DeviceInfo:
        """Build Home Assistant device info from PDU metadata."""
        device_info = {
            "manufacturer": MANUFACTURER,
            "identifiers": {(DOMAIN, self.pdu.unique_id)},
            "name": self.pdu.name,
            "model": self.pdu.object_name,
        }

        if self.pdu.firmware_version:
            device_info["sw_version"] = self.pdu.firmware_version

        if self.pdu.hardware_version:
            device_info["hw_version"] = self.pdu.hardware_version

        if self.pdu.serial_number:
            device_info["serial_number"] = self.pdu.serial_number

        if self.pdu.mac_address:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self.pdu.mac_address)}

        if self.pdu.ip_address and self.pdu.ip_address != "0.0.0.0":
            device_info["configuration_url"] = f"http://{self.pdu.ip_address}"
        else:
            device_info["configuration_url"] = f"http://{self.pdu.host}"

        return DeviceInfo(**device_info)

    async def _async_update_data(self) -> dict:
        """Fetch the data from the device."""
        await self.pdu.update_data()
        self.device_info = self.build_device_info()

        return self.pdu.get_data()
