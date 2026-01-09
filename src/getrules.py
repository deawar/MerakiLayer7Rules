readMe = '''This is a script to print out to the console a current list of Layer 7 Firewall rules in an organization. 
 It takes a json file and will combine the existing rules with the new ruleset. If there are duplicates it will only
 add new rules. No output will be saved or rules pushed back to the Firewall from this script.

Usage:
 python getrules.py [<newRules.json>] -f [<output file>] --all-orgs --all-networks [<org name>] --orgs [<org names>] --networks [<network ids>] -h
 
 **Note anything in [] is optional if supplied in the .env file

 The .env file will need to be populated with your Meraki Dashboard API key and optionally a NetworkId that looks like "N_0000000000000" 
 or "L_0000000000000" of the network firewall you wish to interrogate (unless using flags to specify networks/orgs).

Parameters:
  <new rules file>.json :   JSON file required to add new rules to the firewall. Defaults to 'newRules.json' if omitted.
  -f <output file>      :   Optional. Output file path to save results. Supports .json or .txt extensions.
                            If .json, saves as formatted JSON. If .txt, saves as formatted text.
                            If omitted, output is printed to console only (default behavior).
  --all-orgs            :   Process ALL organizations you have access to. For each org, processes all MX networks.
                            This will loop through every organization and every network within each organization.
  --all-networks [<org name>] : Process all MX networks in the specified organization. Uses orgName from .env if omitted.
  --orgs <org names>    :   Process specific organizations by providing a comma-separated list of organization names.
                            For each org, processes all MX networks within that org.
                            Example: --orgs "Org1,Org2,Org3"
  --networks <ids>      :   Process specific networks by providing a comma-separated list of network IDs.
                            Example: --networks "L_123456789,L_987654321"
  -h, --help            :   Help option that opens this ReadMe.      

Example:
  python getrules.py "newRules.json" 
  python getrules.py "newRules.json" -f "output.json"
  python getrules.py "newRules.json" --all-orgs -f "output.json"
  python getrules.py "newRules.json" --all-networks "My Organization"
  python getrules.py "newRules.json" --orgs "Org1,Org2" -f "output.json"
  python getrules.py "newRules.json" --networks "L_123456789,L_987654321" -f "output.json"

Notes:
 * In Windows, use double quotes ("") to enter command line parameters containing spaces.
 * This script was built for Python 3.7.1.
 * Depending on your operating system, the command to start python can be either "python" or "python3". 
 * Default behavior (no flags) uses networkId from .env file for a single network.
 * Only MX/appliance networks are processed (non-MX networks are automatically skipped).
 * Processing order: --all-orgs > --all-networks/--orgs > --networks > default (single network from .env)

Required Python modules:
  Requests     : http://docs.python-requests.org
After installing Python, you can install these additional modules using pip with the following commands:
  pip install requests

Depending on your operating system, the command can be "pip3" instead of "pip".'''

import meraki
import json
import os, sys, getopt, time, datetime
from dotenv import load_dotenv

load_dotenv()

# Parse command line arguments
# Note: getopt stops at first non-option, so we need to handle flags manually if they come after positional args
output_file = None
args = []
process_all_orgs = False
process_all_networks = False
org_name_for_all_networks = None
org_names_list = None
network_ids_list = None

# First, manually check for flags anywhere in arguments (handles case where they come after positional args)
for i, arg in enumerate(sys.argv[1:], 1):
    if arg in ('-h', '--help'):
        print(readMe)
        sys.exit(0)
    elif arg in ('-f', '--file') and i < len(sys.argv) - 1:
        output_file = sys.argv[i + 1]
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

# Then use getopt for proper parsing (it will handle flags if they come before positional args)
try:
    opts, remaining_args = getopt.getopt(sys.argv[1:], "hk:o:f:", ["help", "key=", "org=", "file=", "all-orgs", "all-networks=", "orgs=", "networks=", "all="])
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(readMe)
            sys.exit()
        elif opt in ("-f", "--file"):
            output_file = arg  # Override with getopt result if it parsed it
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
    # Combine getopt args with any remaining positional arguments
    args = remaining_args
