import asyncio

from .snmp import SNMPManager
from .const import _LOGGER


class RaritanPDUOutlet:
    def __init__(self, snmp_manager: SNMPManager, index: int):
        self.snmp_manager: SNMPManager = snmp_manager
        self.index = index
        self.label = ""
        self.data = {
            "current": 0,
            "max_current": 0,
            "voltage": 0,
            "active_power": 0,
            "apparent_power": 0,
            "power_factor": 0,
            "current_upper_warning": 0,
            "current_upper_critical": 0,
            "current_lower_warning": 0,
            "current_lower_critical": 0,
            "current_rating": 0,
            "watt_hours": 0,
        }

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
        self.key = f"{host}:{port} {community}"
        self.snmp_manager: SNMPManager = SNMPManager(host, port, community)
        self.name = ""
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

        outlet_count = await self.snmp_manager.snmp_get("PDU-MIB", "outletCount", 0)
        _LOGGER.info(f"Initialized RaritanPDU {self.name} - {outlet_count} outlets")

        initialize_tasks = []
        for i in range(outlet_count):
            outlet = RaritanPDUOutlet(self.snmp_manager, i + 1)  # Outlet index starts from 1
            initialize_tasks.append(outlet.initialize())  # Create task for initialization
            self.outlets.append(outlet)

        await asyncio.gather(*initialize_tasks)
