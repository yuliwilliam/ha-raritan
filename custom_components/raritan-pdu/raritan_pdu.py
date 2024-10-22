import asyncio
import time

from .snmp import SNMPManager
from .const import _LOGGER


class RaritanPDUOutlet:
    def __init__(self, snmp_manager: SNMPManager, index: int, energy_support: bool):
        self.snmp_manager: SNMPManager = snmp_manager
        self.index = index
        self.energy_support = energy_support

        # Ignore some data for performance optimization
        self.sensor_data = {
            "label": "",

            # A value for each outlet which describes the operational state of the outlet. It is also used to set the operational state of the outlet Enumeration: 'on': 1, 'cycling': 2, 'off': 0, 'error': -1.
            "operational_state": "",

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

            # NOT SUPPORTED by all PDUs. The value of the cumulative active energy for this outlet. This value is reported in WattHours. The total energy consumption in watt-hours (accumulated over time)
            # "watt_hours": 0,
        }

        # A snapshot of previous sensor data
        self.previous_sensor_data = {}

        self.sensor_data_update_timestamp = 0
        self.previous_sensor_data_update_timestamp = 0

        self.initial_energy_delivered = 0  # energy delivered from previous sessions
        self.energy_delivered = 0  # energy delivered in current session

        if energy_support:
            self.sensor_data["watt_hours"] = 0

    def get_outlet_index_and_label(self):
        outlet_label = self.sensor_data['label']
        if outlet_label == f"Outlet {self.index}":
            return outlet_label
        else:
            return f"Outlet {self.index} {outlet_label}"

    def get_sensor_oid_from_sensor_name(self, sensor_name: str) -> str:
        mib_object_name = f"outlet{sensor_name.title().replace('_', '')}"
        return mib_object_name

    def get_sensor_oids(self):
        oids = []
        for data_name in self.sensor_data.keys():
            oids.append(["PDU-MIB", self.get_sensor_oid_from_sensor_name(data_name), self.index])
        return oids

    def get_sensor_names(self):
        return self.sensor_data.keys()

    def update_sensor_data(self, new_sensor_data: dict[str, any]):
        # backup
        self.previous_sensor_data_update_timestamp = self.sensor_data_update_timestamp
        self.previous_sensor_data = self.sensor_data.copy()

        # update
        self.sensor_data_update_timestamp = time.time()
        for key in new_sensor_data.keys():
            self.sensor_data[key] = new_sensor_data[key]

        self.update_energy_delivered()

    def initialize_energy_delivered(self, initial_value: float):
        self.initial_energy_delivered = initial_value
        _LOGGER.debug(f"Initialize Outlet {self.index} initial_energy_delivered to {self.initial_energy_delivered}")

    def update_energy_delivered(self):
        """Calculated using Left Riemann Sum"""

        # not enough data to estimate
        if self.previous_sensor_data_update_timestamp == 0 or self.sensor_data_update_timestamp == 0:
            return  # abort

        time_diff_seconds = self.sensor_data_update_timestamp - self.previous_sensor_data_update_timestamp
        if time_diff_seconds < 0:
            return  # abort

        time_diff_hours = time_diff_seconds / (60.0 * 60.0)  # 3600s in 1 hour
        new_energy_delivered = self.previous_sensor_data["active_power"] * time_diff_hours
        self.energy_delivered += new_energy_delivered

    async def power_on(self):
        await self.set_operational_state("on")

    async def power_off(self):
        await self.set_operational_state("off")

    async def power_cycle(self):
        await self.set_operational_state("cycling")

    async def set_operational_state(self, operational_state: str):
        expected_new_operational_state = await self.snmp_manager.snmp_set(
            [["PDU-MIB", self.get_sensor_oid_from_sensor_name("operational_state"), self.index], operational_state])
        new_operational_state = ""

        # Wait for the PDU to process
        start = time.time()
        while expected_new_operational_state != new_operational_state:
            await asyncio.sleep(1)
            new_operational_state = await self.snmp_manager.snmp_get(
                ["PDU-MIB", self.get_sensor_oid_from_sensor_name("operational_state"), self.index])
            if time.time() - start > 10:
                break  # timeout to set state

        self.update_sensor_data({"operational_state": new_operational_state})

    def is_on(self):
        return self.sensor_data["operational_state"] == "on"

    def get_data(self):
        data = self.sensor_data.copy()
        # add energy_delivered data
        data["energy_delivered"] = self.energy_delivered + self.initial_energy_delivered
        return data


class RaritanPDU:
    def __init__(self, host: str, port: int, read_community: str, write_community: str) -> None:
        """Initialize."""
        self.unique_id = f"{host}:{port}, read community: {read_community}, write community: {write_community}"
        self.snmp_manager: SNMPManager = SNMPManager(host, port, read_community, write_community)
        self.name = ""
        self.energy_support = False
        self.outlet_count = 0
        self.cpu_temperature = 0
        self.outlets: [RaritanPDUOutlet] = []

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            result = await self.snmp_manager.snmp_get(["SNMPv2-MIB", "sysDescr", 0])
            if result is None:
                return False
            return str(result).startswith("Raritan Dominion PX")
        except Exception:
            return False

    async def update_data(self):
        _LOGGER.info("Initializing RaritanPDU")

        result = await self.snmp_manager.snmp_get(
            ["SNMPv2-MIB", "sysDescr", 0],
            ["SNMPv2-MIB", "sysName", 0],
            ["PDU-MIB", "outletEnergySupport", 0],
            ["PDU-MIB", "outletCount", 0],
            ["PDU-MIB", "unitCpuTemp", 0],  # The value for the unit's CPU temperature sensor in tenth degrees celsius.
        )

        if result is None:
            return  # abort update

        [desc, name, energy_support, outlet_count, cpu_temperature] = result

        self.name = str(desc).split(" - ")[0] + " " + str(name)
        self.energy_support = energy_support == "Yes"
        self.cpu_temperature = cpu_temperature / 10.0  # The value for the unit's CPU temperature sensor in tenth degrees celsius.

        # If the outlet count has changed, reinitialize the outlets list. This should only run when first initialized.
        if outlet_count != self.outlet_count:
            self.outlet_count = outlet_count
            self.outlets = []
            for i in range(outlet_count):
                # Create an outlet (index starts from 1) and append it to the outlets list
                outlet = RaritanPDUOutlet(self.snmp_manager, i + 1, self.energy_support)
                self.outlets.append(outlet)

        # For each outlet, append all relevant MIB OIDs
        outlet_sensor_oids = []
        for outlet in self.outlets:
            outlet_sensor_oids.extend(outlet.get_sensor_oids())

        # Fetch all the outlet data in one go using the OIDs
        results = await self.snmp_manager.snmp_get(*outlet_sensor_oids)
        if result is None:
            return  # abort update

        # Update outlet data with the fetched results
        for i, outlet in enumerate(self.outlets):
            new_sensor_data = results[i * len(outlet.get_sensor_oids()): (i + 1) * len(outlet.get_sensor_oids())]
            outlet.update_sensor_data(dict(zip(outlet.get_sensor_names(), new_sensor_data)))

    def get_outlet_by_index(self, index: int) -> RaritanPDUOutlet:
        return self.outlets[index - 1]  # Outlet index starts from 1

    def get_data(self) -> dict:
        data = {}
        # Add data from outlets
        for outlet in self.outlets:
            data[outlet.index] = outlet.get_data()

        # Add data from PDU
        data["cpu_temperature"] = self.cpu_temperature
        return data
