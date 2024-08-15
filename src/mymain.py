import requests
import json
import yaml

# Open the config.yml file and load its contents into the 'config' variable
with open('config.yml', 'r') as file:
  config = yaml.safe_load(file)

# New rules to be created
newRules = {'rules': [{'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/101', 'name': 'CBS Sports'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/40', 'name': 'ESPN'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/96', 'name': 'foxsports.com'}}]}

# Create the URL for retrieving all VLANs in the network
url = f"https://api.meraki.com/api/v1/networks/{config['networkId']}/appliance/firewall/l7FirewallRules"
print ("\nURL: ",url)

# Set the HTTP headers
headers = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "X-Cisco-Meraki-API-Key": config["apiKey"]
}

# Make the API request using the requests library
response = requests.request("PUT", url, headers=headers, data=json.dumps(newRules))

# Print the response
print("\nRequest status code : "+str(response), "\n")

