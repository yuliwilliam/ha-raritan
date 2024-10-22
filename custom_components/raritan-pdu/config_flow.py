import voluptuous as vol
from homeassistant import exceptions
from homeassistant.config_entries import ConfigFlow

from .raritan_pdu import RaritanPDU
from .const import _LOGGER, DOMAIN, CONF_READ_COMMUNITY, CONF_WRITE_COMMUNITY, CONF_POLLING_INTERVAL, CONF_HOST, \
    CONF_PORT

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_PORT, default=161): int,
    vol.Optional(CONF_READ_COMMUNITY, default="public"): str,
    vol.Optional(CONF_WRITE_COMMUNITY, default="private"): str,
    vol.Optional(CONF_POLLING_INTERVAL, default=5): int,
})


class RaritanPDUConfigFlow(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST],
                                             CONF_PORT: user_input[CONF_PORT],
                                             CONF_READ_COMMUNITY: user_input[CONF_READ_COMMUNITY],
                                             CONF_WRITE_COMMUNITY: user_input[CONF_WRITE_COMMUNITY]})

            try:
                pdu = RaritanPDU(user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_READ_COMMUNITY],
                                 user_input[CONF_WRITE_COMMUNITY])
                if not await pdu.authenticate():
                    raise InvalidHost
                else:
                    await self.async_set_unique_id(pdu.unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=pdu.name, data=user_input)
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.error(f"Unexpected exception occurred: {str(e)}")
                errors["base"] = f"Unexpected exception occurred: {str(e)}"

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate this is an invalid host."""
