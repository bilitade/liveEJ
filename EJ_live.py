import configparser
import os
import shutil
import time
import sys
import logging
from datetime import datetime
import winreg
import csv

from logging.handlers import RotatingFileHandler

def setup_logging(log_file="./ej_live_status/monitoring_status.log", max_log_size=5*1024*1024, backup_count=3):
    """Set up logging configuration with log rotation and ensure the directory exists."""
    
    # Check if the directory exists, if not, create it
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            print(f"Created log directory: {log_dir}")
        except Exception as e:
            print(f"Error creating log directory: {e}")
            return None

    # Create or get the logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_log_size, backupCount=backup_count
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # Console handler to display logs in the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # Adding both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def rename_files():
    directory_path = r"C:\NCR"

    """
    Renames all `.bat`, `.vbs`, and `.exe` files in the given directory by prefixing them with `dont_rename_`.
    If the file already has the prefix, it skips renaming it.
    If a file with the new name exists, it will be overridden.
    """
    # Validate the path
    if not os.path.exists(directory_path):
        logger.warning(f"Invalid or non-existent path to find nx-daily.bat at: '{directory_path}'")
        return

    # Rename `.bat`, `.vbs`, and `.exe` files in the specified directory
    logger.info(f"Check For nx-daily in NCR  {directory_path}")
    for file_name in os.listdir(directory_path):
        # Process only `.bat`, `.vbs`, and `.exe` files
        if file_name.endswith(('.bat', '.vbs', '.exe')):  
            old_path = os.path.join(directory_path, file_name)

            # Check if 'dont_rename_' is already in the file name
            if "dont_rename_" in file_name:
                logger.info(f"Skipping: {old_path} (already contains 'dont_rename_' prefix)")
                continue

            new_name = f"dont_rename_{file_name}"  # Add prefix to file name
            new_path = os.path.join(directory_path, new_name)

            try:
                # Check if file with new name exists, and remove it if so
                if os.path.exists(new_path):
                    os.remove(new_path)
                    logger.info(f"Removed existing file: {new_path}")

                # Rename the file (now it's safe to rename since we've ensured no conflict)
                os.rename(old_path, new_path)
                logger.info(f"Renamed: {old_path} -> {new_path}")
            except Exception as e:
                logger.error(f"Failed to rename {old_path}: {e}")
                
def read_config():
    """Load configuration from paths.ini and retrieve paths for files and folders."""
    config = configparser.ConfigParser()
    atms, source_path, destination_path, terminal_csv, ejdump_folder = {}, None, None, None, None

    if not config.read('paths.ini'):
        logger.error("paths.ini not found or empty.")
        return atms, source_path, destination_path, ejdump_folder

    source_path = config['DEFAULT'].get('source')
    destination_path = config['DEFAULT'].get('destination')
    terminal_csv = config['DEFAULT'].get('csv_path') 
  
    

    if not source_path or not destination_path:
        logger.warning("Source or destination path is missing in paths.ini.")
    if not terminal_csv:
        logger.warning("Terminal CSV path is missing in paths.ini.")
    
    
    # Load the terminal IDs from the CSV file
    if terminal_csv: 
        try:
            atms = load_terminal_ids(terminal_csv)
        except FileNotFoundError:
            logger.error(f"Terminal CSV file not found at {terminal_csv}.")
    
    return atms, source_path, destination_path


