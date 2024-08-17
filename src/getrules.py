import meraki
import json
import yaml

# Open the config.yml file and load its contents into the 'config' variable
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

API_KEY = config["apiKey"]
dashboard = meraki.DashboardAPI(API_KEY)
network_id = config["networkId"]
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

# Combine existing_rules and newRules dict int to new_rules.
policies = newRules["rules"]
print("\nnested policies for newRules: ",policies,"\n")
existing_rules["rules"] += policies
newRules = existing_rules

print("\ncombined JSON to now push to FW: ",existing_rules,"\n")
print("\ncombined JSON newRules to now push to FW: ",newRules,"\n")