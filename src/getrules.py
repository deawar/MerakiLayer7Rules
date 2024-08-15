import meraki
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

print("\nRules downloaded: ", response)