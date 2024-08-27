import os
import json
import subprocess
import sys

def check_command(command):
    """Check if a command is available on the system."""
    result = subprocess.run(["which", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def install_influxdb():
    print("Installing InfluxDB...")

    # Download and verify the key, then add the repository
    subprocess.run(["wget", "-q", "https://repos.influxdata.com/influxdata-archive_compat.key"], check=True)
    subprocess.run([
        "bash", "-c",
        "echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c"
    ], check=True)
    subprocess.run([
        "bash", "-c",
        "cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null"
    ], check=True)
    subprocess.run([
        "bash", "-c",
        "echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list"
    ], check=True)
    
    # Update package list and install InfluxDB 2.x
    subprocess.run(["sudo", "apt-get", "update"], check=True)
    subprocess.run(["sudo", "apt-get", "install", "-y", "influxdb2"], check=True)

    print("Starting and enabling InfluxDB service...")
    subprocess.run(["sudo", "systemctl", "start", "influxdb"], check=True)
    subprocess.run(["sudo", "systemctl", "enable", "influxdb"], check=True)


def setup_influxdb_database(database, username, password):
    if not check_command("influx"):
        print("Error: 'influx' command not found. Please ensure InfluxDB is installed correctly.")
        sys.exit(1)
    
    print(f"Setting up InfluxDB with Database: '{database}', Username: '{username}'...")
    try:
        subprocess.run([
            "influx", "setup",
            "--bucket", database,
            "--org", "my-org",
            "--username", username,
            "--password", password,
            "--retention", "0",
            "--force"
        ], check=True)
        print("InfluxDB setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during InfluxDB setup: {e}")
        sys.exit(1)

def create_config_file(file_name, influxdb_url, database, username, password):
    config = {
        "influxdb_url": influxdb_url,
        "influxdb_database": database,
        "influxdb_username": username,
        "influxdb_password": password
    }
    try:
        with open(file_name, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        print(f"Configuration file '{file_name}' created successfully in the current directory.")
    except IOError as e:
        print(f"An error occurred while creating the configuration file: {e}")
        sys.exit(1)

def load_config(file_name):
    try:
        with open(file_name, 'r') as file:
            config = json.load(file)
        print(f"Configuration loaded from '{file_name}':")
        print(json.dumps(config, indent=4))
        return config
    except (IOError, json.JSONDecodeError) as e:
        print(f"An error occurred while loading the configuration file: {e}")
        sys.exit(1)

def main():
    influxdb_installed = input("Is InfluxDB already installed? (yes/no): ").strip().lower()
    if influxdb_installed == "no":
        install_influxdb()
    else:
        print("Skipping InfluxDB installation.")

    if not check_command("influx"):
        print("Error: 'influx' command not found after installation. Exiting.")
        sys.exit(1)

    database = input("Enter the database name: ").strip()
    username = input("Enter the username: ").strip()
    password = input("Enter the password: ").strip()

    setup_influxdb_database(database, username, password)
    
    # Define config file name
    file_name = "influx_config.json"
    influxdb_url = "http://localhost:8086"
    
    create_config_file(file_name, influxdb_url, database, username, password)
    load_config(file_name)

if __name__ == "__main__":
    main()

