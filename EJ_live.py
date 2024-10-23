import json
import configparser
import os
import shutil
import socket
import time
from datetime import datetime

def read_config():
    """Load configuration from ATMS.json and paths.ini."""
    try:
        with open('atms.json', 'r') as f:
            atms = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading ATMS.json: {e}. Exiting.")
        exit(1)

    config = configparser.ConfigParser()
    config.read('paths.ini')
    try:
        source_path = config['DEFAULT']['source']
        destination_path = config['DEFAULT']['destination']
    except KeyError as e:
        print(f"Error reading paths.ini: missing key {e}. Exiting.")
        exit(1)
    
    return atms, source_path, destination_path

def get_current_ip():
    """Get the primary external IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))  # Connect to a public DNS server
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return None

def move_log_file(source_file,destination_file):
    """Move the current log file to the EJ_dump folder with a timestamp."""
    if not os.path.exists(source_file):
        print(f"Source file does not exist: {source_file}. Skipping move operation.")
        return  # Skip the move operation if the log file does not exist

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    destination_folder = os.path.join(os.path.dirname(destination_file), 'Ejdump')
    os.makedirs(destination_folder, exist_ok=True)  # Create Ejdump directory if it doesn't exist

    new_file_name = f"EJ_dump_{timestamp}.log"
    new_file_path = os.path.join(destination_folder, new_file_name)

    shutil.move(source_file, new_file_path)
    print(f"Moved log file {source_file} to {new_file_path}")

def log_file_exists(destination_path, terminal_id):
    """Check if a log file exists for the current date and terminal ID."""
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    expected_log_filename = f"{current_date_str}_{terminal_id}.log"
    expected_log_path = os.path.join(os.path.dirname(destination_path), expected_log_filename)
    return os.path.exists(expected_log_path), expected_log_path

def monitor_file(source_path, destination_path, terminal_id):
    """Monitor the source log file for changes and manage log files accordingly."""
    last_size = 0
    last_mod_time = 0

    while True:
        # Check if today's log file exists
        file_exists, new_destination_path = log_file_exists(destination_path, terminal_id)

        # Move Ejdata.log to dump folder if the daily log file does not exist
        if not file_exists:
            print(f"No log file for today found. Moving Ejdata.log to dump folder if it exists.")
            move_log_file(source_path,destination_path)  # Move the core log file if it exists

            # Optionally create a new log file here if needed
            open(source_path, 'w').close()  # Create a new empty Ejdata.log

        # Check if the source file exists
        if not os.path.exists(source_path):
            print(f"Source file does not exist: {source_path}")
            time.sleep(10)  # Check every 10 seconds
            continue

        # Get the current size and modification time of the source file
        current_size = os.path.getsize(source_path)
        current_mod_time = os.path.getmtime(source_path)

        # Check if the file size or modification time has changed
        if current_size != last_size or current_mod_time != last_mod_time:
            print(f"Change detected in Ejdata.log, copying to {new_destination_path}...")
            shutil.copy2(source_path, new_destination_path)  # Copy the file to the destination
            last_size = current_size
            last_mod_time = current_mod_time

        time.sleep(10)  # Wait before checking again

if __name__ == '__main__':
    atms, source_path, destination_path = read_config()

    # Get current IP address
    current_ip = get_current_ip()
    print(f"Current IP Address: {current_ip}")

    # Retrieve terminal_id based on the current IP address
    terminal_id = atms.get(current_ip)
    if terminal_id:
        print(f"Terminal ID for IP {current_ip}: {terminal_id}")
    else:
        print(f"No terminal ID found for IP {current_ip}. Exiting.")
        exit(1)  # Exit if no terminal ID is found

    print("Monitoring for changes in:", source_path)
    try:
        monitor_file(source_path, destination_path, terminal_id)
    except KeyboardInterrupt:
        print("Stopping the monitoring.")
