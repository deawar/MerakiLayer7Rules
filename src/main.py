import meraki
import json
import os
import sys
import getopt
from dotenv import load_dotenv

load_dotenv()

# This script is based off the Meraki API documentation and the Github of Xavier VALETTE (xvalette)
# at https://github.com/xaviervalette/meraki-update-l7-firewall-rules.
# Author: Dean Warren with contributions from Jacob Warren.
# Created: 8/17/2024

# Parse command line arguments
process_all_orgs = False
process_all_networks = False
org_name_for_all_networks = None
org_names_list = None
network_ids_list = None

# Help text
help_text = '''This script updates Layer 7 Firewall rules on Meraki MX networks.
It combines existing rules with new rules from a JSON file and pushes the combined ruleset to the firewall.

⚠ WARNING: This script WILL MODIFY your firewall rules. Use getrules.py to preview changes first.

Usage:
  python main.py [--all-orgs] [--all-networks <org_name>] [--orgs <org_names>] [--networks <network_ids>] [-h]

Parameters:
  --all-orgs            : Process ALL organizations you have access to. For each org, processes all MX networks.
                          This will loop through every organization and every network within each organization.
                          
  --all-networks <org_name> : Process all MX networks in the specified organization.
                              Uses orgName from .env file if org_name is omitted.
                              Only MX/appliance networks are processed (non-MX networks are skipped).
                              
  --orgs <org_names>    : Process specific organizations by providing a comma-separated list of organization names.
                          For each org, processes all MX networks within that org.
                          Example: --orgs "Org1,Org2,Org3"
                          
  --networks <ids>      : Process specific networks by providing a comma-separated list of network IDs.
                          Example: --networks "L_123456789,L_987654321"
                          Only MX/appliance networks are processed (non-MX networks are skipped).
                          
  -h, --help            : Display this help message.

Default Behavior:
  If no flags are provided, the script uses networkId from .env file for a single network.
  The script will prompt you for the filename containing new rules.

Examples:
  python main.py
  python main.py --all-orgs
  python main.py --all-networks "My Organization"
  python main.py --all-networks
  python main.py --orgs "Org1,Org2"
  python main.py --networks "L_123456789,L_987654321"

Notes:
  * In Windows, use double quotes ("") to enter command line parameters containing spaces.
  * The .env file must contain 'apiKey' and optionally 'networkId' and 'orgName'.
  * Layer 7 firewall rules only work on MX/appliance networks.
  * Non-MX networks are automatically skipped with a warning message.
  * The script will show a summary of successful and failed network updates at the end.
  * Processing order: --all-orgs > --all-networks/--orgs > --networks > default (single network from .env)
'''

# Check for flags manually first
for i, arg in enumerate(sys.argv[1:], 1):
    if arg in ('-h', '--help'):
        print(help_text)
        sys.exit(0)
    elif arg == '--all-orgs':
        process_all_orgs = True
    elif arg == '--all-networks':
        process_all_networks = True
        if i < len(sys.argv) - 1 and not sys.argv[i + 1].startswith('-'):
            org_name_for_all_networks = sys.argv[i + 1]
    elif arg == '--orgs' and i < len(sys.argv) - 1:
        org_names_list = sys.argv[i + 1].split(',')
    elif arg == '--networks' and i < len(sys.argv) - 1:
        network_ids_list = sys.argv[i + 1].split(',')
    # Backward compatibility: --all is treated as --all-networks
    elif arg == '--all':
        process_all_networks = True
        if i < len(sys.argv) - 1 and not sys.argv[i + 1].startswith('-'):
            org_name_for_all_networks = sys.argv[i + 1]

