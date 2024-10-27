import json
import configparser
import os
import shutil
import time
import sys  
from datetime import datetime
import winreg

def read_config():
    """Load configuration from ATMS.json and paths.ini."""
    atms = {}
    source_path, destination_path = None, None

    # Handle ATMS.json
    try:
        with open('atms.json', 'r') as f:
            atms = json.load(f)
    except FileNotFoundError:
        print("ATMS.json not found. Ensure the file exists.")
    except json.JSONDecodeError:
        print("ATMS.json is not properly formatted. Please check the JSON structure.")
    
    # Handle paths.ini
    config = configparser.ConfigParser()
    try:
        if not config.read('paths.ini'):
            print("paths.ini not found or empty.")
        else:
            source_path = config['DEFAULT'].get('source', None)
            destination_path = config['DEFAULT'].get('destination', None)
            
            if source_path is None or destination_path is None:
                print("Source or destination path is missing in paths.ini.")
    except KeyError as e:
        print(f"Missing key in paths.ini: {e}")
    
    return atms, source_path, destination_path


def get_manual_ipv4():
    """
    Get the manually configured IPv4 address from the Windows Registry.
    """
    try:
        # Open the registry key where network adapter information is stored
        reg_key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path)

        # Iterate through all subkeys (network adapters)
        i = 0
        while True:
            try:
                adapter_key_name = winreg.EnumKey(reg_key, i)
                adapter_key_path = reg_key_path + "\\" + adapter_key_name
                adapter_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, adapter_key_path)

                # Check for a manually configured IP address
                try:
                    ip_address, _ = winreg.QueryValueEx(adapter_key, "IPAddress")
                    if ip_address and ip_address[0] != "0.0.0.0":
                        return ip_address[0]
                except FileNotFoundError:
                    pass  # IPAddress not found for this adapter, continue to the next

                i += 1
            except OSError:
                # No more subkeys
                break

        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def move_log_file(source_file, destination_file):
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
    current_date_str = datetime.now().strftime("%Y_%m_%d")
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

        # Move EJDATA.LOG to dump folder if the daily log file does not exist
        if not file_exists:
            print(f"No log file for today found. Moving EJDATA.LOG to dump folder if it exists.")
            move_log_file(source_path, destination_path)  # Move the core log file if it exists

            # Optionally create a new log file here if needed
            open(source_path, 'w').close()  # Create a new empty EJDATA.LOG

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
            print(f"Change detected in EJDATA.LOG, copying to {new_destination_path}...")
            shutil.copy2(source_path, new_destination_path)  # Copy the file to the destination
            last_size = current_size
            last_mod_time = current_mod_time

        time.sleep(5)  # Wait before checking again





if __name__ == '__main__':
    atms, source_path, destination_path = read_config()

    # Ensure required data is loaded before proceeding
    if not atms:
        print("No ATMs data loaded. Exiting gracefully.")
        sys.exit(1)
    elif not source_path or not destination_path:
        print("Paths not correctly loaded. Exiting gracefully.")
        sys.exit(1)
    else:
        # Get current IP address
        current_ip = get_manual_ipv4()
        if current_ip:
            print(f"Current IP Address: {current_ip}")

            # Retrieve terminal_id based on the current IP address
            terminal_id = atms.get(current_ip)
            if terminal_id:
                print(f"Terminal ID for IP {current_ip}: {terminal_id}")
                print("Monitoring for changes in:", source_path)
                try:
                    monitor_file(source_path, destination_path, terminal_id)
                except KeyboardInterrupt:
                    print("Stopping the monitoring.")
            else:
                print(f"No terminal ID found for IP {current_ip}. Make sure the current IP exists and is mapped to a Terminal ID in atms.json. Exiting gracefully.")
                sys.exit(1)
        else:
            print("Unable to retrieve the current IP address. Exiting gracefully.")
            sys.exit(1)
