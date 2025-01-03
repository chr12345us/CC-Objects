import time
import requests
import urllib3
import json
import os
from configparser import ConfigParser
from getpass import getpass
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
current_working_directory = os.path.abspath(os.getcwd()) + os.path.sep
log = current_working_directory + 'download_cybercontroller_objects.log'
logging.basicConfig(filename=log, filemode='w', format='%(asctime)s - %(message)s',
                    level=logging.INFO)

def get_console_input():
    print("--- Source Cyber-Controller Details ---")
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
    config_file = 'download.ini'
    
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
    parent_site_name_response = session.get(parent_site_name_url, verify=False)
    data = json.loads(parent_site_name_response.text)
    if "There is no site with name" in parent_site_name_response.text:
        return False
    else:
        parent_site_id = data['ormID']
        return parent_site_id


def get_parent_site_name(device_parent_id, session, ip):
    parent_site_id_url = 'https://' + ip + '/mgmt/system/config/tree/site/byid/' + device_parent_id
    parent_site_id_response = session.get(parent_site_id_url, verify=False)
    data = json.loads(parent_site_id_response.text)
    if "There is no site with name" in parent_site_id_response.text:
        return False
    else:
        parent_site_name = data['name']
        return parent_site_name


def extract_sites_and_devices(data, src_session, src_cc_ip, parent_id=None):
    sites = []
    devices = []

    for item in data["children"]:
        if item["meIdentifier"]["managedElementClass"] == "com.radware.insite.model.device.Device":
            device_parent_id = parent_id if parent_id else data["meIdentifier"]["managedElementID"]
            device = {
                "name": item["name"],
                "type": item["type"],
                "managementIp": item["managementIp"],
                "id": item["meIdentifier"]["managedElementID"],
                "parentOrmID": device_parent_id
            }
            devices.append(device)
        elif item["meIdentifier"]["managedElementClass"] == "com.radware.insite.model.device.Site":
            site_parent_id = parent_id if parent_id else data["meIdentifier"]["managedElementID"]
            parent_site_name = get_parent_site_name(site_parent_id, src_session, src_cc_ip)

            site = {
                "name": item["name"],
                "id": item["meIdentifier"]["managedElementID"],
                "parent_site_name": parent_site_name,
                "parentOrmID": site_parent_id
            }

            sites.append(site)
            extracted_sites, extracted_devices = extract_sites_and_devices(item, src_session, src_cc_ip,
                                                                           item["meIdentifier"]["managedElementID"])
            sites.extend(extracted_sites)
            devices.extend(extracted_devices)

    return sites, devices


def extract_device_access_data(device_ip, existing_file_data, session, src_cc_ip):
    url = 'https://' + src_cc_ip + '/mgmt/system/config/tree/device/byip/' + device_ip
    response = session.get(url, verify=False)
    data = json.loads(response.text)
    device_access_data = data["deviceSetup"]['deviceAccess']
    del device_access_data['ormID']

    for device in existing_file_data['devices']:
        if device['managementIp'] == device_ip:
            device['deviceAccess'] = device_access_data
            break

    return existing_file_data


def get_site_name_by_id(site_id, json_data):
    site_name = None
    for site in json_data['sites']:
        if site['id'] == site_id:
            site_name = site['name']
            break
    return site_name


def write_json_to_file(data, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f'Successfully wrote data to {filename}')
        print(f'Data has been written to {filename}')
    except Exception as e:
        logging.error(f'Error writing to file: {str(e)}')
        print(f'Error writing to file: {str(e)}')


def main(src_cc_ip, src_cc_user, src_cc_password, url_suffix):
    src_session = login_cyber_controller(src_cc_ip, src_cc_user, src_cc_password)

    url = 'https://' + src_cc_ip + url_suffix
    response = src_session.get(url, verify=False)
    data = json.loads(response.text)

    # Extract sites and devices
    extracted_sites, extracted_devices = extract_sites_and_devices(data, src_session, src_cc_ip)

    # Construct the final JSON structure
    final_json = {
        "sites": extracted_sites,
        "devices": extracted_devices
    }

    for device in final_json['devices']:
        device_ip = device['managementIp']
        final_json = extract_device_access_data(device_ip, final_json, src_session, src_cc_ip)
    
    # Generate filename based on the URL suffix
    filename = f'cyber_controller_{url_suffix.split("/")[-1].lower()}.json'
    write_json_to_file(final_json, filename)
    

if __name__ == "__main__":
    logging.info('Starting the script.')
    
    # Load credentials from config file or fall back to console input
    credentials = load_config()
    
    # Execute main function for both endpoints
    main(credentials['ip'], credentials['username'], credentials['password'],
         '/mgmt/system/config/tree/Physical')
    
    main(credentials['ip'], credentials['username'], credentials['password'],
         '/mgmt/system/config/tree/Organization')
     
    logging.info('Finishing the script.')
    print("Done.")
#    print("This prompt will be closed in 5 seconds.")
#    print("You can see the log file in this directory")

#    time.sleep(1)