# Use getopt for proper parsing
try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "all-orgs", "all-networks=", "orgs=", "networks=", "all="])
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_text)
            sys.exit()
        elif opt == "--all-orgs":
            process_all_orgs = True
        elif opt == "--all-networks":
            process_all_networks = True
            if arg:
                org_name_for_all_networks = arg
        elif opt == "--orgs":
            org_names_list = arg.split(',')
        elif opt == "--networks":
            network_ids_list = arg.split(',')
        # Backward compatibility
        elif opt == "--all":
            process_all_networks = True
            if arg:
                org_name_for_all_networks = arg
except getopt.GetoptError:
    pass  # Continue with defaults

# Pull credentials/NetworkId from.env file
API_KEY = os.getenv("apiKey")
if not API_KEY:
    print("ERROR: API key not found in .env file. Please set 'apiKey' in your .env file.")
    sys.exit(1)

dashboard = meraki.DashboardAPI(API_KEY)
network_id = os.getenv("networkId")

# Helper function to check if network is MX/appliance type
def is_mx_network(network_id, network_type=None):
    """Check if a network is an MX/appliance network that supports Layer 7 rules."""
    # MX networks typically have type "appliance" or network ID starts with "L_"
    if network_id.startswith('L_'):
        return True
    if network_type and network_type.lower() == 'appliance':
        return True
    return False

# Helper function to get network IDs from organization name
def get_network_ids_from_org(dashboard, org_name):
    """Get all MX/appliance network IDs for a given organization name."""
    try:
        # Get all organizations
        organizations = dashboard.organizations.getOrganizations()
        
        # Find the organization ID by name (case-insensitive match)
        org_id = None
        org_name_lower = org_name.lower()
        for org in organizations:
            if org['name'].lower() == org_name_lower:
                org_id = org['id']
                break
        
        if not org_id:
            # List available organizations to help user
            available_orgs = [org['name'] for org in organizations]
            error_msg = f"Organization '{org_name}' not found.\n\nAvailable organizations:\n"
            for org in organizations:
                error_msg += f"  - {org['name']} (ID: {org['id']})\n"
            raise ValueError(error_msg)
        
        # Get all networks for the organization
        networks = dashboard.organizations.getOrganizationNetworks(org_id)
        
        if not networks:
            raise ValueError(f"No networks found in organization '{org_name}'.")
        
        # Filter to only MX/appliance networks (Layer 7 rules only work on MX networks)
        # MX networks typically have type "appliance" or network ID starts with "L_"
        mx_networks = []
        skipped_networks = []
        
        for network in networks:
            network_type = network.get('type', '').lower()
            network_id = network.get('id', '')
            
            # Check if it's an MX/appliance network
            if network_type == 'appliance' or network_id.startswith('L_'):
                mx_networks.append(network)
            else:
                skipped_networks.append({
                    'name': network.get('name', 'Unknown'),
                    'id': network_id,
                    'type': network_type
                })
        
        if skipped_networks:
            print(f"\n⚠ Skipping {len(skipped_networks)} non-MX network(s) (Layer 7 rules only work on MX/appliance networks):")
            for net in skipped_networks:
                print(f"  - {net['name']} ({net['id']}) - Type: {net['type']}")
        
        if not mx_networks:
            raise ValueError(f"No MX/appliance networks found in organization '{org_name}'. Layer 7 firewall rules only work on MX networks.")
        
        # Extract network IDs
        network_ids = [network['id'] for network in mx_networks]
        return network_ids, mx_networks
    except Exception as e:
        raise Exception(f"Error fetching networks from organization '{org_name}': {str(e)}")

existing_rules = {}

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

# Function to filter out unsupported rule types
def filter_unsupported_rules(rules):
    """Filter out rule types that are not supported by the Meraki API for Layer 7 firewall rules."""
    # blockedCountries is not supported in Layer 7 firewall rules API
    # (even though it may appear when reading rules, it cannot be set via API)
    unsupported_types = ['blockedCountries']
    filtered_rules = []
    skipped_rules = []
    
    for rule in rules:
        if rule.get('type') in unsupported_types:
            skipped_rules.append(rule)
        else:
            filtered_rules.append(rule)
    
    if skipped_rules:
        print(f"\n⚠ Warning: Skipping {len(skipped_rules)} unsupported rule(s):")
        for rule in skipped_rules:
            print(f"  - {rule.get('type')} rule (not supported by Layer 7 firewall API)")
    
    return filtered_rules

