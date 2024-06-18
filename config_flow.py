from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, ConfigEntry, OptionsFlow

from .const import DOMAIN

import voluptuous as vol


class HABlueLinkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 0
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:

        data_schema = {
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("pin"): str
        }

        if user_input is not None:
            return self.async_create_entry(title=user_input['username'], data=user_input)

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))
