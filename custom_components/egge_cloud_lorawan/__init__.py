"""Support egge.cloud devices over LoRaWAN."""

from lorawan_connection import ConnectionUnavailable

from homeassistant.components.lorawan import DeviceManager
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import EggeCloudCoordinator
from .models import EggeCloudCollection, EggeCloudDevice

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.EVENT, Platform.SENSOR]

type EggeCloudConfigEntry = ConfigEntry[
    DeviceManager[EggeCloudDevice, EggeCloudCoordinator]
]


async def async_setup_entry(hass: HomeAssistant, entry: EggeCloudConfigEntry) -> bool:
    """Set up egge.cloud devices across the available LoRaWAN connections."""
    manager = entry.runtime_data = DeviceManager(
        hass,
        entry,
        create_collection=EggeCloudCollection,
        create_coordinator=EggeCloudCoordinator,
    )
    entry.async_on_unload(manager.close)
    try:
        await manager.async_setup()
    except ConnectionUnavailable as err:
        raise ConfigEntryNotReady(str(err)) from err
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EggeCloudConfigEntry) -> bool:
    """Unload entities; the manager releases the collection and coordinators."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
