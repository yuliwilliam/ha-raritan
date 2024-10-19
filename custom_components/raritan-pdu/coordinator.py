from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .raritan_pdu import RaritanPDU
from .const import _LOGGER, DOMAIN, MANUFACTURER, UPDATE_INTERVAL


class RaritanPDUCoordinator(DataUpdateCoordinator):
    def __init__(
            self,
            hass: HomeAssistant,
            pdu: RaritanPDU,
    ) -> None:
        """Initialise a custom coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.pdu: RaritanPDU = pdu
        self.device_id = self.pdu.unique_id
        self.device_info = DeviceInfo(
            manufacturer=MANUFACTURER,
            identifiers={(DOMAIN, self.pdu.unique_id)},
            name=self.pdu.name
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
