"""egge.cloud LoRaWAN device models.

To add a device: subclass EggeCloudDevice in a new module, then list it in
EggeCloudCollection.DEVICES.
"""

from lorawan_connection import DeviceCollection

from .base import BRAND_ID, EggeCloudDevice
from .brisket_beacon import BrisketBeacon


class EggeCloudCollection(DeviceCollection[EggeCloudDevice]):
    """Discover egge.cloud devices by their TTS version identifiers."""

    DEVICES = (BrisketBeacon,)


__all__ = ["BRAND_ID", "BrisketBeacon", "EggeCloudCollection", "EggeCloudDevice"]
