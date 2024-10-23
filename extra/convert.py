import csv
import json

def convert_csv_to_json(csv_file_path, json_file_path):
    ip_terminal_mapping = {}
    
    # Read the CSV file
    with open(csv_file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        
        for row in reader:
            if len(row) == 2:
                ip_address, terminal_id = row
                ip_terminal_mapping[ip_address] = terminal_id
    
    # Write to JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(ip_terminal_mapping, json_file, indent=4)

# Specify the paths
csv_file_path = 'ip_term.csv'  # Path to your CSV file
json_file_path = 'atm.json'      # Desired path for the JSON output

# Convert the CSV to JSON
convert_csv_to_json(csv_file_path, json_file_path)

print(f"Converted {csv_file_path} to {json_file_path}")
