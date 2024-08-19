import meraki
import json
import os
from dotenv import load_dotenv

load_dotenv()

# This script is based off the MEraki API documentation and the Github of Xavier VALETTE (xvalette)
# at https://github.com/xaviervalette/meraki-update-l7-firewall-rules.
# Author: Dean Warren with contributions from Jacob Warren.
# Created: 8/17/2024

# Pull credentials/NetworkId from.env file
API_KEY = os.getenv("apiKey")
dashboard = meraki.DashboardAPI(API_KEY)
network_id = os.getenv("networkId")

existing_rules = {}

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

# Function to combine nested dictionaries with lists and eliminate duplicate entries.
def combine_rules(existing_rules, new_rules):
    # Convert the list of rules into a set of tuples to easily identify duplicates
    existing_set = { (rule['policy'], rule['type'], tuple(rule['value']) if isinstance(rule['value'], list) else rule['value']) for rule in existing_rules['rules'] }
    new_set = { (rule['policy'], rule['type'], tuple(rule['value']) if isinstance(rule['value'], list) else rule['value']) for rule in new_rules['rules'] }

    # Combine the two sets
    combined_set = existing_set.union(new_set)

    # Convert the set back to the original dictionary format
    combined_rules = {'rules': []}
    for rule in combined_set:
        combined_rules['rules'].append({
            'policy': rule[0],
            'type': rule[1],
            'value': list(rule[2]) if isinstance(rule[2], tuple) else rule[2]
        })

    return combined_rules

# Combine existing_rules and newRules dict int to new_rules.
combined_rules = combine_rules(existing_rules, newRules)

# For testing puropses-this print will be removed for production.
print("\ncombined JSON newRules to now push to FW: ",combined_rules,"\n")

# Make the API request using the requests library
response = dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules(
   network_id, 
   rules = combined_rules["rules"]
)

# Print the response
print("\nRequest status of code : ", str(response), "\n")