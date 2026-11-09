"""Shared base for egge.cloud LoRaWAN device models."""

from datetime import datetime
from typing import ClassVar, override

from lorawan_connection import Device, DeviceDescriptor, DeviceEvent, EventType

BRAND_ID = "egge-cloud"


class EggeCloudDevice(Device):
    """Route uplinks on the model's ports to decode_uplink, dropping stale ones.

    Subclasses set MODEL_ID and MODEL_NAME, and implement decode_uplink.
    """

    MODEL_ID: ClassVar[str]
    MODEL_NAME: ClassVar[str]
    PORTS: ClassVar[tuple[int, ...]] = (1,)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if model_id := cls.__dict__.get("MODEL_ID"):
            cls.identifiers = {"tts": (BRAND_ID, model_id)}

    def __init__(self, descriptor: DeviceDescriptor) -> None:
        super().__init__(descriptor)
        self.received_at: datetime | None = None

    @override
    def handle_event(self, event: DeviceEvent) -> None:
        if event.type != EventType.UPLINK or event.f_port not in self.PORTS:
            return
        if self.received_at is not None and event.received_at < self.received_at:
            return
        try:
            self.decode_uplink(event.f_port, event.data)
        except ValueError:
            return
        self.received_at = event.received_at
        self.notify()

    def decode_uplink(self, f_port: int, data: bytes) -> None:
        """Decode and store one uplink; raise ValueError on malformed data."""
        raise NotImplementedError
