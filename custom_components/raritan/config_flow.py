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


def build_data_schema(user_input=None):
    """Build the data schema with optional defaults."""
    if user_input is None:
        return DATA_SCHEMA

    return vol.Schema({
        vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): str,
        vol.Optional(CONF_PORT, default=user_input.get(CONF_PORT, 161)): int,
        vol.Optional(CONF_READ_COMMUNITY, default=user_input.get(CONF_READ_COMMUNITY, "public")): str,
        vol.Optional(CONF_WRITE_COMMUNITY, default=user_input.get(CONF_WRITE_COMMUNITY, "private")): str,
        vol.Optional(CONF_POLLING_INTERVAL, default=user_input.get(CONF_POLLING_INTERVAL, 5)): int,
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
                pdu = await self.validate_input(user_input)
                await self.async_set_unique_id(pdu.unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=pdu.name, data=user_input)
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.error(f"Unexpected exception occurred: {str(e)}")
                errors["base"] = f"Unexpected exception occurred: {str(e)}"

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of an existing config entry."""
        entry = self._get_reconfigure_entry()
        errors = {}

        if user_input is not None:
            if self.entry_matches_existing_config(user_input, entry.entry_id):
                return self.async_abort(reason="already_configured")

            try:
                pdu = await self.validate_input(user_input)
                self.hass.config_entries.async_update_entry(entry, unique_id=pdu.unique_id)
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.error(f"Unexpected exception occurred: {str(e)}")
                errors["base"] = f"Unexpected exception occurred: {str(e)}"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=build_data_schema(entry.data),
            errors=errors,
        )

    async def validate_input(self, user_input):
        """Validate config flow input."""
        pdu = RaritanPDU(user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_READ_COMMUNITY],
                         user_input[CONF_WRITE_COMMUNITY])
        if not await pdu.authenticate():
            raise InvalidHost
        return pdu

    def entry_matches_existing_config(self, user_input, current_entry_id):
        """Return true if input matches another existing config entry."""
        for entry in self._async_current_entries():
            if entry.entry_id == current_entry_id:
                continue

            if all(entry.data.get(key) == user_input[key] for key in (
                    CONF_HOST,
                    CONF_PORT,
                    CONF_READ_COMMUNITY,
                    CONF_WRITE_COMMUNITY,
            )):
                return True

        return False


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate this is an invalid host."""
