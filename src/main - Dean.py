import meraki
import requests
import json
import yaml

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

# Open JSON file and read in new rule attributes to push into layer 7 firewall ruleset
with open('newRules.json') as json_file:
    file_contents = json.load(json_file)

print("newRules from file: ", file_contents)



# New rules to be created JSON format
newRules = file_contents
# newRules = '''{
#     "rules": [
#         {
#             "policy": "deny",
#             "type": "host",
#             "value": "botzer.com"
#         },        
#         {
#             "policy": "deny", 
#             "type": "host", 
#             "value": "ESPN.com"
#         }, 
#         {
#             "policy": "deny",
#             "type": "host",
#             "value": "foxsports.com"
#         }
#     ]
# }'''

# Create the URL for retrieving all VLANs in the network
url = f"https://api.meraki.com/api/v1/networks/{config['networkId']}/appliance/firewall/l7FirewallRules"

# Set the HTTP headers
headers = {
    "Authorization": config["apiKey"],
    "Content-Type": "application/json",
    "Accept": "application/json"
}
print ("\nurl: ",url,headers)

# Make the API request using the requests library
response = dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules(
   network_id, 
   rules = newRules
   #rules = [{'policy': 'deny', 'type': 'host', 'value': 'botzer.com'}, {'policy': 'deny', 'type': 'host', 'value': 'ESPN.com'}, {'policy': 'deny', 'type': 'host', 'value': 'FoxSports.com'}]
)

# Print the response
print("\nRequest status of code : ", str(response), "\n")