"""Config flow for Xiaomi Mi Smart Pedestal Fan."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from miio import Device, DeviceException

from .const import (
    CONF_FIRMWARE_VERSION,
    CONF_HARDWARE_VERSION,
    CONF_MAC,
    CONF_MODEL,
    CONF_PRESET_MODES_OVERRIDE,
    CONF_RETRIES,
    DEFAULT_NAME,
    DEFAULT_RETRIES,
    DOMAIN,
    MODEL_FAN_1C,
    MODEL_FAN_LESHOW_SS4,
    MODEL_FAN_P10,
    MODEL_FAN_P11,
    MODEL_FAN_P15,
    MODEL_FAN_P18,
    MODEL_FAN_P30,
    MODEL_FAN_P33,
    MODEL_FAN_P39,
    MODEL_FAN_P5,
    MODEL_FAN_P70,
    MODEL_FAN_P76,
    MODEL_FAN_P8,
    MODEL_FAN_P9,
    MODEL_FAN_SA1,
    MODEL_FAN_V2,
    MODEL_FAN_V3,
    MODEL_FAN_ZA1,
    MODEL_FAN_ZA3,
    MODEL_FAN_ZA4,
    MODEL_FAN_ZA5,
)

_LOGGER = logging.getLogger(__name__)

SUPPORTED_MODELS = [
    MODEL_FAN_V2,
    MODEL_FAN_V3,
    MODEL_FAN_SA1,
    MODEL_FAN_ZA1,
    MODEL_FAN_ZA3,
    MODEL_FAN_ZA4,
    MODEL_FAN_ZA5,
    MODEL_FAN_P5,
    MODEL_FAN_P8,
    MODEL_FAN_P9,
    MODEL_FAN_P10,
    MODEL_FAN_P11,
    MODEL_FAN_P15,
    MODEL_FAN_P18,
    MODEL_FAN_P30,
    MODEL_FAN_P33,
    MODEL_FAN_P39,
    MODEL_FAN_P76,
    MODEL_FAN_P70,
    MODEL_FAN_LESHOW_SS4,
    MODEL_FAN_1C,
]

PRESET_MODE_OPTIONS = ["Level 1", "Level 2", "Level 3", "Level 4"]

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_MODEL): vol.In(SUPPORTED_MODELS),
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): int,
    }
)


class XiaomiFanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xiaomi Mi Smart Pedestal Fan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN]
            model = user_input.get(CONF_MODEL)

            try:
                miio_device = Device(host, token)
                device_info = await self.hass.async_add_executor_job(miio_device.info)
                mac = device_info.mac_address
                firmware_version = device_info.firmware_version
                hardware_version = device_info.hardware_version
                if model is None:
                    model = device_info.model
                _LOGGER.info(
                    "%s %s %s detected",
                    model,
                    firmware_version,
                    hardware_version,
                )
            except DeviceException:
                errors["base"] = "cannot_connect"
                mac = None
                firmware_version = None
                hardware_version = None

            if not errors:
                await self.async_set_unique_id(mac or host)
                self._abort_if_unique_id_configured()

                data = {
                    CONF_HOST: host,
                    CONF_TOKEN: token,
                    CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                    CONF_MODEL: model,
                    CONF_RETRIES: user_input.get(CONF_RETRIES, DEFAULT_RETRIES),
                }
                if mac:
                    data[CONF_MAC] = mac
                if firmware_version:
                    data[CONF_FIRMWARE_VERSION] = firmware_version
                if hardware_version:
                    data[CONF_HARDWARE_VERSION] = hardware_version

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Handle reconfiguration of an existing entry."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN]
            model = user_input.get(CONF_MODEL)

            try:
                miio_device = Device(host, token)
                device_info = await self.hass.async_add_executor_job(miio_device.info)
                mac = device_info.mac_address
                firmware_version = device_info.firmware_version
                hardware_version = device_info.hardware_version
                if model is None:
                    model = device_info.model
            except DeviceException:
                errors["base"] = "cannot_connect"
                mac = None
                firmware_version = None
                hardware_version = None

            if not errors:
                new_data = {
                    **entry.data,
                    CONF_HOST: host,
                    CONF_TOKEN: token,
                    CONF_MODEL: model,
                }
                if mac:
                    new_data[CONF_MAC] = mac
                if firmware_version:
                    new_data[CONF_FIRMWARE_VERSION] = firmware_version
                if hardware_version:
                    new_data[CONF_HARDWARE_VERSION] = hardware_version

                return self.async_update_reload_and_abort(
                    entry,
                    data=new_data,
                )

        reconfigure_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST, "")): str,
                vol.Required(CONF_TOKEN, default=entry.data.get(CONF_TOKEN, "")): vol.All(
                    str, vol.Length(min=32, max=32)
                ),
                vol.Optional(CONF_MODEL, default=entry.data.get(CONF_MODEL)): vol.In(
                    SUPPORTED_MODELS
                ),
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=reconfigure_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return XiaomiFanOptionsFlow(config_entry)


class XiaomiFanOptionsFlow(OptionsFlow):
    """Handle options for Xiaomi Fan."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_override = self.config_entry.options.get(CONF_PRESET_MODES_OVERRIDE, [])
        if isinstance(current_override, list):
            current_selection = current_override
        else:
            current_selection = []

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PRESET_MODES_OVERRIDE,
                        default=current_selection,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=PRESET_MODE_OPTIONS,
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )
