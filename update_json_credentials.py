import json
import configparser
import os
from typing import Dict, Optional, List

def load_json_config(filename: str) -> Dict:
    """Load and parse the JSON configuration file."""
    with open(filename, 'r') as f:
        return json.load(f)

def load_credentials(filename: str) -> Optional[Dict]:
    """Load credentials from an INI file."""
    if not os.path.exists(filename):
        return None
        
    config = configparser.ConfigParser()
    config.read(filename)
    print(f"\nLoading credentials from {filename}")
    
    credentials = {}
    # Process each user section
    for section in config.sections():
        if 'old-user' not in config[section] or 'new-user' not in config[section]:
            print(f"Warning: Skipping section {section} - missing old-user or new-user")
            continue
            
        old_username = config[section]['old-user']
        print(f"\nProcessing section {section}:")
        print(f"  Old username: {old_username}")
        print(f"  New username: {config[section]['new-user']}")
        print(f"  Password: {config[section].get('password', '[not set]')}")
        
        credentials[old_username] = {
            'new_username': config[section]['new-user'],
            'credentials': config[section].get('password', '')  # For CLI credentials
        }
        
        # Handle SNMP specific fields if they exist
        if 'auth-password' in config[section] and 'privacy-password' in config[section]:
            credentials[old_username]['credentials'] = f"{config[section]['auth-password']},{config[section]['privacy-password']}"
            
    return credentials

def update_cli_credentials(device: Dict, credentials: Dict) -> tuple[Dict, bool]:
    """Update CLI and HTTP(S) credentials and usernames for a device."""
    device = device.copy()
    access = device['deviceAccess']
    changed = False
    
    print(f"\nChecking device: {device['name']}")
    print(f"  CLI username: {access['cliUsername']}")
    print(f"  HTTP username: {access['httpUsername']}")
    print(f"  HTTPS username: {access['httpsUsername']}")
    print("  Available credentials to match against:", list(credentials.keys()))
    
    # Update CLI credentials
    if access['cliUsername'] in credentials:
        print(f"  Found match for CLI username: {access['cliUsername']}")
        cred_info = credentials[access['cliUsername']]
        access['cliUsername'] = cred_info['new_username']
        access['cliPassword'] = cred_info['credentials']
        changed = True
    
    # Update HTTP credentials
    if access['httpUsername'] in credentials:
        print(f"  Found match for HTTP username: {access['httpUsername']}")
        cred_info = credentials[access['httpUsername']]
        access['httpUsername'] = cred_info['new_username']
        access['httpPassword'] = cred_info['credentials']
        changed = True
    
    # Update HTTPS credentials
    if access['httpsUsername'] in credentials:
        print(f"  Found match for HTTPS username: {access['httpsUsername']}")
        cred_info = credentials[access['httpsUsername']]
        access['httpsUsername'] = cred_info['new_username']
        access['httpsPassword'] = cred_info['credentials']
        changed = True
    
    return device, changed
    
    # Update CLI credentials
    if access['cliUsername'] in credentials:
        cred_info = credentials[access['cliUsername']]
        access['cliUsername'] = cred_info['new_username']
        access['cliPassword'] = cred_info['credentials']
    
    # Update HTTP credentials
    if access['httpUsername'] in credentials:
        cred_info = credentials[access['httpUsername']]
        access['httpUsername'] = cred_info['new_username']
        access['httpPassword'] = cred_info['credentials']
    
    # Update HTTPS credentials
    if access['httpsUsername'] in credentials:
        cred_info = credentials[access['httpsUsername']]
        access['httpsUsername'] = cred_info['new_username']
        access['httpsPassword'] = cred_info['credentials']
    
    return device

def update_snmp_credentials(device: Dict, credentials: Dict) -> tuple[Dict, bool]:
    """Update SNMP V3 credentials and username for a device."""
    device = device.copy()
    access = device['deviceAccess']
    changed = False
    
    print(f"\nChecking SNMP for device: {device['name']}")
    print(f"  SNMP V3 username: {access['snmpV3Username']}")
    print("  Available SNMP credentials to match against:", list(credentials.keys()))
    
    if access['snmpV3Username'] in credentials:
        print(f"  Found match for SNMP username: {access['snmpV3Username']}")
        cred_info = credentials[access['snmpV3Username']]
        access['snmpV3Username'] = cred_info['new_username']
        
        # Split the credentials into auth and privacy passwords
        snmp_creds = cred_info['credentials'].split(',')
        if len(snmp_creds) >= 2:
            access['snmpV3AuthenticationPassword'] = snmp_creds[0].strip()
            access['snmpV3PrivacyPassword'] = snmp_creds[1].strip()
            changed = True
    
    return device, changed
    
    if access['snmpV3Username'] in credentials:
        cred_info = credentials[access['snmpV3Username']]
        access['snmpV3Username'] = cred_info['new_username']
        
        # Split the credentials into auth and privacy passwords
        snmp_creds = cred_info['credentials'].split(',')
        if len(snmp_creds) >= 2:
            access['snmpV3AuthenticationPassword'] = snmp_creds[0].strip()
            access['snmpV3PrivacyPassword'] = snmp_creds[1].strip()
    
    return device

def main():
    # Load the JSON configuration
    config = load_json_config('cyber_controller_organization.json')
    
    # Try to load credentials from either INI file
    cli_creds = load_credentials('clicredentials.ini')
    snmp_creds = load_credentials('snmpsecrets.ini')
    
    if not cli_creds and not snmp_creds:
        print("Error: Neither clicredentials.ini nor snmpsecrets.ini found!")
        return
    
    # Update devices with new credentials and usernames
    updated_devices = []
    any_changes = False
    
    for device in config['devices']:
        device_changed = False
        
        if cli_creds:
            device, cli_changed = update_cli_credentials(device, cli_creds)
            device_changed = device_changed or cli_changed
            
        if snmp_creds:
            device, snmp_changed = update_snmp_credentials(device, snmp_creds)
            device_changed = device_changed or snmp_changed
            
        if device_changed:
            print(f"\nUpdated credentials for device: {device['name']}")
            any_changes = True
            
        updated_devices.append(device)
    
    # Update the configuration with new credentials
    config['devices'] = updated_devices
    
    # Save the updated configuration if changes were made
    if any_changes:
        output_filename = 'cyber_controller_organization_updated.json'
        print(f"\nSaving changes to {output_filename}")
        try:
            with open(output_filename, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Configuration successfully saved to {output_filename}")
        except Exception as e:
            print(f"Error saving file: {str(e)}")
    else:
        print("\nNo changes were made to any devices - no new file created")
        print("\nDebug summary of current usernames:")
        for device in config['devices']:
            print(f"  Device {device['name']}:")
            print(f"    CLI user: {device['deviceAccess']['cliUsername']}")
            print(f"    HTTP user: {device['deviceAccess']['httpUsername']}")
            print(f"    HTTPS user: {device['deviceAccess']['httpsUsername']}")
            print(f"    SNMP V3 user: {device['deviceAccess']['snmpV3Username']}")

if __name__ == "__main__":
    main()