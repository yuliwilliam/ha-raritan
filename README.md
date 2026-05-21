# Raritan PDU Home Assistant Integration

Custom Home Assistant integration for Raritan Dominion PX PDUs. The integration talks to the PDU over SNMP and exposes
each outlet as Home Assistant entities for monitoring and control.

## Features

- Discovers outlets from the PDU over SNMP.
- Adds one switch per outlet for turning power on and off.
- Adds one restart button per outlet for power cycling.
- Adds one text entity per outlet for reading and changing the outlet label.
- Adds outlet sensors for current, voltage, active power, power factor, and estimated delivered energy.
- Adds a PDU CPU temperature sensor.
- Adds device information for model type, firmware, hardware revision, serial number, MAC address, and device URL.
- Restores the estimated delivered energy sensor after Home Assistant restarts.
- Supports config entry reconfiguration from the Home Assistant UI.

## Requirements

- A Raritan Dominion PX PDU reachable from Home Assistant.
- SNMP enabled on the PDU.
- Read community for sensors and state polling.
- Write community for outlet control and label changes.

The integration currently authenticates by reading `SNMPv2-MIB::sysDescr.0` and expects the device description to start
with `Raritan Dominion PX`.

## Installation

### HACS

1. Add this repository as a custom repository in HACS.
2. Select the integration category.
3. Install `Raritan`.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/raritan` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

Add the integration from:

`Settings` -> `Devices & services` -> `Add integration` -> `Raritan`

Configuration fields:

- `host`: PDU hostname or IP address.
- `port`: SNMP port. Defaults to `161`.
- `read community`: SNMP read community. Defaults to `public`.
- `write community`: SNMP write community. Defaults to `private`.
- `polling interval(seconds)`: Data update interval in seconds. Defaults to `5`.

## Reconfiguration

Existing entries can be reconfigured from the Home Assistant integration page. Reconfiguration can update the host, port,
SNMP communities, and polling interval without deleting and recreating the integration entry.

The updated values are validated against the PDU before the entry is saved. If validation succeeds, Home Assistant
reloads the entry with the new settings.

## Entities

For each outlet:

- `power_switch`: outlet on/off control.
- `power_cycle`: restart button for power cycling an outlet.
- `label`: editable outlet label.
- `current`: outlet current.
- `voltage`: outlet voltage.
- `active_power`: outlet real power usage.
- `power_factor`: outlet power factor.
- `energy_delivered`: estimated energy delivered, calculated from active power over time.

For the PDU:

- `cpu_temperature`: PDU CPU temperature.

## Troubleshooting

If setup fails with `Failed to connect to Raritan PDU`, check:

- The PDU is reachable from Home Assistant.
- SNMP is enabled on the PDU.
- The configured SNMP port is correct.
- The read community can read `SNMPv2-MIB::sysDescr.0`.
- The device is a supported Raritan Dominion PX model.

If controls fail but sensors work, check that the write community has permission to update outlet state and labels.

## References

- Raritan PX support: https://www.raritan.com/support/product/px
- PDU-MIB: https://mibbrowser.online/mibdb_search.php?mib=PDU-MIB
- SNMPv2-MIB: https://mibbrowser.online/mibdb_search.php?mib=SNMPv2-MIB
