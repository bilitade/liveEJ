import time
from datetime import datetime
import random

def write_to_log(log_path, duration=180):
    """Write timestamped messages to EJDATA.LOG for a specified duration with randomized intervals.
    
    Args:
        log_path (str): Path to the EJDATA.LOG file.
        duration (int): Total time to write to the log in seconds.
    """
    start_time = time.time()
    entry = 1
    
    # List of possible intervals in seconds
    intervals = [0.5,0.7,1,2,3,]  # You can add more intervals as needed
    
    while time.time() - start_time < duration:
        with open(log_path, 'a') as log_file:
            log_file.write(f"-{entry}- {datetime.now()} - Sample log entry-{entry} \n")
            print(f"Wrote to log: {datetime.now()} - Sample log entry-{entry} \n")
        
        # Select a random interval from the list
        sleep_time = random.choice(intervals)
        time.sleep(sleep_time)  # Wait for a random time before writing the next entry
        entry += 1
        
    print("Finished writing to the log.")

if __name__ == '__main__':
    # Define the path to the log file
    log_file_path = "coreEJ/EJDATA.LOG"
    write_to_log(log_file_path)
