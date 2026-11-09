"""Events for egge.cloud devices."""

from typing import override

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.components.lorawan import LoRaWANEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EggeCloudConfigEntry
from .coordinator import EggeCloudCoordinator
from .models import BrisketBeacon

PARALLEL_UPDATES = 0

EVENT_RAPID_RISE = "rapid_rise"

RAPID_RISE_DESCRIPTIONS: tuple[EventEntityDescription, ...] = (
    EventEntityDescription(
        key="external",
        translation_key="external_rapid_rise",
        event_types=[EVENT_RAPID_RISE],
    ),
    EventEntityDescription(
        key="internal",
        translation_key="internal_rapid_rise",
        event_types=[EVENT_RAPID_RISE],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EggeCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up events for existing and newly discovered devices."""

    @callback
    def added(coordinator: EggeCloudCoordinator) -> None:
        if isinstance(coordinator.data, BrisketBeacon):
            async_add_entities(
                BrisketBeaconRapidRiseEvent(coordinator, description)
                for description in RAPID_RISE_DESCRIPTIONS
            )

    entry.async_on_unload(entry.runtime_data.subscribe_coordinator_added(added))


class BrisketBeaconRapidRiseEvent(LoRaWANEntity[BrisketBeacon], EventEntity):
    """Fires when a Brisket Beacon probe reports a rapid temperature rise."""

    coordinator: EggeCloudCoordinator

    @property
    @override
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    @override
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.device.add_rapid_rise_listener(self._rapid_rise))

    @callback
    def _rapid_rise(self, probe: str) -> None:
        if probe != self.entity_description.key:
            return
        self._trigger_event(
            EVENT_RAPID_RISE,
            {"temperature": getattr(self.device.reading, probe, None)},
        )
        self.async_write_ha_state()