# Function to process a single network
def process_network(dashboard, network_id, network_name, newRules):
    """Process and update rules for a single network."""
    print(f"\n{'='*80}")
    print(f"Processing Network: {network_name} (ID: {network_id})")
    print(f"{'='*80}")
    
    # Check if this is an MX network before processing
    if not is_mx_network(network_id):
        error_msg = f"⚠ Skipping {network_name} ({network_id}): Not an MX/appliance network. Layer 7 firewall rules only work on MX networks."
        print(error_msg)
        return False, error_msg
    
    try:
        # Get existing rules from the target network
        existing_rules = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(network_id)
        
        print(f"\nExisting Rules downloaded for {network_name}: ", existing_rules)
        
        # Combine existing_rules and newRules
        combined_rules = combine_rules(existing_rules, newRules)
        
        # Filter out unsupported rule types before sending to API
        filtered_rules = filter_unsupported_rules(combined_rules["rules"])
        
        if not filtered_rules:
            error_msg = f"No supported rules to apply for {network_name}. All rules were filtered out as unsupported."
            print(f"\n⚠ {error_msg}")
            return False, error_msg
        
        print(f"\nCombined JSON newRules for {network_name} to now push to FW ({len(filtered_rules)} rule(s)): ", 
              json.dumps({'rules': filtered_rules}, indent=2), "\n")
        
        # Make the API request to update rules
        response = dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules(
            network_id, 
            rules=filtered_rules
        )
        
        print(f"\nResulting ruleset for {network_name}: ", str(response), "\n")
        return True, None
    except Exception as e:
        error_msg = f"ERROR processing network {network_name} ({network_id}): {str(e)}"
        print(error_msg)
        return False, error_msg

# Determine which networks to process
network_ids_to_process = []
network_info = {}  # Store network name/id mapping

if process_all_orgs:
    # Process all organizations - loop through each org and get all networks
    print("Fetching all organizations...")
    try:
        all_organizations = dashboard.organizations.getOrganizations()
        print(f"Found {len(all_organizations)} organization(s)\n")
        
        for org_idx, org in enumerate(all_organizations, 1):
            org_name = org['name']
            org_id = org['id']
            print(f"[{org_idx}/{len(all_organizations)}] Processing organization: {org_name} (ID: {org_id})")
            
            try:
                network_ids, networks = get_network_ids_from_org(dashboard, org_name)
                # Store network info with org context
                for net in networks:
                    net_id = net['id']
                    net_name = net.get('name', 'Unknown')
                    network_info[net_id] = f"{org_name} - {net_name}"
                    network_ids_to_process.append(net_id)
                print(f"  Added {len(network_ids)} network(s) from {org_name}\n")
            except Exception as e:
                print(f"  ⚠ Skipping organization {org_name}: {str(e)}\n")
                continue
        
        if not network_ids_to_process:
            print("ERROR: No MX networks found in any accessible organization.")
            sys.exit(1)
        print(f"Total: {len(network_ids_to_process)} network(s) to process across {len(all_organizations)} organization(s)\n")
    except Exception as e:
        print(f"ERROR fetching organizations: {str(e)}")
        sys.exit(1)
elif process_all_networks:
    # Get org name from argument or .env
    org_name = org_name_for_all_networks or os.getenv("orgName")
    if not org_name:
        print("ERROR: --all-networks flag requires organization name. Provide it as argument or set 'orgName' in .env file.")
        sys.exit(1)
    
    print(f"Fetching all networks from organization: {org_name}")
    try:
        network_ids, networks = get_network_ids_from_org(dashboard, org_name)
        network_ids_to_process = network_ids
        # Store network info for display
        for net in networks:
            network_info[net['id']] = net.get('name', 'Unknown')
        print(f"Found {len(network_ids_to_process)} network(s) to process\n")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
