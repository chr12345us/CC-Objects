import json
import argparse
import os
import logging

# Set up logging
current_working_directory = os.path.abspath(os.getcwd()) + os.path.sep
log = current_working_directory + 'split_cybercontroller.log'
logging.basicConfig(filename=log, filemode='w', format='%(asctime)s - %(message)s',
                    level=logging.INFO)

def ensure_output_dir(dir_path):
    """Create output directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            logging.info(f"Created output directory: {dir_path}")
            print(f"Created output directory: {dir_path}")
        except Exception as e:
            logging.error(f"Error creating directory {dir_path}: {str(e)}")
            print(f"Error creating directory {dir_path}: {str(e)}")
            return False
    return True

def load_json_file(filename):
    """Load a JSON file and return its contents."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        print(f"Error: Could not find file {filename}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from file: {filename}")
        print(f"Error: Invalid JSON format in file {filename}")
        return None

def save_json_file(data, filename):
    """Save data to a JSON file."""
    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully saved: {filename}")
        logging.info(f"Successfully saved: {filename}")
        return True
    except Exception as e:
        logging.error(f"Error saving file {filename}: {str(e)}")
        print(f"Error saving file {filename}: {str(e)}")
        return False

def split_devices(source_json, output_dir, output_file1, output_file2):
    """Split devices according to the specified criteria."""
    logging.info('Starting to split devices.')
    
    # Ensure output directory exists
    if not ensure_output_dir(output_dir):
        return False
    
    # Create full paths for output files
    output_path1 = os.path.join(output_dir, output_file1)
    output_path2 = os.path.join(output_dir, output_file2)
    
    # Load the source JSON file
    data = load_json_file(source_json)
    if not data:
        return False
    
    # Create two new data structures with the same sites
    data1 = {
        "sites": data.get("sites", []),
        "devices": []
    }
    
    data2 = {
        "sites": data.get("sites", []),
        "devices": []
    }
    
    # Filter devices based on criteria
    for device in data.get("devices", []):
        device_name = device.get("name", "").lower()
        
        if device_name.startswith("dp01") or device_name.startswith("dp03"):
            data1["devices"].append(device)
            logging.info(f"Device {device_name} added to file 1")
        elif device_name.startswith("dp02") or device_name.startswith("dp04"):
            data2["devices"].append(device)
            logging.info(f"Device {device_name} added to file 2")
    
    # Save the new files
    success1 = save_json_file(data1, output_path1)
    success2 = save_json_file(data2, output_path2)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total devices in source file: {len(data.get('devices', []))}")
    print(f"Devices in {output_path1}: {len(data1['devices'])} (dp01 and dp03)")
    print(f"Devices in {output_path2}: {len(data2['devices'])} (dp02 and dp04)")
    
    logging.info('Finished splitting devices.')
    return success1 and success2

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Split Cyber-Controller JSON file based on device naming patterns')
    parser.add_argument('-s', '--source', required=True, help='Source JSON file')
    parser.add_argument('-d', '--dir', default='output', help='Output directory (default: output)')
    parser.add_argument('-o1', '--output1', default='dp01_dp03_devices.json', 
                        help='Output file name for dp01 and dp03 devices (default: dp01_dp03_devices.json)')
    parser.add_argument('-o2', '--output2', default='dp02_dp04_devices.json', 
                        help='Output file name for dp02 and dp04 devices (default: dp02_dp04_devices.json)')
    return parser.parse_args()

def main():
    """Main function."""
    logging.info('Starting the script.')
    
    # Parse command line arguments
    args = parse_arguments()
    
    print(f"Source file: {args.source}")
    print(f"Output directory: {args.dir}")
    print(f"Output file 1 (dp01/dp03): {os.path.join(args.dir, args.output1)}")
    print(f"Output file 2 (dp02/dp04): {os.path.join(args.dir, args.output2)}")
    
    # Split the devices and create the output files
    split_devices(args.source, args.dir, args.output1, args.output2)
    
    logging.info('Finishing the script.')
    print("\nDone.")

if __name__ == "__main__":
    main()