def load_terminal_ids(csv_path):
    """Load terminal IDs and their corresponding IP addresses
      from a CSV file specified in paths.ini."""
    terminal_ids = {}

    try:
        with open(csv_path, mode='r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Skip header
            for row in reader:
                if len(row) == 2:
                    ip, terminal_id = row
                    terminal_ids[ip.strip()] = terminal_id.strip()
        
    except FileNotFoundError:
        logger.error(f"CSV file not found at {csv_path}. Ensure the path is correct in paths.ini.")
    except Exception as e:
        logger.error(f"Error loading CSV file {csv_path}: {e}")

    return terminal_ids


def get_priority_manual_ipv4():
    """
    Get the highest priority manually configured IPv4 address from the Windows Registry.
    Priority order:
    1. IP addresses starting with "192.168..."
    2. IP addresses starting with "10.1..."
    3. Return "0.0.0.0" if neither are found.
    """
    ip_addresses = []
    
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
                        ip_addresses.append(ip_address[0])  # Collect all valid IPs
                except FileNotFoundError:
                    pass  # IPAddress not found for this adapter, continue to the next

                i += 1
            except OSError:
                # No more subkeys
                break

        # Sort based on priority: "192.168..." > "10.1..."
        for ip in ip_addresses:
            if ip.startswith("192.168"):
                return ip
        for ip in ip_addresses:
            if ip.startswith("10.1"):
                return ip

        return "0.0.0.0"  # Return default if no priority IP is found

    except Exception:
        return "0.0.0.0"







def clear_EJ(source_file):
    """Clear the current log file."""
    if not os.path.exists(source_file):
        logger.warning(f"Source file does not exist: {source_file}. Skipping Clear operation.")
        return

    try:
        os.remove(source_file)
        logger.info(f"Deleted log file: {source_file}")
    except Exception as e:
        logger.error(f"Error deleting file {source_file}: {e}")

 

def last_run_date():
    """Load the last known date from a file; if not found, return the current date."""
    if os.path.exists("last_run_date.txt"):
        with open("last_run_date.txt", "r") as f:
            return f.read().strip()
    return datetime.now().strftime("%Y_%m_%d")


def save_last_run_date(date_str):
    """Save the current date to a file for persistence across restarts."""
    with open("last_run_date.txt", "w") as f:
        f.write(date_str)


def monitor_file(source_path, destination_path, terminal_id):
    """Monitor EJDATA.LOG and handle date-based log rotation with downtime handling."""
    
    last_size, last_mod_time = 0, 0
    last_date = last_run_date()  # Load last date from file
    new_destination_path = os.path.join(destination_path, f"{last_date}_{terminal_id}.log")
    rename_files()

    while True:
        current_date = datetime.now().strftime("%Y_%m_%d")

        # Check if EJDATA.LOG exists; if not, wait until it does
        if not os.path.exists(source_path):
            logger.warning(f"Source file does not exist: {source_path}")
            time.sleep(5)
            continue

        # Detect date change due to downtime or daily rollover
        if current_date != last_date:
            # Dump the previous EJDATA.LOG to handle date change
            logger.info(f"'DATE CHANGE' Detected: {last_date} to {current_date}. Deleting Old EJDATA.LOG...")
            clear_EJ(source_path)
        
            open(source_path, 'w').close()  # Clear EJDATA.LOG for fresh content
            
            # Update last date and destination path
            last_date = current_date
            save_last_run_date(last_date)  # Persist the updated last date
            new_destination_path = os.path.join(destination_path, f"{current_date}_{terminal_id}.log")
            logger.info(f"Creating New DAILY EJ- @ -{new_destination_path}.")
           

        # Check if file size or modification time has changed
        current_size, current_mod_time = os.path.getsize(source_path), os.path.getmtime(source_path)
        if current_size != last_size or current_mod_time != last_mod_time:
            logger.info(f"Change detected in EJDATA.LOG, Copying To Destination...")
            if not os.path.exists(destination_path):
                os.makedirs(destination_path)
            shutil.copy2(source_path, new_destination_path)

            # Update last known file size and modification time
            last_size, last_mod_time = current_size, current_mod_time

        time.sleep(1)



def main():

    atms, source_path, destination_path = read_config()

    if not all([atms, source_path, destination_path]):
        logger.error("Configuration incomplete. Exiting gracefully.")
        sys.exit(1)
    else:
        logger.info("Config Loaded Successfully")

    static_ip = get_priority_manual_ipv4()
    if static_ip:
        logger.info(f"The Static IP Address: {static_ip}")
        terminal_id = atms.get(static_ip)
        if terminal_id:
            logger.info(f"Terminal ID for IP {static_ip}: {terminal_id}")
            logger.info(f"Watching for changes in: {source_path}")
          
            
            monitor_file(source_path, destination_path, terminal_id)
            
        else:
            logger.warning(f"No terminal ID found for IP {static_ip}. Check 'ip_terminal_id.csv',  Exiting...")
            sys.exit(1)
    else:
        logger.error("Unable to retrieve the current IP address. Exiting gracefully.")
        sys.exit(1)


    
if __name__ == '__main__':
    
     # Set up logging
    logger = setup_logging() 
    logger.info("The Script Started...")
    try:
        main()
    except KeyboardInterrupt:
        logging.getLogger().info("Monitoring stopped by user.") 
    except Exception as e:
        logging.getLogger().error(f"An error occurred: {e}") 
    finally:
        sys.exit(1)
    