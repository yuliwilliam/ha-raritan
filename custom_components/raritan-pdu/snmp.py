from pysnmp.entity.engine import SnmpEngine
from pysnmp.hlapi.v3arch import get_cmd, CommunityData, UdpTransportTarget, ContextData, ObjectIdentity, ObjectType
from pysnmp.smi import builder, view, compiler

from .const import _LOGGER

class SNMPManager:
    def __init__(self, host, port, community) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.community = community

        # snmpEngine = SnmpEngine()
        # mibBuilder = snmpEngine.get_mib_builder()
        # self.snmpEngine = snmpEngine

        mib_source_dir = '../../mibs'

        mibBuilder = builder.MibBuilder()
        compiler.add_mib_compiler(mibBuilder, sources=[mib_source_dir])
        mibBuilder.add_mib_sources(builder.DirMibSource(mib_source_dir))
        mibBuilder.loadModules('PDU-MIB', 'SNMPv2-SMI', 'INET-ADDRESS-MIB', 'SNMPv2-TC', 'SNMPv2-CONF')
        mibViewController = view.MibViewController(mibBuilder)

    async def snmp_get(self, *args: any, **kwargs: any) -> any:
        _LOGGER.debug(f"SNMP get: {self.host}:{self.port} {self.community} {args}")

        """Perform SNMP GET request."""
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.community),
            await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=3),
            ContextData(),
            ObjectType(ObjectIdentity(*args, **kwargs))
        )

        _LOGGER.debug(f"SNMP get: {self.host}:{self.port} {self.community} {args}", errorIndication, errorStatus, errorIndex, varBinds)

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

        for varBind in varBinds:
            val = varBind.prettyPrint().split('=')[1].strip()
            if val.isdigit():
                return int(val)
            elif val.isdecimal():
                return float(val)
            else:
                return val

        return None
