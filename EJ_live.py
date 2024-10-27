import json
import configparser
import os
import shutil
import time
import sys
import logging
from datetime import datetime
import winreg

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler to write logs to a file
file_handler = logging.FileHandler("monitoring.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Console handler to display logs on the terminal
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Adding both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def read_config():
    """Load configuration from ATMS.json and paths.ini."""
    atms = {}
    source_path, destination_path = None, None

    try:
        with open('atms.json', 'r') as f:
            atms = json.load(f)
    except FileNotFoundError:
        logger.error("ATMS.json not found. Ensure the file exists.")
    except json.JSONDecodeError:
        logger.error("ATMS.json is not properly formatted. Please check the JSON structure.")

    config = configparser.ConfigParser()
    try:
        if not config.read('paths.ini'):
            logger.error("paths.ini not found or empty.")
        else:
            source_path = config['DEFAULT'].get('source')
            destination_path = config['DEFAULT'].get('destination')
            if not source_path or not destination_path:
                logger.warning("Source or destination path is missing in paths.ini.")
    except KeyError as e:
        logger.error(f"Missing key in paths.ini: {e}")

    return atms, source_path, destination_path


def get_manual_ipv4():
    """Retrieve the manually configured IPv4 address from the Windows Registry."""
    try:
        reg_key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path)
        i = 0
        while True:
            try:
                adapter_key_name = winreg.EnumKey(reg_key, i)
                adapter_key_path = os.path.join(reg_key_path, adapter_key_name)
                adapter_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, adapter_key_path)
                try:
                    ip_address, _ = winreg.QueryValueEx(adapter_key, "IPAddress")
                    if ip_address and ip_address[0] != "0.0.0.0":
                        return ip_address[0]
                except FileNotFoundError:
                    pass
                i += 1
            except OSError:
                break
    except Exception as e:
        logger.error(f"Error retrieving IP address: {e}")
    return None


def move_log_file(source_file, destination_file):
    """Move the current log file to the EJ_dump folder with a timestamp."""
    if not os.path.exists(source_file):
        logger.warning(f"Source file does not exist: {source_file}. Skipping move operation.")
        return

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    destination_folder = os.path.join(os.path.dirname(destination_file), 'Ejdump')
    os.makedirs(destination_folder, exist_ok=True)

    new_file_name = f"EJ_dump_{timestamp}.log"
    new_file_path = os.path.join(destination_folder, new_file_name)
    shutil.move(source_file, new_file_path)
    logger.info(f"Moved log file {source_file} to {new_file_path}")


def log_file_exists(destination_path, terminal_id):
    """Check if a log file exists for the current date and terminal ID."""
    current_date_str = datetime.now().strftime("%Y_%m_%d")
    expected_log_filename = f"{current_date_str}_{terminal_id}.log"
    expected_log_path = os.path.join(os.path.dirname(destination_path), expected_log_filename)
    return os.path.exists(expected_log_path), expected_log_path


def monitor_file(source_path, destination_path, terminal_id):
    """Monitor the source log file for changes and manage log files accordingly."""
    last_size, last_mod_time = 0, 0

    while True:
        file_exists, new_destination_path = log_file_exists(destination_path, terminal_id)

        if not file_exists:
            logger.info("No log file for today found. Moving EJDATA.LOG to dump folder if it exists.")
            move_log_file(source_path, destination_path)
            open(source_path, 'w').close()

        if not os.path.exists(source_path):
            logger.warning(f"Source file does not exist: {source_path}")
            time.sleep(10)
            continue

        current_size, current_mod_time = os.path.getsize(source_path), os.path.getmtime(source_path)

        if current_size != last_size or current_mod_time != last_mod_time:
            logger.info(f"Change detected in EJDATA.LOG, copying to {new_destination_path}...")
            shutil.copy2(source_path, new_destination_path)
            last_size, last_mod_time = current_size, current_mod_time

        time.sleep(5)


if __name__ == '__main__':
    atms, source_path, destination_path = read_config()
    logger.info("NCR ATM BOOTED UP...")
    logger.info("EJMonitoringService Initiated The Script...")

    if not atms:
        logger.error("No ATMs data loaded. Exiting gracefully.")
        sys.exit(1)

    if not source_path or not destination_path:
        logger.error("Paths not correctly loaded. Exiting gracefully.")
        sys.exit(1)

    current_ip = get_manual_ipv4()
    if not current_ip:
        logger.error("Unable to retrieve the current IP address. Exiting gracefully.")
        sys.exit(1)

    logger.info(f"Current IP Address: {current_ip}")

    terminal_id = atms.get(current_ip)
    if not terminal_id:
        logger.warning(f"No terminal ID found for IP {current_ip}. Exiting gracefully.")
        sys.exit(1)

    logger.info(f"Terminal ID for IP {current_ip}: {terminal_id}")
    logger.info("Monitoring for changes in: " + source_path)

    try:
        monitor_file(source_path, destination_path, terminal_id)
    except KeyboardInterrupt:
        logger.info("Stopping the monitoring.")
