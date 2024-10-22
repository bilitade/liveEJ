import json
import configparser
import os
import shutil
import socket
import time

def read_config():
    # Load ATMS.json with error handling
    try:
        with open('atms.json', 'r') as f:
            atms = json.load(f)
    except FileNotFoundError:
        print("ATMS.json file not found. Exiting.")
        exit(1)
    except json.JSONDecodeError:
        print("Error decoding ATMS.json. Please check the file format.")
        exit(1)

    # Load paths.ini with error handling
    config = configparser.ConfigParser()
    config.read('paths.ini')
    try:
        source_path = config['DEFAULT']['source']
        destination_path = config['DEFAULT']['destination']
    except KeyError:
        print("Error reading paths.ini. Check for 'source' and 'destination' keys.")
        exit(1)
    
    return atms, source_path, destination_path

def get_current_ip():
    # Get the primary external IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))  # Connect to a public DNS server to detect external IP
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return None

def monitor_file(source_path, destination_path, terminal_id):
    last_size = 0
    last_mod_time = 0

    while True:
        # Check if source file exists
        if not os.path.exists(source_path):
            print(f"Source file does not exist: {source_path}")
            time.sleep(45)  # Wait before checking again
            continue

        # Get the current size and modification time of the source file
        current_size = os.path.getsize(source_path)
        current_mod_time = os.path.getmtime(source_path)

        # Create new destination filename with terminal_id and date
        current_date = time.strftime("%Y-%m-%d")  # Get current date
        new_destination_path = os.path.join(os.path.dirname(destination_path), f"{current_date}_{terminal_id}.log")

        # Create the destination directory if it doesn't exist
        os.makedirs(os.path.dirname(new_destination_path), exist_ok=True)

        # Check if the file size or modification time has changed
        if current_size != last_size or current_mod_time != last_mod_time:
            # If it has changed, copy the file to the new destination
            print("Change detected in Ejdata.log, copying file...")
            shutil.copy2(source_path, new_destination_path)  # Copy the file and preserve metadata
            last_size = current_size
            last_mod_time = current_mod_time
        
        # Sleep for 10 seconds to reduce system load and avoid rapid copying
        time.sleep(10)

if __name__ == '__main__':
    # Read configuration
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
        # Start monitoring the file
        monitor_file(source_path, destination_path, terminal_id)
    except KeyboardInterrupt:
        print("Stopping the monitoring.")
