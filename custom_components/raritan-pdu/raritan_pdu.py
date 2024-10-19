from .snmp import SNMPManager
from .const import _LOGGER


class RaritanPDUOutlet:
    def __init__(self, snmp_manager: SNMPManager, index: int, energy_support: bool):
        self.snmp_manager: SNMPManager = snmp_manager
        self.index = index
        self.energy_support = energy_support

        # Ignore some data for performance optimization
        self.data = {
            "label": "",

            # A value for each outlet which describes the operational state of the outlet. It is also used to set the operational state of the outlet Enumeration: 'on': 1, 'cycling': 2, 'off': 0, 'error': -1.
            # "operational_state": 0,

            # A unique value for the current sensor attached to the outlet. This value is reported in milliamps (1/1000th of an amp)
            "current": 0,

            # A unique value for the max. current sensor attached to the outlet. This value is reported in milliamps (1/1000th of an amp)
            # "max_current": 0,

            # A unique value for the voltage sensor attached to the outlet.This value is reported in millivolts (1/1000th of a volt)
            "voltage": 0,

            # A unique value for the active power sensor attached to the outlet. This value is reported in Watts. The real power consumption.
            "active_power": 0,

            # A unique value for the apparent power sensor attached to the outlet. This value is reported in Volt-Amps. This is the product of current and voltage.
            # "apparent_power": 0,

            # A unique value for the power factor of the outlet. The reading represents a percentage in the range of 0% to 100%. The power factor, a ratio of real power to apparent power.
            "power_factor": 0,

            # The value of the upper warning (non-critical) current threshold for the outlet. This value is reported in milliamps (1/1000th of an amp)
            # "current_upper_warning": 0,

            # The value of the upper critical current threshold for the outlet. This value is reported in milliamps (1/1000th of an amp)
            # "current_upper_critical": 0,

            # The value of the lower warning (non-critical) current threshold for the outlet. This value is reported in milliamps (1/1000th of an amp)
            # "current_lower_warning": 0,

            # The value of the lower critical current threshold for the outlet. This value is reported in milliamps (1/1000th of an amp)
            # "current_lower_critical": 0,

            # The hysteresis used for deassertions. This value is reported in milliamps (1/1000th of an amp)
            # "current_hysteresis": 0,

            # The current rating of the outlet. This value is reported in milliamps (1/1000th of an amp). The rated maximum current that the system can safely handle, in milliamps
            # "current_rating": 0,

            # NOT SUPPORTED by PDU. The value of the cumulative active energy for this outlet. This value is reported in WattHours. The total energy consumption in watt-hours (accumulated over time)
            # "watt_hours": 0,
        }

        if energy_support:
            self.data["watt_hours"] = 0


class RaritanPDU:
    def __init__(self, host: str, port: int, community: str) -> None:
        """Initialize."""
        self.unique_id = f"{host}:{port} {community}"
        self.snmp_manager: SNMPManager = SNMPManager(host, port, community)
        self.name = ""
        self.energy_support = False
        self.outlet_count = 0
        self.outlets: [RaritanPDUOutlet] = []

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            result = await self.snmp_manager.snmp_get(["SNMPv2-MIB", "sysDescr", 0])
            is_valid = str(result).startswith("Raritan Dominion PX")
            if is_valid:
                await self.update_data()

            return is_valid
        except Exception:
            return False

    async def update_data(self):
        _LOGGER.info("Initializing RaritanPDU")

        [desc, name, energy_support, outlet_count] = await self.snmp_manager.snmp_get(
            ["SNMPv2-MIB", "sysDescr", 0],
            ["SNMPv2-MIB", "sysName", 0],
            ["PDU-MIB", "outletEnergySupport", 0],
            ["PDU-MIB", "outletCount", 0]
        )

        self.name = str(desc).split(" - ")[0] + " " + str(name)
        self.energy_support = energy_support == "Yes"

        # If the outlet count has changed, reinitialize the outlets list. This will run when first initialized.
        if outlet_count != self.outlet_count:
            self.outlet_count = outlet_count
            self.outlets = []
            for i in range(outlet_count):
                # Create an outlet (index starts from 1) and append it to the outlets list
                outlet = RaritanPDUOutlet(self.snmp_manager, i + 1, self.energy_support)
                self.outlets.append(outlet)

        # For each outlet, append all relevant MIB OIDs (using the key names from outlet.data)
        oids = []
        for outlet in self.outlets:
            for data_name in outlet.data.keys():
                mib_object_name = f"outlet{data_name.title().replace('_', '')}"
                oids.append(["PDU-MIB", mib_object_name, outlet.index])

        # Fetch all the outlet data in one go using the OIDs
        results = await self.snmp_manager.snmp_get(*oids)

        # Update outlet data with the fetched results
        i = 0
        for outlet in self.outlets:
            for data_name in outlet.data.keys():
                outlet.data[data_name] = results[
                    i]  # Update each data field in the outlet using the corresponding result
                i += 1

    def get_outlet_by_index(self, index: int) -> RaritanPDUOutlet:
        return self.outlets[index - 1]  # Outlet index starts from 1

    def get_data(self) -> dict:
        data = {}
        for outlet in self.outlets:
            data[outlet.index] = outlet.data.copy()
        return data
