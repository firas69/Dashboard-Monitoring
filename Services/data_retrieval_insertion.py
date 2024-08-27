import asyncio
from pysnmp.hlapi.asyncio import *
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import json

# Load InfluxDB and SNMP config
with open('Config.json') as config_file:
    config = json.load(config_file)

# Load OIDs from OIDs.json
with open('oids.json') as oids_file:
    oids_data = json.load(oids_file)

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

# Load OIDs for octetsIN and octetsOUT from the JSON file
oids_to_poll = [
    ("octetsIN", oids_data['oids']['network']['octetsIN']['oid']),  # OID for octetsIN
    ("octetsOUT", oids_data['oids']['network']['octetsOUT']['oid'])  # OID for octetsOUT
]

# Load active devices
def load_active_devices(devices_file):
    with open(devices_file, 'r') as f:
        devices_data = json.load(f)['active_device']
    return devices_data

# SNMP Polling Function
async def poll_snmp_data(ip, oids, community_string="public"):
    result = {}
    for oid_name, oid in oids:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community_string),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        if errorIndication:
            print(f"Error: {errorIndication}")
        elif errorStatus:
            print(f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
        else:
            # Extract the value from varBinds
            for varBind in varBinds:
                result[oid_name] = int(varBind[1])
                print(f"IP: {ip}, OID: {oid_name}, Value: {result[oid_name]}")

    return result

# Main function to poll devices and insert data into InfluxDB
async def main():
    devices = load_active_devices('Devices.json')

    while True:
        for ip in devices:
            snmp_values = await poll_snmp_data(ip, oids_to_poll)
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

