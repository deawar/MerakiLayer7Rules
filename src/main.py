import meraki
import json
import yaml

# This script is based off the MEraki API documentation and the Github of Xavier VALETTE (xvalette)
# at https://github.com/xaviervalette/meraki-update-l7-firewall-rules.
# Author: Dean Warren with contributions from Jacob Warren.
# Created: 8/17/2024

# Open the config.yml file and load its contents into the 'config' variable
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

# Pull credentials/NetworkId from YAML file
# (networkId will need to be pulled from different part of API-maybe separate function in future)
API_KEY = config["apiKey"]
dashboard = meraki.DashboardAPI(API_KEY)
network_id = config["networkId"]

# Get existing rules from the target network and save to existingRules dictionary
existing_rules = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(
    network_id
)

# For testing puropses-this print will be removed for production.
print("\nExisting Rules downloaded: ", existing_rules)

# Asking user for File name for rules
filename = input("Enter the filename: ")

# Open JSON file and read in new rule attributes to push into layer 7 firewall ruleset
with open(filename) as json_file:
#with open('newRules.json') as json_file:
    file_contents = json.load(json_file)

# For testing puropses-this print will be removed for production.
print("\nnewRules from file: ", file_contents,"\n")

# New rules to be created JSON format
newRules = file_contents

# Combine existing_rules and newRules dict int to new_rules.
policies = newRules["rules"]
print("\nnested policies for newRules: ",policies,"\n")
existing_rules["rules"] += policies
newRules = existing_rules

# For testing puropses-this print will be removed for production.
print("\ncombined JSON newRules to now push to FW: ",newRules,"\n")

# Make the API request using the requests library
response = dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules(
   network_id, 
   rules = newRules["rules"]
   #rules = [{'policy': 'deny', 'type': 'blockedCountries', 'value': ['AF', 'AM', 'CN', 'IR', 'KZ', 'RU', 'TJ', 'TM', 'UZ']}, {'policy': 'deny', 'type': 'ipRange', 'value': '217.160.0.181'}, {'policy': 'deny', 'type': 'host', 'value': 'biter.de'}, {'policy': 'deny', 'type': 'host', 'value': 'b.itzer.de '}, {'policy': 'deny', 'type': 'host', 'value': 'betzer.de'}, {'policy': 'deny', 'type': 'host', 'value': 'pornhub.com'}]
)

# Print the response
print("\nRequest status of code : ", str(response), "\n")