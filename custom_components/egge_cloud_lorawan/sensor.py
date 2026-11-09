"""Sensors for egge.cloud devices."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.lorawan import LoRaWANEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EggeCloudConfigEntry
from .coordinator import EggeCloudCoordinator
from .models import BrisketBeacon, EggeCloudDevice

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EggeCloudSensorDescription[DeviceT: EggeCloudDevice](SensorEntityDescription):
    """Select a value from the device models it applies to."""

    device_types: tuple[type[DeviceT], ...]
    value_fn: Callable[[DeviceT], float | None]


DESCRIPTIONS: tuple[EggeCloudSensorDescription[Any], ...] = (
    EggeCloudSensorDescription[BrisketBeacon](
        key="external_temperature",
        translation_key="external_temperature",
        device_types=(BrisketBeacon,),
        value_fn=lambda device: device.external_temperature,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    EggeCloudSensorDescription[BrisketBeacon](
        key="internal_temperature",
        translation_key="internal_temperature",
        device_types=(BrisketBeacon,),
        value_fn=lambda device: device.internal_temperature,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    EggeCloudSensorDescription[BrisketBeacon](
        key="battery_voltage",
        device_types=(BrisketBeacon,),
        value_fn=lambda device: device.battery_voltage,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EggeCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors for existing and newly discovered devices."""

    @callback
    def added(coordinator: EggeCloudCoordinator) -> None:
        async_add_entities(
            EggeCloudSensor(coordinator, description)
            for description in DESCRIPTIONS
            if isinstance(coordinator.data, description.device_types)
        )

    entry.async_on_unload(entry.runtime_data.subscribe_coordinator_added(added))


class EggeCloudSensor(LoRaWANEntity[EggeCloudDevice], SensorEntity):
    """An egge.cloud device measurement."""

    coordinator: EggeCloudCoordinator
    entity_description: EggeCloudSensorDescription[Any]

    @property
    @override
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    @property
    @override
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.device)
