import asyncio
import os
import threading
from pathlib import Path
from pysnmp.entity.engine import SnmpEngine
from pysnmp.hlapi.v3arch import get_cmd, CommunityData, UdpTransportTarget, ContextData, ObjectIdentity, ObjectType, \
    set_cmd
from pysnmp.smi import builder, view, compiler

from .const import _LOGGER, MIB_MODULES, MIB_SOURCE_DIR


class SNMPManager:
    def __init__(self, host: str, port: int, read_community: str, write_community: str) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.read_community = read_community
        self.write_community = write_community

        self.modules_loaded = False
        self.modules_lock = threading.Lock()
        self.mib_view_controller = None

    def load_mib_modules(self):
        with self.modules_lock:
            if self.modules_loaded:
                return

            if not Path(MIB_SOURCE_DIR).is_dir():
                _LOGGER.error(f"mibs directory does not exist: {MIB_SOURCE_DIR}, cwd: {os.getcwd()}")

            mib_builder = builder.MibBuilder()
            mib_builder.add_mib_sources(builder.DirMibSource(MIB_SOURCE_DIR))
            compiler.add_mib_compiler(mib_builder, sources=[MIB_SOURCE_DIR])
            mib_builder.loadModules(*MIB_MODULES)
            self.mib_view_controller = view.MibViewController(mib_builder)
            self.modules_loaded = True

    def build_get_object_types(self, oids: any) -> list:
        return [
            ObjectType(ObjectIdentity(*oid)).resolve_with_mib(self.mib_view_controller)
            for oid in oids
        ]

    def build_set_object_types(self, oids_and_values: any) -> list:
        return [
            ObjectType(ObjectIdentity(*oid), value).resolve_with_mib(self.mib_view_controller)
            for oid, value in oids_and_values
        ]

    def resolve_var_binds(self, var_binds: any) -> list:
        return [
            var_bind.resolve_with_mib(self.mib_view_controller)
            for var_bind in var_binds
        ]

    def parse_var_binds(self, var_binds: any) -> list:
        results = []
        for var_bind in var_binds:
            val = var_bind[1].prettyPrint()
            if val.isdigit():
                results.append(int(val))
            elif val.isdecimal():
                results.append(float(val))
            else:
                results.append(val)
        return results

    async def snmp_get(self, *oids: any) -> any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._snmp_get, oids)

    def _snmp_get(self, oids: any) -> any:
        return asyncio.run(self._async_snmp_get(oids))

    async def _async_snmp_get(self, oids: any) -> any:
        _LOGGER.debug(f"SNMP get: {self.host}:{self.port} {self.read_community} {oids}")

        # load modules if not already
        if not self.modules_loaded:
            self.load_mib_modules()

        oid_objects = self.build_get_object_types(oids)
        error_indication, error_status, error_index, var_binds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.read_community),
            await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=1),
            ContextData(),
            *oid_objects,
            lookupMib=False
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

        var_binds = self.resolve_var_binds(var_binds)
        results = self.parse_var_binds(var_binds)

        if len(results) == 1:
            return results[0]
        return results

    async def snmp_set(self, *oids_and_values: any) -> any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._snmp_set, oids_and_values)

    def _snmp_set(self, oids_and_values: any) -> any:
        return asyncio.run(self._async_snmp_set(oids_and_values))

    async def _async_snmp_set(self, oids_and_values: any) -> any:
        _LOGGER.debug(f"SNMP set: {self.host}:{self.port} {self.write_community} {oids_and_values}")

        # Load MIB modules if not already loaded
        if not self.modules_loaded:
            self.load_mib_modules()

        # Prepare the OID objects with values to set
        oid_objects = self.build_set_object_types(oids_and_values)

        # Send the SNMP set command
        error_indication, error_status, error_index, var_binds = await set_cmd(
            SnmpEngine(),
            CommunityData(self.write_community),
            await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=1),
            ContextData(),
            *oid_objects,
            lookupMib=False
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
        var_binds = self.resolve_var_binds(var_binds)
        results = self.parse_var_binds(var_binds)

        if len(results) == 1:
            return results[0]
        return results
