import os
import json
import subprocess
import time
import netifaces as ni

def get_network_range():
    """Automatically retrieves the network range of the active network interface."""
    interfaces = ni.interfaces()
    for interface in interfaces:
        if ni.AF_INET in ni.ifaddresses(interface):
            addr_info = ni.ifaddresses(interface)[ni.AF_INET][0]
            ip_address = addr_info['addr']
            netmask = addr_info['netmask']
            network_range = f"{ip_address}/{sum([bin(int(x)).count('1') for x in netmask.split('.')])}"
            print(f"Detected network range: {network_range} on interface {interface}")
            return network_range
    return None

def create_general_config(file_path, scan_period, network_range):
    """Creates a general configuration file with the specified scan period and network range."""
    config = {
        "scan_period": scan_period,
        "network_range": network_range
    }
    with open(file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Configuration file '{file_path}' created with scan period of {scan_period} seconds.")

def load_general_config(file_path):
    """Loads the general configuration file."""
    print(f"Loading configuration from '{file_path}'...")
    with open(file_path, 'r') as file:
        config = json.load(file)
    print("Configuration loaded:")
    print(json.dumps(config, indent=4))
    return config

def scan_network(network_range):
    """Scans the network for active devices and returns a list of their IP addresses."""
    print(f"Scanning network range {network_range}...")
    result = subprocess.run(["nmap", "-sn", network_range], capture_output=True, text=True)
    active_ips = []
    for line in result.stdout.splitlines():
        if "Nmap scan report for" in line:
            ip_address = line.split(" ")[-1].strip("()")  # Remove parentheses if they exist
            active_ips.append(ip_address)
    print(f"Active IP addresses: {active_ips}")
    return active_ips

def update_devices_json(devices_file, active_ips):
    """Updates the Devices.json file with the list of active IP addresses."""
    if os.path.exists(devices_file):
        with open(devices_file, 'r') as file:
            devices_data = json.load(file)
    else:
        devices_data = {"active_device": [], "devices": []}

    devices_data["active_device"] = active_ips

    with open(devices_file, 'w') as file:
        json.dump(devices_data, file, indent=4)
    print(f"Devices.json updated with active devices: {active_ips}")

def main():
    config_path = "general_config.json"
    devices_file = "Devices.json"
    
    # Check if the config file exists, if not, create it
    if not os.path.exists(config_path):
        scan_period = int(input("Enter the scan period in seconds: "))
        network_range = get_network_range()
        if network_range is None:
            print("Could not detect network range automatically.")
            network_range = input("Enter the network range to scan (e.g., 192.168.1.0/24): ")
        create_general_config(config_path, scan_period, network_range)
    
    # Load the config file
    config = load_general_config(config_path)
    scan_period = config['scan_period']
    network_range = config['network_range']
    
    # Start the periodic scanning
    try:
        while True:
            active_ips = scan_network(network_range)
            update_devices_json(devices_file, active_ips)
            print(f"Waiting {scan_period} seconds until next scan...")
            time.sleep(scan_period)
    except KeyboardInterrupt:
        print("Scanning interrupted by user.")

if __name__ == "__main__":
    main()

