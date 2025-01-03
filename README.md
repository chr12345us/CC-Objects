# CyberController Objects Scripts #
These tools will allow you to download and upload all Cyber Controller objects (sites, Alteon devices, DefensePro devices) to another Cyber Controller.
Or, use a downloaded json file to update credentials and secrets for devices in the Organization tree.

## Table Of Contents ###
- [Description](#description)
- [Pre Requisites](#Pre-Requisites)
- [How To Use](#how-to-use)
- [Currently Supported](#currently-supported)
- [Notes on Passwords] (#Notes-on-Passwords)
- [Disclaimer](#Disclaimer)

## Description ##
The script described is provided to help with migration for organizations that want to copy sites and devices from a Cyber-Controller instance to another one.

The tool is designed to copy Alteon and DefensePro devices.

The tool works for both physical and virtual devices.

The tool changes the name of the root site if needed for both the **Physical Containers** and **Sites and Devices sections**.

The tool is tested on both Cyber Controller and Vision products, with various versions from Vision 4.85 to Cyber Controller 10.7.0.

## Pre Requisites ##
The RTU license on the destination Cyber Controller should be able to support the additional devices from the source Cyber Controller.

## How To Use ##
Verify that Python3.10 or later is installed on your computer.
The script uses the following modules:
* requests
* urllib3 (it is a dependancy for requests)

Included in python libraries:
* time
* json
* os
* getpass
* logging

There are four scripts:
- download_cybercontroller_objects.py
	Downloads the Sites and Devices into 2 json files:
		cyber_controller_organization.json - for sites and devices in the organization tree
		cyber_controller_physical.json - for sites and devices in the physical tree
	The files can be used for backup purposes or to clone sites and devices to a different server while having the ability to make modifications to names, ips, credentials etc.	
- upload_cybercontroller_objects.py
	Uploads the sites and devices to a destination server using the two json files exported from a previous download.
- update_json_credentials.py
	Updates credentials used to connect CC to devices. 
	Runing the script creates a new output file: cyber_controller_organization_updated.json
	For input, it uses the original cyber_controller_organization.json and two other files: clicredentials.ini and snmpcredentials.ini - some .example files are in the source directory. 
	If the files do not exist or credentials in the files do not match any existing data in the organization json file, nothing will be changed.
- update_cybercontroller_objects.py
	Updates certain items from devices in the Organization Tree, such as credentials for SHH/HTTPS and SNMP connectivity, using the cyber_controller_organization_updated.json file (file needs to be created from cyber_controller_organization.json either by editing directly or using another script)
	NOTE: for the "update" script, use the "download" script to get the json files from the same device!

Each of these scripts can get credentials interactively when the script is started or from a corresponding ini file: download.ini, upload.ini and update.ini
The structure of each of these files is:
	[credentials]
	ip = cc-ipaddress
	username = cc-username
	password = cc-password

How to run (from the command line of the device that has python and the scripts, in the directory with the scripts):

	python3 download_cybercontroller_objects.py # or the desired scripts

- Follow the instructions in the terminal and provide the cyber controller ip and credentials (if you didn't use the ini file).

- After the script finishes, you can refer to corresponding log file (for instance **download_cyber_controller_objects.log**) in the current directory

- Check the two json files.

- If this was an upload or update, refresh the destination Cyber-Controller screen and verify that the objects are there and that the CC has proper connectivity to them.


## Currently Supported ##
* Site objects
* Physical and virtual Alteon devices
* Physical and virtual Defense-Pro devices

## Notes on Passwords ##

** Passwords and secrets are saved in clear text!!! ** The reason is to be able to easily use them for updates.

** Notes on passwords limitations in the scripts ** (common network device limitations):

	Safe characters to use:

	Alphanumeric (a-z, A-Z, 0-9)
	Common special characters: @ # $ % ^ & * - _ + =
	Length typically between 8-32 characters

	Characters to avoid:

	Space/whitespace characters
	Quotes (single ' or double ")
	Backticks (`)
	Angle brackets (< >)
	Forward or backward slashes (/ )
	Pipe symbol (|)
	Semicolons (;)
	Curly braces ({ })
	Square brackets ([ ])
	Control characters or non-printable ASCII
	
## Disclaimer ##
There is no warranty, expressed or implied, associated with this product. Use at your own risk.