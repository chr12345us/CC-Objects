import time
import requests
import urllib3
import json
import os
import argparse
from configparser import ConfigParser
from getpass import getpass
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
current_working_directory = os.path.abspath(os.getcwd()) + os.path.sep
log = current_working_directory + 'update_cybercontroller_objects.log'
logging.basicConfig(filename=log, filemode='w', format='%(asctime)s - %(message)s',
                    level=logging.INFO)

def get_console_input():
    print("--- Destination Cyber-Controller Details ---")
    ip = input("Address: ")
    username = input("Username: ")
    password = getpass("Password: ")
    return {
        'ip': ip,
        'username': username,
        'password': password
    }

def load_config():
    config = ConfigParser()
    config_file = 'update.ini'
    
    if not os.path.exists(config_file):
        logging.info("Configuration file not found. Falling back to console input.")
        print("Configuration file not found. Please enter credentials manually.")
        return get_console_input()
        
    try:
        config.read(config_file)
        credentials = {
            'ip': config.get('credentials', 'ip'),
            'username': config.get('credentials', 'username'),
            'password': config.get('credentials', 'password')
        }
        logging.info("Successfully loaded credentials from config file")
        print("Successfully loaded credentials from config file")
        return credentials
    except Exception as e:
        logging.error(f"Error reading configuration: {str(e)}. Falling back to console input.")
        print(f"Error reading configuration: {str(e)}")
        print("Falling back to manual input.")
        return get_console_input()

def login_cyber_controller(ip, user, password):
    headers = {
        'authority': ip,
        'accept': 'application/json; */*',
        "accept-encoding": "gzip, deflate, br",
        'accept-language': 'en-US,en;q=0.9,he;q=0.8',
        'content-type': 'application/json',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'supportasync': 'true',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/113.0.0.0 Safari/537.36'
    }

    with requests.sessions.Session() as session:
        session.auth = (user, password)
        session.verify = False
        session.headers = headers

    login_data = '{"username":"' + user + '","password":"' + password + '"}'
    login_url = 'https://' + ip + '/mgmt/system/user/login'
    login_response = session.post(login_url, headers=headers, verify=False, data=login_data)
    if login_response.status_code != 200:
        print("Cyber-Controller " + ip + " login status code:", login_response.status_code)
        logging.error("Cyber-Controller " + ip + " login status code: " + str(login_response.status_code))
        logging.info('Finishing the script.')
        exit(1)
    else:
        return session

def get_parent_site_id(parent_site_name, session, dst_cc_ip):
    parent_site_name_url = 'https://' + dst_cc_ip + '/mgmt/system/config/tree/site/byname/' + parent_site_name
    try:
        parent_site_name_response = session.get(parent_site_name_url, verify=False)
        data = json.loads(parent_site_name_response.text)
        
        # Debug logging to see the actual response
        logging.debug(f"API Response for site {parent_site_name}: {parent_site_name_response.text}")
        
        # Check if the response indicates no site found
        if "There is no site with name" in parent_site_name_response.text:
            logging.info(f"No site found with name: {parent_site_name}")
            return False
            
        # Check if we have a valid response with meIdentifier
        if 'meIdentifier' in data and 'managedElementID' in data['meIdentifier']:
            return data['meIdentifier']['managedElementID']
        
        # If we have ormID directly
        if 'ormID' in data:
            return data['ormID']
            
        # If we couldn't find any valid ID
        logging.error(f"Unexpected API response format for site {parent_site_name}: {data}")
        return False
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for site {parent_site_name}: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response for site {parent_site_name}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error getting parent site ID for {parent_site_name}: {str(e)}")
        return False

def get_site_name_by_id(site_id, json_data):
    site_name = None
    for site in json_data['sites']:
        if site['id'] == site_id:
            site_name = site['name']
            break
    return site_name

def load_json_file(filename):
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

def upload_configuration(dst_cc_ip, dst_cc_user, dst_cc_password, json_data, tree_type):
    dst_session = login_cyber_controller(dst_cc_ip, dst_cc_user, dst_cc_password)
    
    # Get root site information
    url = f'https://{dst_cc_ip}/mgmt/system/config/tree/{tree_type}'
    response = dst_session.get(url, verify=False)
    data = json.loads(response.text)
    dst_cc_root_site_id = data["meIdentifier"]["managedElementID"]

    # Update devices
    for device in json_data["devices"]:
        device_name = device['name']
        orm_ID = device['id']
        src_parent_device_id = device['parentOrmID']
        parent_site_name = get_site_name_by_id(src_parent_device_id, json_data)
        parent_orm_id = dst_cc_root_site_id if not parent_site_name else get_parent_site_id(parent_site_name, dst_session, dst_cc_ip)

        payload = {
            "name": device['name'],
            "parentOrmID": parent_orm_id,
            "type": device['type'],
            "ormID": orm_ID,
            "deviceSetup": {
                "deviceAccess": device['deviceAccess']
            }
        }
        url = f'https://{dst_cc_ip}/mgmt/system/config/tree/device'
        response = dst_session.put(url, verify=False, json=payload)
        if response.status_code != 200:
            print(f"Failed to update device: {device_name}")
            error = response.json()
            logging.error(f"Failed to update device - {device_name} {error['message']}")
        else:
            print(f"Updated device: {device_name}")
            logging.info(f"Updated device: {device_name}")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Update Cyber-Controller objects from JSON files')
    parser.add_argument('-p', '--physical', required=False, help='Path to physical tree JSON file')
    parser.add_argument('-o', '--organizational', required=False, help='Path to organizational tree JSON file')
    return parser.parse_args()

def main():
    logging.info('Starting the script.')
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Load credentials from config file or fall back to console input
    credentials = load_config()
    
    # Process Physical tree configuration if provided
    if args.physical:
        physical_json = load_json_file(args.physical)
        if physical_json:
            print(f"\nUploading Physical tree configuration from {args.physical}...")
            upload_configuration(credentials['ip'], credentials['username'], credentials['password'], 
                               physical_json, 'Physical')
    
    # Process Organization tree configuration if provided
    if args.organizational:
        organization_json = load_json_file(args.organizational)
        if organization_json:
            print(f"\nUploading Organization tree configuration from {args.organizational}...")
            upload_configuration(credentials['ip'], credentials['username'], credentials['password'], 
                               organization_json, 'Organization')
    
    # If no files were provided, inform the user
    if not args.physical and not args.organizational:
        print("No input files specified. Use -p for physical tree JSON and -o for organizational tree JSON.")
        parser = argparse.ArgumentParser()
        parser.print_help()
    
    logging.info('Finishing the script.')
    print("\nDone.")

if __name__ == "__main__":
    main()