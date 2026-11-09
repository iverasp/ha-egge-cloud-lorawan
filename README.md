# egge.cloud for Home Assistant

A Home Assistant (2026.11+) LoRaWAN device integration for egge.cloud devices.
It uses the built-in `lorawan` integration and an existing The Things Network
connection.

## Supported devices

| Model | TTN model ID | Firmware |
| --- | --- | --- |
| Brisket Beacon | `brisket-beacon` | [brisket-beacon](../brisket-beacon) |

### Brisket Beacon

| Entity | Type | Notes |
| --- | --- | --- |
| External temperature | sensor (°C) | Meat probe. Unknown while the probe is unplugged. |
| Internal temperature | sensor (°C) | Pit probe. Unknown while the probe is unplugged. |
| Battery voltage | sensor (V, diagnostic) | Unknown when the device reports 0. |
| External rapid rise | event | Fires `rapid_rise` with a `temperature` attribute. |
| Internal rapid rise | event | Fires `rapid_rise` with a `temperature` attribute. |

Uplink: fPort 1, 6 bytes, big-endian, as defined in `brisket-beacon/src/uplink.h`.

| Bytes | Field |
| --- | --- |
| 0–1 | External temperature, int16, 0.1 °C (`0x8000` = not connected) |
| 2–3 | Internal temperature, int16, 0.1 °C (`0x8000` = not connected) |
| 4 | Flags: bit 0 rapid rise external, bit 1 rapid rise internal, bit 2 heartbeat |
| 5 | Battery voltage, uint8, 20 mV units (0 = unknown) |

## Installation

1. Install via **Settings** > **Marketplace** > **Add from link** with this
   repository's URL, or copy `custom_components/egge_cloud_lorawan` into your
   `config/custom_components` folder.
2. Set up **The Things Network** integration if you haven't yet.
3. Tag each device on TTN with brand `egge-cloud` and its model ID. The TTN
   Console doesn't expose these fields for manually registered devices, so use
   the CLI:

   ```sh
   ttn-lw-cli use eu1.cloud.thethings.network --fetch-ca --user
   ttn-lw-cli login
   ttn-lw-cli end-devices set <application-id> <device-id> \
     --version-ids.brand-id egge-cloud \
     --version-ids.model-id brisket-beacon
   ```

   IDs may only contain lowercase letters, digits and single hyphens.
4. Reload The Things Network integration or restart Home Assistant. The
   devices are discovered. You can also add them under **Settings** >
   **Devices & services** > **Add integration** > **egge.cloud**.

The integration decodes the raw bytes itself. A TTN payload formatter isn't needed.

## Adding a device model

1. Add a module in `custom_components/egge_cloud_lorawan/models/` with a
   subclass of `EggeCloudDevice`. Set `MODEL_ID` (the TTN model ID),
   `MODEL_NAME` and `PORTS`, and implement `decode_uplink`.
2. Add the class to `EggeCloudCollection.DEVICES` in `models/__init__.py`.
3. Add entity descriptions with `device_types=(YourModel,)` in `sensor.py`,
   or in a new platform, plus their names in `strings.json` and
   `translations/en.json`.
4. Add a decoder test in `tests/`.

Discovery matches on the `egge-cloud` brand, so new models need no manifest change.

## Tests

```sh
pip install lorawan-connection pytest
pytest tests
```
