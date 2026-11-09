"""Tests for the Brisket Beacon device model, using the lorawan-connection mock."""

import asyncio
from datetime import UTC, datetime

import pytest
from lorawan_connection import DeviceDescriptor, UplinkEvent
from lorawan_connection.mock import MockConnection

from egge_models import BRAND_ID, BrisketBeacon, EggeCloudCollection
from egge_models.brisket_beacon import decode

NOW = datetime.now(UTC)
DESCRIPTOR = DeviceDescriptor(
    "ttn",
    "70b3d57ed0000001",
    "Smoker",
    "brisket-app",
    "",
    model_id=BrisketBeacon.MODEL_ID,
    brand_id=BRAND_ID,
    stack="tts",
)
OTHER = DeviceDescriptor(
    "ttn", "70b3d57ed0000002", "Other", "brisket-app", "", stack="tts"
)


def test_decode() -> None:
    reading = decode(bytes([0x03, 0x84, 0xFF, 0xF6, 0x05, 0xD2]))
    assert reading.external == 90.0
    assert reading.internal == -1.0
    assert reading.rapid_rise_external
    assert not reading.rapid_rise_internal
    assert reading.heartbeat
    assert reading.battery_voltage == 4.2


def test_decode_disconnected_and_unknown_battery() -> None:
    reading = decode(bytes([0x80, 0x00, 0x80, 0x00, 0x00, 0x00]))
    assert reading.external is None
    assert reading.internal is None
    assert reading.battery_voltage is None


def test_decode_wrong_length() -> None:
    with pytest.raises(ValueError):
        decode(bytes(5))


def test_collection() -> None:
    async def run() -> None:
        connection = MockConnection([DESCRIPTOR, OTHER], stack_type="tts")
        collection = EggeCloudCollection(connection)
        await collection.async_setup()
        assert list(collection.devices) == [DESCRIPTOR.dev_eui]
        device = collection.devices[DESCRIPTOR.dev_eui]
        assert isinstance(device, BrisketBeacon)

        updates: list[None] = []
        rises: list[str] = []
        device.add_update_listener(lambda: updates.append(None))
        device.add_rapid_rise_listener(rises.append)

        connection.emit(
            UplinkEvent(received_at=NOW, descriptor=DESCRIPTOR, data=bytes([0, 250, 0, 100, 2, 200]))
        )
        assert device.external_temperature == 25.0
        assert device.internal_temperature == 10.0
        assert device.battery_voltage == 4.0
        assert rises == ["internal"]
        assert len(updates) == 1

        connection.emit(UplinkEvent(received_at=NOW, descriptor=DESCRIPTOR, data=b"\x00", f_port=1))
        connection.emit(
            UplinkEvent(received_at=NOW, descriptor=DESCRIPTOR, data=bytes(6), f_port=2)
        )
        assert len(updates) == 1
        collection.close()

    asyncio.run(run())



def test_identifiers() -> None:
    assert BrisketBeacon.identifiers == {"tts": ("egge-cloud", "brisket-beacon")}
