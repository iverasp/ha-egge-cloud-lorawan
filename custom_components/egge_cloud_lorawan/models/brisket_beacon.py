"""Brisket Beacon smoker thermometer.

fPort 1 payload (6 bytes, big-endian), see brisket-beacon/src/uplink.h:
  [0..1] external temp, int16, 0.1 C (0x8000 = probe not connected)
  [2..3] internal temp, int16, 0.1 C (0x8000 = probe not connected)
  [4]    flags: bit0 rapid rise external, bit1 rapid rise internal, bit2 heartbeat
  [5]    battery voltage, uint8, 20 mV units (0 = unknown)
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from lorawan_connection import DeviceDescriptor, Unsubscribe, notify, subscribe

from .base import EggeCloudDevice

PAYLOAD_LEN = 6
TEMP_NONE = -0x8000

FLAG_RAPID_EXTERNAL = 0x01
FLAG_RAPID_INTERNAL = 0x02
FLAG_HEARTBEAT = 0x04


@dataclass(frozen=True, slots=True)
class Reading:
    """One decoded uplink."""

    external: float | None
    internal: float | None
    rapid_rise_external: bool
    rapid_rise_internal: bool
    heartbeat: bool
    battery_voltage: float | None


def decode(data: bytes) -> Reading:
    """Decode a fPort 1 payload; raise ValueError on malformed data."""
    if len(data) != PAYLOAD_LEN:
        raise ValueError(f"Expected {PAYLOAD_LEN} bytes, got {len(data)}")

    def temp(raw: bytes) -> float | None:
        value = int.from_bytes(raw, "big", signed=True)
        return None if value == TEMP_NONE else value / 10

    flags = data[4]
    return Reading(
        external=temp(data[0:2]),
        internal=temp(data[2:4]),
        rapid_rise_external=bool(flags & FLAG_RAPID_EXTERNAL),
        rapid_rise_internal=bool(flags & FLAG_RAPID_INTERNAL),
        heartbeat=bool(flags & FLAG_HEARTBEAT),
        battery_voltage=round(data[5] * 0.02, 2) if data[5] else None,
    )


class BrisketBeacon(EggeCloudDevice):
    """Latest temperatures and battery voltage, plus rapid-rise notifications."""

    MODEL_ID = "brisket-beacon"
    MODEL_NAME = "Brisket Beacon"

    def __init__(self, descriptor: DeviceDescriptor) -> None:
        super().__init__(descriptor)
        self.reading: Reading | None = None
        self._rapid_rise_listeners: list[Callable[[str], None]] = []

    @property
    def external_temperature(self) -> float | None:
        """External (meat) probe temperature in degrees Celsius."""
        return self.reading.external if self.reading else None

    @property
    def internal_temperature(self) -> float | None:
        """Internal (pit) probe temperature in degrees Celsius."""
        return self.reading.internal if self.reading else None

    @property
    def battery_voltage(self) -> float | None:
        """Battery voltage in volts."""
        return self.reading.battery_voltage if self.reading else None

    def add_rapid_rise_listener(self, listener: Callable[[str], None]) -> Unsubscribe:
        """Call listener with "external" or "internal" for each rapid-rise uplink."""
        return subscribe(self._rapid_rise_listeners, listener)

    @override
    def decode_uplink(self, f_port: int, data: bytes) -> None:
        self.reading = reading = decode(data)
        if reading.rapid_rise_external:
            notify(self._rapid_rise_listeners, "external")
        if reading.rapid_rise_internal:
            notify(self._rapid_rise_listeners, "internal")

    @override
    def close(self) -> None:
        super().close()
        self._rapid_rise_listeners.clear()
