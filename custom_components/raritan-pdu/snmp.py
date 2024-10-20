import asyncio
import os
from pathlib import Path
from pysnmp.entity.engine import SnmpEngine
from pysnmp.hlapi.v3arch import get_cmd, CommunityData, UdpTransportTarget, ContextData, ObjectIdentity, ObjectType
from pysnmp.smi import builder, view, compiler

from .const import _LOGGER, MIB_SOURCE_DIR


class SNMPManager:
    def __init__(self, host, port, community) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.community = community

        self.modules_loaded = False

    def load_mib_modules(self):
        if self.modules_loaded:
            return

        if not Path(MIB_SOURCE_DIR).is_dir():
            _LOGGER.error(f"mibs directory does not exist: {MIB_SOURCE_DIR}, cwd: {os.getcwd()}")

        mibBuilder = builder.MibBuilder()
        compiler.add_mib_compiler(mibBuilder, sources=[MIB_SOURCE_DIR])
        mibBuilder.add_mib_sources(builder.DirMibSource(MIB_SOURCE_DIR))
        mibBuilder.loadModules('PDU-MIB', 'SNMPv2-SMI', 'INET-ADDRESS-MIB', 'SNMPv2-TC', 'SNMPv2-CONF')
        mibViewController = view.MibViewController(mibBuilder)
        self.modules_loaded = True

    async def snmp_get(self, *oids: any) -> any:
        # https://developers.home-assistant.io/docs/asyncio_blocking_operations/#open
        loop = asyncio.get_running_loop()
        promise = await loop.run_in_executor(None, self._snmp_get, *oids)
        return await promise

    async def _snmp_get(self, *oids: any) -> any:
        _LOGGER.debug(f"SNMP get: {self.host}:{self.port} {self.community} {oids}")

        # load modules if not already
        self.load_mib_modules()

        oid_objects = [ObjectType(ObjectIdentity(*oid)) for oid in oids]
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.community),
            await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=1),
            ContextData(),
            *oid_objects
        )

        _LOGGER.debug(f"SNMP get: {self.host}:{self.port} {self.community} {oids} "
                      f"Error: {errorIndication}, Status: {errorStatus}, Index: {errorIndex}, VarBinds: {varBinds}")

        if errorIndication:
            _LOGGER.error("SNMP error: %s", errorIndication)
            return None

        if errorStatus:
            _LOGGER.error(
                "%s at %s",
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1] or "?"
            )
            return None

        results = []
        for varBind in varBinds:
            val = varBind.prettyPrint().split('=')[1].strip()
            if val.isdigit():
                results.append(int(val))
            elif val.isdecimal():
                results.append(float(val))
            else:
                results.append(val)

        if len(results) == 1:
            return results[0]
        return results
