# Meraki Update L7 Firewall (MX) rules

## Script Forked from:
This script is based off the Meraki API documentation and the Github of Xavier VALETTE (xvalette)
at https://github.com/xaviervalette/meraki-update-l7-firewall-rules.

## What is it?
This repository contains scripts to manage Layer 7 firewall rules on Meraki MX networks. The scripts pull existing Layer 7 firewall rules, combine them with new rules from a JSON file, and can preview or push the combined ruleset back to the firewall.

**Important:** Layer 7 firewall rules only work on MX (security appliance) networks. Non-MX networks are automatically filtered out.

## Scripts

### `getrules.py` - Preview Rules (Read-Only)
A read-only script that fetches existing rules, combines them with new rules, and displays the result. **This script does NOT modify your firewall.**

**Features:**
- Preview combined rules before applying
- Save output to JSON or text files
- Process single network, all networks in an org, all orgs, or specific networks/orgs
- Automatic filtering of non-MX networks

**Usage:**
```console
# Preview rules for single network (from .env)
python src/getrules.py newRules.json

# Preview and save to file
python src/getrules.py newRules.json -f output.json

# Process all organizations and all networks within each org
python src/getrules.py newRules.json --all-orgs -f output.json

# Process all MX networks in a specific organization
python src/getrules.py newRules.json --all-networks "My Organization"

# Process specific organizations (all networks in each)
python src/getrules.py newRules.json --orgs "Org1,Org2" -f output.json

# Process specific networks
python src/getrules.py newRules.json --networks "L_123456789,L_987654321" -f output.json

# Show help
python src/getrules.py -h
```

### `main.py` - Update Rules (Write Operations)
⚠️ **WARNING:** This script WILL MODIFY your firewall rules. Use `getrules.py` to preview changes first.

**Features:**
- Combines existing and new rules
- Updates firewall rules on Meraki MX networks
- Process single network, all networks in an org, all orgs, or specific networks/orgs
- Automatic filtering of non-MX networks
- Summary of successful and failed updates

**Usage:**
```console
# Update single network (from .env)
python src/main.py

# Update all organizations and all networks within each org
python src/main.py --all-orgs

# Update all MX networks in a specific organization
python src/main.py --all-networks "My Organization"

# Update specific organizations (all networks in each)
python src/main.py --orgs "Org1,Org2"

# Update specific networks
python src/main.py --networks "L_123456789,L_987654321"

# Show help
python src/main.py -h
```

### `get_network_id.py` - Find Network IDs
Helper script to retrieve network IDs from an organization name.

**Usage:**
```console
python src/get_network_id.py
```

## Source API
All the api calls were created using the Meraki API V1 Index at https://developer.cisco.com/meraki/api-v1/api-index/

## Prerequisites
- Meraki Dashboard access
- Meraki API key with organization-level privileges
- Meraki network ID (for single network operations) or organization name (for multi-network operations)
- Python 3.7.1 or higher

## Get started
1. Clone or download this repo
```console
git clone https://github.com/deawar/MerakiLayer7Rules
```

2. Install required packages
```console
python3 -m pip install -r requirements.txt
```

3. Rename `sample_config.env` to `.env` and edit it:
```diff
└── MerakiLayer7Rules/
+   ├── .env
    ├── requirements.txt
    ├── newRules.json
    └── src/
         ├── getrules.py
         ├── main.py
         └── get_network_id.py
```

4. In the `.env` file, add the following variables:
```environment
#.env
---
apiKey = "<yourApiKey>"
networkId = "<yourNetworkId>"  # Optional if using --all-orgs, --all-networks, --orgs, or --networks
orgName = "<yourOrgName>"       # Optional, used with --all-networks flag
```

5. Create your new rules JSON file (e.g., `newRules.json`):
```json
{
  "rules": [
    {
      "policy": "deny",
      "type": "host",
      "value": "example.com"
    },
    {
      "policy": "deny",
      "type": "ipRange",
      "value": "1.2.3.4"
    }
  ]
}
```

6. Preview your changes (recommended):
```console
python src/getrules.py newRules.json -f output.json
```

7. Apply changes:
```console
python src/main.py
```

## Command Line Flags

### `getrules.py` Flags
- `-f, --file <output_file>` - Save results to file (.json or .txt)
- `--all-orgs` - Process ALL organizations you have access to. For each org, processes all MX networks.
- `--all-networks [<org_name>]` - Process all MX networks in a specific organization (uses orgName from .env if omitted)
- `--orgs <org_names>` - Process specific organizations by providing a comma-separated list. For each org, processes all MX networks.
- `--networks <network_ids>` - Process specific networks (comma-separated list)
- `-h, --help` - Show help message

### `main.py` Flags
- `--all-orgs` - Process ALL organizations you have access to. For each org, processes all MX networks.
- `--all-networks [<org_name>]` - Process all MX networks in a specific organization (uses orgName from .env if omitted)
- `--orgs <org_names>` - Process specific organizations by providing a comma-separated list. For each org, processes all MX networks.
- `--networks <network_ids>` - Process specific networks (comma-separated list)
- `-h, --help` - Show help message

## How Rule Combination Works

The scripts use an **additive merge** approach:
- **Append**: New unique rules are added to existing rules
- **Deduplicate**: Exact duplicate rules (same policy, type, and value) are kept only once
- **No Removal**: Existing rules are never removed unless they're exact duplicates
- **Preserve All**: All existing rules are preserved, new rules are added

Rules are considered duplicates only if all three match exactly:
- `policy` (e.g., "deny", "allow")
- `type` (e.g., "host", "ipRange", "blockedCountries")
- `value` (normalized for comparison)

## Output Examples

### getrules.py output (JSON format):
```json
{
  "new_rules": { ... },
  "existing_rules": { ... },
  "combined_rules": {
    "rules": [
      {
        "policy": "deny",
        "type": "host",
        "value": "example.com"
      }
    ]
  }
}
```

### main.py output:
```console
Processing Network: My Network (ID: L_123456789)
================================================================================
Existing Rules downloaded for My Network: { ... }
Combined JSON newRules for My Network to now push to FW: { ... }
Resulting ruleset for My Network: { ... }

================================================================================
Summary: 3 network(s) updated successfully, 0 network(s) failed
================================================================================
```

## Notes
- **Windows users**: Use double quotes (`""`) for command line parameters containing spaces
- **Network filtering**: Only MX/appliance networks are processed. Non-MX networks are automatically skipped with a warning
- **Case-insensitive**: Organization name matching is case-insensitive
- **Error handling**: Scripts continue processing other networks even if one fails

## Author and Contributors
This script was written by Dean Warren with extensive help from:
- Jacob Warren
- Jared Haviland
- Patrick Kelley



