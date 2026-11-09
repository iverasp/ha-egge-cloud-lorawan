"""Share egge.cloud device updates across platforms."""

import logging
from typing import override

from homeassistant.components.lorawan import device_identifier
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, MANUFACTURER
from .models import EggeCloudDevice

_LOGGER = logging.getLogger(__name__)


class EggeCloudCoordinator(DataUpdateCoordinator[EggeCloudDevice]):
    """Distribute push updates from one device."""

    def __init__(self, hass: HomeAssistant, device: EggeCloudDevice) -> None:
        """Subscribe once to the device model."""
        super().__init__(
            hass,
            _LOGGER,
            # DeviceManager owns the coordinator's lifecycle.
            config_entry=None,
            name=device.descriptor.name,
        )
        self.async_set_updated_data(device)
        self._unsubscribe = device.add_update_listener(self._async_device_updated)

    @property
    def device_info(self) -> DeviceInfo:
        """Describe this device for its entities."""
        return DeviceInfo(
            identifiers={device_identifier(DOMAIN, self.data)},
            name=self.data.descriptor.name,
            manufacturer=MANUFACTURER,
            model=self.data.MODEL_NAME,
            model_id=self.data.MODEL_ID,
        )

    @callback
    def _async_device_updated(self) -> None:
        self.async_set_updated_data(self.data)

    @override
    async def async_shutdown(self) -> None:
        """Release the model subscription when its collection retires it."""
        self._unsubscribe()
        await super().async_shutdown()
