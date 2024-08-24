import os
import json
import subprocess

def install_influxdb():
    print("Adding InfluxDB repository...")
    subprocess.run(["wget", "-qO-", "https://repos.influxdata.com/influxdb.key", "|", "sudo", "apt-key", "add", "-"], shell=True, check=True)
    subprocess.run(["source", "/etc/lsb-release"], shell=True, check=True)
    subprocess.run(["sudo", "apt-get", "update"], check=True)
    print("Installing InfluxDB...")
    subprocess.run(["sudo", "apt-get", "install", "-y", "influxdb"], check=True)
    print("Starting and enabling InfluxDB service...")
    subprocess.run(["sudo", "systemctl", "start", "influxdb"], check=True)
    subprocess.run(["sudo", "systemctl", "enable", "influxdb"], check=True)

def setup_influxdb_database(database, username, password):
    print(f"Setting up InfluxDB database '{database}' and user '{username}'...")
    commands = [
        f"CREATE DATABASE {database};",
        f"CREATE USER {username} WITH PASSWORD '{password}';",
        f"GRANT ALL ON {database} TO {username};"
    ]
    for command in commands:
        subprocess.run(["influx", "-execute", command], shell=True, check=True)

def create_config_file(file_path, influxdb_url, database, username, password):
    config = {
        "influxdb_url": influxdb_url,
        "influxdb_database": database,
        "influxdb_username": username,
        "influxdb_password": password
    }
    with open(file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Configuration file '{file_path}' created.")

def load_config(file_path):
    print(f"Loading configuration from '{file_path}'...")
    with open(file_path, 'r') as file:
        config = json.load(file)
    print("Configuration loaded:")
    print(json.dumps(config, indent=4))
    return config

def main():
    influxdb_installed = input("Is InfluxDB already installed? (yes/no): ").strip().lower()
    if influxdb_installed == "no":
        install_influxdb()

    database = input("Enter the database name: ").strip()
    username = input("Enter the username: ").strip()
    password = input("Enter the password: ").strip()

    setup_influxdb_database(database, username, password)
    
    config_path = input("Enter the path to save the config file (e.g., influx_config.json): ").strip()
    create_config_file(config_path, "http://localhost:8086", database, username, password)
    
    # Load and print the configuration file
    load_config(config_path)

if __name__ == "__main__":
    main()
