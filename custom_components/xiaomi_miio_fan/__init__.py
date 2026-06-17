"""The Xiaomi Mi Smart Pedestal Fan integration."""

import asyncio
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xiaomi Fan from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        # Remove domain services only if no other entries remain
        if len(hass.config_entries.async_entries(DOMAIN)) <= 1:
            _remove_services(hass)

    return unload_ok


def _remove_services(hass: HomeAssistant) -> None:
    """Remove all domain services."""
    from .fan import SERVICE_TO_METHOD

    for service in SERVICE_TO_METHOD:
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
