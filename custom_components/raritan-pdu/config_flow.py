import voluptuous as vol
from homeassistant import exceptions
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_PORT, CONF_HOST

from .raritan_pdu import RaritanPDU
from .const import _LOGGER, DOMAIN, CONF_COMMUNITY

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_PORT, default=161): int,
    vol.Optional(CONF_COMMUNITY, default="public"): str,
})


class RaritanPDUConfigFlow(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST],
                                             CONF_PORT: user_input[CONF_PORT],
                                             CONF_COMMUNITY: user_input[CONF_COMMUNITY]})

            try:
                pdu = RaritanPDU(user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_COMMUNITY])
                if not await pdu.authenticate():
                    raise InvalidHost
                else:
                    await pdu.initialize()
                    await self.async_set_unique_id(pdu.key)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=pdu.name, data=user_input)
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate this is a invalid host."""
