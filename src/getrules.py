readMe = '''This is a script to print out to the console a current list of Layer 7 Firewall rules in an organization. 
 It takes a json file and will combine the existing rules with the new ruleset. If there are duplicates it will only
 add new rules. No output will be saved or rules pushed back to the Firewall from this script.

Usage:
 python getrules.py -k [<api key>] -o [<org name>] [<newRules.json>] -f [<output file>] -h [opens helpfile]
 
 **Note anything in [] is optional if supplied in the .env file

 The .env file will need to be populated with your Meraki Dashboard API key and a NetworkId that looks like "N_0000000000000" 
 or "L_0000000000000" of the network firewall you wish to interrogate.

Parameters:
  <new rules file>.json :   JSON file required to add new rules to the firewall.
  -k <api key>          :   Your Meraki Dashboard API key. Requires org-level privilege. If omitted, script
                            looks for an API key in OS environment variable "meraki.DashboardAPI" 
                            OS environment variable "meraki.DashboardAPI"
  -o <org name>         :   Optional. Name of the organization you want to process. Use keyword "/all" to explicitly
                            specify all orgs. Default is "/all"
  -f <output file>      :   Optional. Output file path to save results. Supports .json or .txt extensions.
                            If .json, saves as formatted JSON. If .txt, saves as formatted text.
                            If omitted, output is printed to console only (default behavior).
  -h                    :   Help option that opens this ReadMe.      

Example:
  python getrules.py "newRules.json" -o "Big Industries Inc" 
  python getrules.py "newRules.json" -f "output.json"
  python getrules.py "newRules.json" -f "output.txt"

Notes:
 * In Windows, use double quotes ("") to enter command line parameters containing spaces.
 * This script was built for Python 3.7.1.
 * Depending on your operating system, the command to start python can be either "python" or "python3". 

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
# Note: getopt stops at first non-option, so we need to handle -f flag manually if it comes after positional args
output_file = None
args = []

# First, manually check for -f flag anywhere in arguments (handles case where it comes after positional args)
for i, arg in enumerate(sys.argv[1:], 1):
    if arg in ('-f', '--file') and i < len(sys.argv) - 1:
        output_file = sys.argv[i + 1]
        break

# Then use getopt for proper parsing (it will handle -f if it comes before positional args)
try:
    opts, remaining_args = getopt.getopt(sys.argv[1:], "hk:o:f:", ["help", "key=", "org=", "file="])
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(readMe)
            sys.exit()
        elif opt in ("-f", "--file"):
            output_file = arg  # Override with getopt result if it parsed it
    # Combine getopt args with any remaining positional arguments
    args = remaining_args
except getopt.GetoptError as e:
    # If there's an error parsing, continue with defaults
    print(f"Warning: Error parsing arguments: {e}")
    # Extract positional arguments (non-option args)
    if not args:  # Only set if we didn't get args from getopt
        args = [arg for arg in sys.argv[1:] if not arg.startswith('-') and arg != output_file]

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
   
# Pull the orgId by using the orgName
	# Search for the org
def get_org_name(orgs, orgName):
    orgs = meraki.organizations.get_organizations()
    for org in orgs:
        if org['name'] == orgName:
            orgId=org['id']
            break;

existing_rules = {}

# Get existing rules from the target network and save to existingRules dictionary
existing_rules = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(
    network_id
)

# For testing puropses-this print will be removed for production.
existing_rules_output = "\nExisting Rules downloaded: " + json.dumps(existing_rules, indent=2) + "\n"
print(existing_rules_output)
if output_file:
    output_content.append(existing_rules_output.strip())
    if output_file.endswith('.json'):
        output_data['existing_rules'] = existing_rules

# Open JSON file and read in new rule attributes to push into layer 7 firewall ruleset
rules_file = 'newRules.json'
if args:
    rules_file = args[0]

with open(rules_file) as json_file:
    file_contents = json.load(json_file)

new_rules_output = "\nNewRules from file: " + json.dumps(file_contents, indent=2) + "\n"
print(new_rules_output)
if output_file:
    output_content.append(new_rules_output.strip())
    if output_file.endswith('.json'):
        output_data['new_rules'] = file_contents

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

combined_output = "\nCombined JSON newRules to now push to FW: " + json.dumps(combined_rules, indent=2) + "\n"
print(combined_output)
if output_file:
    output_content.append(combined_output.strip())
    if output_file.endswith('.json'):
        output_data['combined_rules'] = combined_rules

# Write all output to file if specified
if output_file:
    write_final_output(output_file)