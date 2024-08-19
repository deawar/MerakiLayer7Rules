import meraki
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Open the .env file and pull credentials

API_KEY = os.getenv("apiKey")
dashboard = meraki.DashboardAPI(API_KEY)
network_id = os.getenv("networkId")

existing_rules = {}

# Get existing rules from the target network and save to existingRules dictionary
existing_rules = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(
    network_id
)

# For testing puropses-this print will be removed for production.
print("\nExisting Rules downloaded: ", existing_rules,"\n")

# Open JSON file and read in new rule attributes to push into layer 7 firewall ruleset
with open('newRules.json') as json_file:
    file_contents = json.load(json_file)

print("\nnewRules from file: ", file_contents,"\n")

# New rules to be created JSON format
newRules = file_contents

def normalize_value(value):
    """Helper function to normalize the 'value' field for consistent comparison."""
    if isinstance(value, list):
        return tuple(sorted(value))  # Sort and convert lists to tuples for comparison
    elif isinstance(value, dict):
        return json.dumps(value, sort_keys=True)  # Convert dicts to JSON strings for comparison
    return value

# Function to combine nested dictionaries with lists and eliminate duplicate entries.
def combine_rules(existing_rules, new_rules):
    # Convert the list of rules into a set of tuples to easily identify duplicates
    existing_set = { (rule['policy'], rule['type'], normalize_value(rule['value'])) for rule in existing_rules['rules'] }
    new_set = { (rule['policy'], rule['type'], normalize_value(rule['value'])) for rule in new_rules['rules'] }

    # Combine the two sets
    combined_set = existing_set.union(new_set)

    # Convert the set back to the original dictionary format
    combined_rules = {'rules': []}
    for rule in combined_set:
        normalized_value = rule[2]
        if isinstance(normalized_value, str) and normalized_value.startswith('{'):
            normalized_value = json.loads(normalized_value)  # Convert JSON string back to dict
        elif isinstance(normalized_value, tuple):
            normalized_value = list(normalized_value)  # Convert tuple back to list
        
        combined_rules['rules'].append({
            'policy': rule[0],
            'type': rule[1],
            'value': normalized_value
        })

    return combined_rules

# Combine existing_rules and newRules dict int to new_rules.
combined_rules = combine_rules(existing_rules, newRules)

print("\ncombined JSON newRules to now push to FW: ",combined_rules,"\n")