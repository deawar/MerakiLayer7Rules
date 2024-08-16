import meraki
import requests
import json
import yaml

# Open the config.yml file and load its contents into the 'config' variable
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

# Open JSON file and read in new rule attributes to push into layer 7 firewall ruleset
with open('newRules.json') as json_file:
    file_contents = json.load(json_file)

print("newRules: ", file_contents)


API_KEY = config["apiKey"]
dashboard = meraki.DashboardAPI(API_KEY)
network_id = config["networkId"]

# response = dashboard.organizations.getOrganizations()
# print("Allowed Networks: ",response)

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
#response = requests.request("PUT", url, headers=headers, data=json.dumps(newRules))
#response = requests.request("PUT", url, headers=headers, data = newRules)
response = dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules(
   network_id, 
   rules = newRules
   #rules = [{'policy': 'deny', 'type': 'host', 'value': 'botzer.com'}, {'policy': 'deny', 'type': 'host', 'value': 'ESPN.com'}, {'policy': 'deny', 'type': 'host', 'value': 'FoxSports.com'}]
)

# Print the response
print("\nRequest status of code : ", str(response), "\n")