except getopt.GetoptError as e:
    # If there's an error parsing, continue with defaults
    print(f"Warning: Error parsing arguments: {e}")
    # Extract positional arguments (non-option args)
    if not args:  # Only set if we didn't get args from getopt
        excluded = [output_file] if output_file else []
        if network_ids_list:
            excluded.extend(network_ids_list)
        if org_names_list:
            excluded.extend(org_names_list)
        args = [arg for arg in sys.argv[1:] if not arg.startswith('-') and arg not in excluded]

# Option Function
def killScript(reason=None):
    if reason is None:
        print(readMe)
        sys.exit()
    else:
        print("ERROR: %s" % reason)
        log("ERROR: %s" % reason)
        sys.exit()
        
# Print Help File
def printhelp():
    print(readMe) 

# Output collection for file writing
output_content = []
output_data = {}

# Function to write final output to file
def write_final_output(file_path):
    """Write all collected output to file based on extension."""
    if not file_path:
        return
    
    # Convert to absolute path for clarity
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            # Write as structured JSON with all data
            with open(file_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\n✓ Output saved to {file_path} (JSON format)")
        else:
            # Write as formatted text (default for .txt or any other extension)
            with open(file_path, 'w') as f:
                f.write('\n'.join(output_content))
            print(f"\n✓ Output saved to {file_path} (text format)")
    except Exception as e:
        error_msg = f"ERROR: Unable to write to output file '{file_path}': {str(e)}"
        print(error_msg)
        try:
            log(error_msg)
        except:
            pass  # If log function has issues, at least we printed the error

# Open the .env file and pull credentials
API_KEY = os.getenv("apiKey")
if API_KEY is None:
    killScript()
dashboard = meraki.DashboardAPI(API_KEY)
network_id = os.getenv("networkId")
org_list = os.getenv("orgList")

# Generate logfile if errors
def log(text, filePath=None):
    logString = "%s -- %s" % (str(datetime.datetime.now())[:19], text)
    print(logString)
    if not filePath is None:
        try:
            with open(filePath, "a") as logFile:
                logFile.write("%s\n" % logString)
        except:
            log("ERROR: Unable to append to log file")
   
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

# Function to check if network is MX/appliance type
def is_mx_network(network_id, network_type=None):
    """Check if a network is an MX/appliance network that supports Layer 7 rules."""
    # MX networks typically have type "appliance" or network ID starts with "L_"
    if network_id.startswith('L_'):
        return True
    if network_type and network_type.lower() == 'appliance':
        return True
    return False

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
        warning_msg = f"\n⚠ Warning: {len(skipped_rules)} unsupported rule(s) will be skipped when applying:"
        print(warning_msg)
        for rule in skipped_rules:
            print(f"  - {rule.get('type')} rule (not supported by Layer 7 firewall API)")
    
    return filtered_rules, skipped_rules

# Function to process a single network
def process_network(dashboard, network_id, network_name, newRules, output_file, output_content, output_data):
    """Process rules for a single network."""
    network_output = []
    network_data = {}
    
    print(f"\n{'='*80}")
    print(f"Processing Network: {network_name} (ID: {network_id})")
    print(f"{'='*80}")
    
    # Check if this is an MX network before processing
    if not is_mx_network(network_id):
        error_msg = f"⚠ Skipping {network_name} ({network_id}): Not an MX/appliance network. Layer 7 firewall rules only work on MX networks."
        print(error_msg)
        log(error_msg)
        return None, [error_msg], error_msg
    
    try:
        # Get existing rules from the target network
        existing_rules = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(network_id)
        
        existing_rules_output = f"\nExisting Rules downloaded for {network_name}: " + json.dumps(existing_rules, indent=2) + "\n"
        print(existing_rules_output)
        network_output.append(existing_rules_output.strip())
        if output_file and output_file.endswith('.json'):
            network_data['existing_rules'] = existing_rules
        
        # Combine existing_rules and newRules
        combined_rules = combine_rules(existing_rules, newRules)
        
        # Filter out unsupported rule types
        filtered_rules, skipped_rules = filter_unsupported_rules(combined_rules["rules"])
        
        # Store both filtered and original for output
        combined_rules_filtered = {'rules': filtered_rules}
        if skipped_rules:
            network_data['skipped_unsupported_rules'] = skipped_rules
        
        combined_output = f"\nCombined JSON newRules for {network_name} to now push to FW ({len(filtered_rules)} supported rule(s)): " + json.dumps(combined_rules_filtered, indent=2) + "\n"
        print(combined_output)
        network_output.append(combined_output.strip())
        if output_file and output_file.endswith('.json'):
            network_data['combined_rules'] = combined_rules_filtered
            network_data['combined_rules_all'] = combined_rules  # Keep original for reference
        
        return network_data, network_output, None
    except Exception as e:
        error_msg = f"ERROR processing network {network_name} ({network_id}): {str(e)}"
        print(error_msg)
        log(error_msg)
        return None, network_output, error_msg

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
            killScript("ERROR: No MX networks found in any accessible organization.")
        print(f"Total: {len(network_ids_to_process)} network(s) to process across {len(all_organizations)} organization(s)\n")
    except Exception as e:
        killScript(f"ERROR fetching organizations: {str(e)}")
elif process_all_networks:
    # Get org name from argument or .env
    org_name = org_name_for_all_networks or os.getenv("orgName")
    if not org_name:
        killScript("ERROR: --all-networks flag requires organization name. Provide it as argument or set 'orgName' in .env file.")
    
    print(f"Fetching all networks from organization: {org_name}")
    try:
        network_ids, networks = get_network_ids_from_org(dashboard, org_name)
        network_ids_to_process = network_ids
        # Store network info for display
        for net in networks:
            network_info[net['id']] = net.get('name', 'Unknown')
        print(f"Found {len(network_ids_to_process)} network(s) to process\n")
    except Exception as e:
        killScript(str(e))
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
        killScript("ERROR: No MX networks found in any of the specified organizations.")
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
            killScript("ERROR: None of the specified network IDs are MX/appliance networks. Layer 7 firewall rules only work on MX networks.")
    except:
        pass  # If we can't get names, just use IDs (but will fail later if not MX)
else:
    # Default: single network from .env
    if not network_id:
        killScript("ERROR: No network ID provided. Use --all, --networks, or set 'networkId' in .env file.")
    # Check if it's an MX network
    if not is_mx_network(network_id):
        killScript(f"ERROR: Network ID '{network_id}' is not an MX/appliance network. Layer 7 firewall rules only work on MX networks.")
    network_ids_to_process = [network_id]
    network_info[network_id] = "Network from .env"

# Open JSON file and read in new rule attributes
rules_file = 'newRules.json'
if args:
    rules_file = args[0]

with open(rules_file) as json_file:
    file_contents = json.load(json_file)

newRules = file_contents
new_rules_output = "\nNewRules from file: " + json.dumps(file_contents, indent=2) + "\n"
print(new_rules_output)
if output_file:
    output_content.append(new_rules_output.strip())
    if output_file.endswith('.json'):
        output_data['new_rules'] = file_contents

# Process each network
all_networks_data = {}
for idx, net_id in enumerate(network_ids_to_process, 1):
    net_name = network_info.get(net_id, net_id)
    print(f"\n[{idx}/{len(network_ids_to_process)}] Processing: {net_name}")
    
    net_data, net_output, error = process_network(dashboard, net_id, net_name, newRules, output_file, output_content, output_data)
    
    if output_file:
        output_content.extend(net_output)
        if output_file.endswith('.json') and net_data:
            all_networks_data[net_id] = {
                'network_name': net_name,
                'network_id': net_id,
                **net_data
            }
    else:
        output_content.extend(net_output)

# Update output_data for JSON format
if output_file and output_file.endswith('.json'):
    if len(network_ids_to_process) == 1:
        # Single network: keep existing structure for backward compatibility
        if all_networks_data and network_ids_to_process[0] in all_networks_data:
            net_data = all_networks_data[network_ids_to_process[0]]
            # Keep existing structure: existing_rules, new_rules, combined_rules
            if 'existing_rules' in net_data:
                output_data['existing_rules'] = net_data['existing_rules']
            if 'combined_rules' in net_data:
                output_data['combined_rules'] = net_data['combined_rules']
    else:
        # Multiple networks: use new structure
        output_data['networks'] = all_networks_data
        output_data['total_networks'] = len(network_ids_to_process)
        output_data['processed_networks'] = len([n for n in all_networks_data.values() if n])

# Write all output to file if specified
if output_file:
    write_final_output(output_file)