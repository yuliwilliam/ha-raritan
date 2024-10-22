import asyncio
import os
from pathlib import Path
from pysnmp.entity.engine import SnmpEngine
from pysnmp.hlapi.v3arch import get_cmd, CommunityData, UdpTransportTarget, ContextData, ObjectIdentity, ObjectType, \
    set_cmd
from pysnmp.smi import builder, view, compiler

from .const import _LOGGER, MIB_SOURCE_DIR


class SNMPManager:
    def __init__(self, host: str, port: int, read_community: str, write_community: str) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.read_community = read_community
        self.write_community = write_community

        self.modules_loaded = False
        self.snmp_engine = None

    def load_mib_modules(self):
        if self.modules_loaded:
            return

        if not Path(MIB_SOURCE_DIR).is_dir():
            _LOGGER.error(f"mibs directory does not exist: {MIB_SOURCE_DIR}, cwd: {os.getcwd()}")

        mib_builder = builder.MibBuilder()
        mib_builder.add_mib_sources(builder.DirMibSource(MIB_SOURCE_DIR))
        compiler.add_mib_compiler(mib_builder, sources=[MIB_SOURCE_DIR])
        mib_builder.loadModules('PDU-MIB', 'SNMPv2-SMI', 'INET-ADDRESS-MIB', 'SNMPv2-TC', 'SNMPv2-CONF', 'SNMPv2-MIB')
        mib_view_controller = view.MibViewController(mib_builder)
        self.modules_loaded = True

    async def snmp_get(self, *oids: any) -> any:
        _LOGGER.debug(f"SNMP get: {self.host}:{self.port} {self.read_community} {oids}")

        # https://developers.home-assistant.io/docs/asyncio_blocking_operations
        loop = asyncio.get_event_loop()

        # load modules if not already
        if not self.modules_loaded:
            await loop.run_in_executor(None, self.load_mib_modules)

        if self.snmp_engine is None:
            self.snmp_engine = await loop.run_in_executor(None, SnmpEngine)

        oid_objects = [ObjectType(ObjectIdentity(*oid)) for oid in oids]
        error_indication, error_status, error_index, var_binds = await get_cmd(
            self.snmp_engine,
            CommunityData(self.read_community),
            await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=1),
            ContextData(),
            *oid_objects
        )

        _LOGGER.debug(f"SNMP get: {self.host}:{self.port} {self.read_community} {oids} "
                      f"Error: {error_indication}, Status: {error_status}, Index: {error_index}, VarBinds: {var_binds}")

        if error_indication:
            _LOGGER.error("SNMP error: %s", error_indication)
            return None

        if error_status:
            _LOGGER.error(
                "%s at %s",
                error_status.prettyPrint(),
                error_index and var_binds[int(error_index) - 1] or "?"
            )
            return None

        results = []
        for var_bind in var_binds:
            val = var_bind.prettyPrint().split('=')[1].strip()
            if val.isdigit():
                results.append(int(val))
            elif val.isdecimal():
                results.append(float(val))
            else:
                results.append(val)

        if len(results) == 1:
            return results[0]
        return results

    async def snmp_set(self, *oids_and_values: any) -> any:
        _LOGGER.debug(f"SNMP set: {self.host}:{self.port} {self.write_community} {oids_and_values}")

        # Obtain the event loop
        loop = asyncio.get_event_loop()

        # Load MIB modules if not already loaded
        if not self.modules_loaded:
            await loop.run_in_executor(None, self.load_mib_modules)

        # Ensure the SNMP engine is instantiated
        if self.snmp_engine is None:
            self.snmp_engine = await loop.run_in_executor(None, SnmpEngine)

        # Prepare the OID objects with values to set
        oid_objects = [ObjectType(ObjectIdentity(*oid), value) for oid, value in oids_and_values]

        # Send the SNMP set command
        error_indication, error_status, error_index, var_binds = await set_cmd(
            self.snmp_engine,
            CommunityData(self.write_community),
            await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=1),
            ContextData(),
            *oid_objects
        )

        _LOGGER.debug(f"SNMP set: {self.host}:{self.port} {self.write_community} {oids_and_values} "
                      f"Error: {error_indication}, Status: {error_status}, Index: {error_index}, VarBinds: {var_binds}")

        # Handle errors in the SNMP operation
        if error_indication:
            _LOGGER.error("SNMP error: %s", error_indication)
            return None

        if error_status:
            _LOGGER.error(
                "%s at %s",
                error_status.prettyPrint(),
                error_index and var_binds[int(error_index) - 1] or "?"
            )
            return None

        # Parse and return the results from var_binds
        results = []
        for var_bind in var_binds:
            val = var_bind.prettyPrint().split('=')[1].strip()
            if val.isdigit():
                results.append(int(val))
            elif val.isdecimal():
                results.append(float(val))
            else:
                results.append(val)

        if len(results) == 1:
            return results[0]
        return results
