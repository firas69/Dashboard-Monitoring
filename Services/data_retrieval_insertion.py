import asyncio
from pysnmp.hlapi.asyncio import *
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import json

# Load InfluxDB and SNMP config
with open('Config.json') as config_file:
    config = json.load(config_file)

# Access the InfluxDB configuration
influx_token = config['InfluxDbToken']
influx_org = config['InfluxDbOrg']
influx_bucket = config['InfluxDbBucket']
influx_url = config['InfluxDbUrl']

# Access SNMP polling interval
polling_interval = config['SNMP']['polling_interval']

# Initialize the InfluxDB client
client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Load OIDs for octetsIN and octetsOUT
oids_to_poll = [
    ("octetsIN", "1.3.6.1.2.1.2.2.1.10"),  # OID for octetsIN
    ("octetsOUT", "1.3.6.1.2.1.2.2.1.16")  # OID for octetsOUT
]

# Load active devices
def load_active_devices(devices_file):
    with open(devices_file, 'r') as f:
        devices_data = json.load(f)['active_device']
    return devices_data

# SNMP Bulk Polling Function
async def poll_bulk_snmp_data(ip, oids, community_string="public"):
    errorIndication, errorStatus, errorIndex, varBinds = await bulkCmd(
        SnmpEngine(),
        CommunityData(community_string),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        0, len(oids),
        *[ObjectType(ObjectIdentity(oid[1])) for oid in oids]
    )

    if errorIndication:
        print(f"Error: {errorIndication}")
        return None
    elif errorStatus:
        print(f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
        return None
    else:
        return {oid_name: int(varBind[1]) for oid_name, varBind in zip([oid[0] for oid in oids], varBinds)}

# Main function to poll devices and insert data into InfluxDB
async def main():
    devices = load_active_devices('Devices.json')

    while True:
        for ip in devices:
            snmp_values = await poll_bulk_snmp_data(ip, oids_to_poll)
            if snmp_values:
                for oid_name, value in snmp_values.items():
                    point = Point("snmp_data") \
                        .tag("ip_address", ip) \
                        .tag("oid_name", oid_name) \
                        .field(oid_name, value) \
                        .time(time.time_ns(), write_precision='ns')

                    write_api.write(bucket=influx_bucket, org=influx_org, record=point)
                    print(f"IP: {ip}, OID: {oid_name}, Value: {value}")

        await asyncio.sleep(polling_interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        client.close()