elif org_names_list:
    # Process specific organizations - loop through each org and get all networks
    org_names_to_process = [name.strip() for name in org_names_list]
    print(f"Processing {len(org_names_to_process)} specified organization(s)\n")
    
    for org_idx, org_name in enumerate(org_names_to_process, 1):
        print(f"[{org_idx}/{len(org_names_to_process)}] Processing organization: {org_name}")
        try:
            network_ids, networks = get_network_ids_from_org(dashboard, org_name)
            # Store network info with org context
            for net in networks:
                net_id = net['id']
                net_name = net.get('name', 'Unknown')
                network_info[net_id] = f"{org_name} - {net_name}"
                network_ids_to_process.append(net_id)
            print(f"  Added {len(network_ids)} network(s) from {org_name}\n")
        except Exception as e:
            print(f"  ⚠ Skipping organization {org_name}: {str(e)}\n")
            continue
    
    if not network_ids_to_process:
        print("ERROR: No MX networks found in any of the specified organizations.")
        sys.exit(1)
    print(f"Total: {len(network_ids_to_process)} network(s) to process\n")
elif network_ids_list:
    # Process specific network IDs
    network_ids_to_process = [nid.strip() for nid in network_ids_list]
    print(f"Processing {len(network_ids_to_process)} specified network(s)\n")
    # Try to get network names and filter to MX networks only
    try:
        organizations = dashboard.organizations.getOrganizations()
        mx_network_ids = []
        for org in organizations:
            try:
                networks = dashboard.organizations.getOrganizationNetworks(org['id'])
                for net in networks:
                    net_id = net['id']
                    if net_id in network_ids_to_process:
                        # Only include MX/appliance networks
                        if is_mx_network(net_id, net.get('type')):
                            network_info[net_id] = net.get('name', 'Unknown')
                            mx_network_ids.append(net_id)
                        else:
                            print(f"⚠ Skipping {net.get('name', net_id)} ({net_id}): Not an MX/appliance network")
            except:
                continue  # Skip this org if we can't get its networks
        # Update to only process MX networks
        network_ids_to_process = [nid for nid in network_ids_to_process if nid in mx_network_ids]
        if not network_ids_to_process:
            print("ERROR: None of the specified network IDs are MX/appliance networks. Layer 7 firewall rules only work on MX networks.")
            sys.exit(1)
    except:
        pass  # If we can't get names, just use IDs (but will fail later if not MX)
else:
    # Default: single network from .env
    if not network_id:
        print("ERROR: No network ID provided. Use --all-orgs, --all-networks, --orgs, --networks, or set 'networkId' in .env file.")
        sys.exit(1)
    # Check if it's an MX network
    if not is_mx_network(network_id):
        print(f"ERROR: Network ID '{network_id}' is not an MX/appliance network. Layer 7 firewall rules only work on MX networks.")
        sys.exit(1)
    network_ids_to_process = [network_id]
    network_info[network_id] = "Network from .env"

# Ask user for file name for rules
filename = input("\nEnter the filename: ")

# Open JSON file and read in new rule attributes
with open(filename) as json_file:
    file_contents = json.load(json_file)

newRules = file_contents
print("\nNewRules from file: ", file_contents, "\n")

# Process each network
success_count = 0
error_count = 0

for idx, net_id in enumerate(network_ids_to_process, 1):
    net_name = network_info.get(net_id, net_id)
    print(f"\n[{idx}/{len(network_ids_to_process)}] Processing: {net_name}")
    
    success, error = process_network(dashboard, net_id, net_name, newRules)
    if success:
        success_count += 1
    else:
        error_count += 1

# Summary
print(f"\n{'='*80}")
print(f"Summary: {success_count} network(s) updated successfully, {error_count} network(s) failed")
print(f"{'='*80}\n")