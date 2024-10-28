import os
import shutil

# Define the source files and the target dist directory
source_files = [
    'EJMonitoringService.exe',
    'EJMonitoringService.xml',
    'paths.ini',
    'ip_terminal_id.csv',
    'service_options.bat',
    'write_simulator.py'
]

# Path to the distribution directory (update this if necessary)
dist_directory = os.path.join(os.getcwd(), 'dist')
coreEJ_directory = os.path.join(dist_directory, 'coreEJ')
CopyEJ_directory = os.path.join(dist_directory, 'CopyEJ')

# Check if the dist directory exists
if not os.path.exists(dist_directory):
    print(f"Destination directory '{dist_directory}' does not exist. Please check your setup.")
else:
    # Create coreEJ and CopyEJ directories if they don't exist
    os.makedirs(coreEJ_directory, exist_ok=True)
    os.makedirs(CopyEJ_directory, exist_ok=True)

    # Copy each file to the dist directory
    for file_name in source_files:
        src_path = os.path.join(os.getcwd(), file_name)
        dst_path = os.path.join(dist_directory, file_name)

        try:
            shutil.copy2(src_path, dst_path)
            print(f"Copied '{file_name}' to '{dist_directory}'.")
        except FileNotFoundError:
            print(f"File '{src_path}' does not exist. Skipping...")
        except Exception as e:
            print(f"Error copying '{file_name}': {e}")

    print("File copying process completed.")

# Create the coreEJ and CopyEJ folders
for folder in [coreEJ_directory, CopyEJ_directory]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created directory: {folder}")
    else:
        print(f"Directory already exists: {folder}")
