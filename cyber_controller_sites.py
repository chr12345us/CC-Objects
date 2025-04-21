import json
import os
import glob

def filter_json_by_sites(json_data, site_names):
    # Filter sites section
    filtered_sites = [site for site in json_data.get('sites', []) if site.get('name') in site_names]
    
    # Get the IDs of the filtered sites
    filtered_site_ids = [site.get('id') for site in filtered_sites]
    
    # Filter devices section based on parentOrmID
    filtered_devices = [device for device in json_data.get('devices', []) 
                        if device.get('parentOrmID') in filtered_site_ids]
    
    # Create the filtered data
    filtered_data = {
        'sites': filtered_sites,
        'devices': filtered_devices
    }
    
    return filtered_data

def main():
    # Create output directory if it doesn't exist
    if not os.path.exists('./output'):
        os.makedirs('./output')
    
    # Find all JSON files in the input directory
    json_files = glob.glob('./input/*.json')
    
    if not json_files:
        print("No JSON files found in the input directory")
        return
    
    # Take the first JSON file as input
    json_file_path = json_files[0]
    json_file_name = os.path.basename(json_file_path)
    json_file_base, json_file_ext = os.path.splitext(json_file_name)
    
    # Read the JSON data once
    try:
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    # Find all INI files in the input directory
    ini_files = glob.glob('./input/sites*.ini')
    
    if not ini_files:
        print("No site INI files found in the input directory")
        return
    
    # Process each INI file
    for sites_file_path in ini_files:
        sites_file_name = os.path.basename(sites_file_path)
        
        # Extract the sites number from the file name
        sites_number = ""
        if sites_file_name.startswith("sites") and sites_file_name.endswith(".ini"):
            sites_number = sites_file_name[5:-4]  # Extract number between "sites" and ".ini"
        
        try:
            # Read the sites file
            with open(sites_file_path, 'r') as f:
                sites_content = f.read()
            
            # Parse sites from the file
            sites_lines = sites_content.strip().split('\n')
            if len(sites_lines) > 0 and sites_lines[0].startswith('sites:'):
                sites_lines = sites_lines[1:]
            
            # Clean up site names (remove commas and whitespace)
            site_names = [site.strip(' ,') for site in sites_lines]
            
            # Filter the JSON data
            filtered_data = filter_json_by_sites(json_data, site_names)
            
            # Generate output file name
            output_file_name = f"./output/{json_file_base}_sites{sites_number}{json_file_ext}"
            
            # Write the filtered data to the output file
            with open(output_file_name, 'w') as f:
                json.dump(filtered_data, f, indent=4)
            
            print(f"Filtered data for {sites_file_name} has been written to '{output_file_name}'")
            
        except Exception as e:
            print(f"Error processing {sites_file_name}: {e}")

if __name__ == "__main__":
    main()