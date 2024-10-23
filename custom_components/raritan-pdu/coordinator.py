from datetime import timedelta

from homeassistant.core import HomeAssistant
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
        self.device_info = DeviceInfo(
            manufacturer=MANUFACTURER,
            identifiers={(DOMAIN, self.pdu.unique_id)},
            name=self.pdu.name,
            sw_version=self.pdu.firmware_version,
            model=self.pdu.model,
        )

    async def _async_update_data(self) -> dict:
        """Fetch the data from the device."""
        await self.pdu.update_data()
        self.device_info = DeviceInfo(
            manufacturer=MANUFACTURER,
            identifiers={(DOMAIN, self.pdu.unique_id)},
            name=self.pdu.name
        )

        return self.pdu.get_data()
