import meraki
import requests
import json
import yaml


# Open the config.yml file and load its contents into the 'config' variable
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

API_KEY = config["apiKey"]
dashboard = meraki.DashboardAPI(API_KEY)
network_id = config["networkId"]

response = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(
    network_id
)
currentRules = response
print("\nExisting rules: ", currentRules, "\n")
# New rules to be created
newRules = {'rules': [{'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/101', 'name': 'CBS Sports'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/40', 'name': 'ESPN'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/96', 'name': 'foxsports.com'}}]}

# Append new rules to exiting rules
updatedRules = currentRules.update(newRules)
print("\nCombined rules: ", updatedRules, "\n")

# Create the URL for retrieving all VLANs in the network
url = f"https://api.meraki.com/api/v1/networks/{config['networkId']}/appliance/firewall/l7FirewallRules"

# Set the HTTP headers
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Cisco-Meraki-API-Key": config["apiKey"]
}
print("url: ", url,headers)
# Make the API request using the requests library
response = requests.request("PUT", url, headers=headers, data=json.dumps(updatedRules))

# Print the status code of the response
print("\nRequest status code : ", str(response), "\n")