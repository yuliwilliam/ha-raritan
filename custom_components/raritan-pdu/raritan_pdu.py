import asyncio

from .snmp import SNMPManager
from .const import _LOGGER


class RaritanPDUOutlet:
    def __init__(self, snmp_manager: SNMPManager, index: int, energy_support: bool):
        self.snmp_manager: SNMPManager = snmp_manager
        self.index = index
        self.energy_support = energy_support

        self.label = ""

        # Ignore some data for performance optimization
        self.data = {
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

    async def initialize(self):
        _LOGGER.info(f"Initializing RaritanPDUOutlet {self.index}")
        initialize_tasks = [self.update_label()]
        for data_name in self.data.keys():
            initialize_tasks.append(self.update_data(data_name))
        await asyncio.gather(*initialize_tasks)

    async def update_data(self, data_name):
        if data_name not in self.data:
            return
        mib_object_name = f"outlet{data_name.title().replace('_', '')}"
        result = await self.snmp_manager.snmp_get("PDU-MIB", mib_object_name, self.index)
        if result is not None:
            self.data[data_name] = result

    async def update_label(self):
        label = await self.snmp_manager.snmp_get("PDU-MIB", "outletLabel", self.index)
        if label is not None:
            self.label = label

    def get_data(self, data_name):
        if data_name not in self.data:
            return None
        return self.data[data_name]

    # async def update_current(self):
    #     current = await self.snmp_manager.snmp_get("PDU-MIB", "outletCurrent", self.index)
    #     if current is not None:
    #         self.current = current
    #
    # async def update_max_current(self):
    #     max_current = await self.snmp_manager.snmp_get("PDU-MIB", "outletMaxCurrent", self.index)
    #     if max_current is not None:
    #         self.max_current = max_current


class RaritanPDU:
    def __init__(self, host: str, port: int, community: str) -> None:
        """Initialize."""
        self.unique_id = f"{host}:{port} {community}"
        self.snmp_manager: SNMPManager = SNMPManager(host, port, community)
        self.name = ""
        self.energy_support = False
        self.outlets: [RaritanPDUOutlet] = []

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            result = await self.snmp_manager.snmp_get("SNMPv2-MIB", "sysDescr", 0)
            is_valid = str(result).startswith("Raritan Dominion PX")
            if is_valid:
                await self.initialize()

            return is_valid
        except Exception:
            return False

    async def initialize(self):
        _LOGGER.info("Initializing RaritanPDU")
        desc = await self.snmp_manager.snmp_get("SNMPv2-MIB", "sysDescr", 0)
        name = await self.snmp_manager.snmp_get("SNMPv2-MIB", "sysName", 0)
        self.name = str(desc).split(" - ")[0] + " " + str(name)

        energy_support = await self.snmp_manager.snmp_get("PDU-MIB", "outletEnergySupport", 0)
        self.energy_support = energy_support == "Yes"

        outlet_count = await self.snmp_manager.snmp_get("PDU-MIB", "outletCount", 0)
        _LOGGER.info(f"Initialized RaritanPDU {self.name} - {outlet_count} outlets")

        initialize_tasks = []
        for i in range(outlet_count):
            outlet = RaritanPDUOutlet(self.snmp_manager, i + 1, self.energy_support)  # Outlet index starts from 1
            initialize_tasks.append(outlet.initialize())  # Create task for initialization
            self.outlets.append(outlet)

        await asyncio.gather(*initialize_tasks)
