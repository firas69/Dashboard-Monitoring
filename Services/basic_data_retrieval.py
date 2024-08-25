import asyncio
from pysnmp.hlapi.asyncio import *
import json
import time

#################### Configs and Data Retrieval ###########################
# Load the configuration file
with open('Config.json') as config_file:
    config = json.load(config_file)

# Access SNMP polling interval
polling_interval = config['SNMP']['polling_interval']

#################### Load OIDs and Devices #############################
def load_oids(oids_file):
    with open(oids_file, 'r') as f:
        oids_data = json.load(f)['oids']
    
    oids = {}
    for category, oids_dict in oids_data.items():
        for oid_name, oid_info in oids_dict.items():
            oids[oid_name] = oid_info['oid']
    
    return oids

def load_devices(devices_file):
    with open(devices_file, 'r') as f:
        devices_data = json.load(f)
    
    return devices_data

def save_devices(devices_file, devices_data):
    with open(devices_file, 'w') as f:
        json.dump(devices_data, f, indent=4)

#################### SNMP Polling and Data Processing #####################
# Function that returns the SNMP value
async def poll_snmp_data(ip, oid, community_string="public"):
    errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
        SnmpEngine(),
        CommunityData(community_string),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    if errorIndication:
        print(f"Error: {errorIndication}")
        return None
    elif errorStatus:
        print(f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
        return None
    else:
        for varBind in varBinds:
            return str(varBind[1])  # Convert SNMP response to string

async def main():
    oids = load_oids('OIDs.json')
    devices = load_devices('Devices.json')

    while True:
        for ip in devices['active_device']:
            device_info = {"ip_address": ip}

            sys_name = await poll_snmp_data(ip, oids['sysName'])
            if sys_name is not None:
                device_info['sysName'] = sys_name

            sys_descr = await poll_snmp_data(ip, oids['sysDescr'])
            if sys_descr is not None:
                device_info['sysDescription'] = sys_descr

            # Insert the polled data into the 'devices' list
            devices['devices'].append(device_info)
            print(f"Device at {ip} polled successfully.")

        # Save the updated devices information back to Devices.json
        save_devices('Devices.json', devices)

        await asyncio.sleep(polling_interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        print("Polling stopped.")
