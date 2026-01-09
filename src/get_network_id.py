"""
Script to retrieve Network IDs from Meraki API using Organization Name.

This script:
1. Loads API key and organization name from .env file
2. Gets the organization ID from the organization name
3. Lists all networks in that organization with their IDs

Usage:
    python src/get_network_id.py
"""

import meraki
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from .env file
API_KEY = os.getenv("apiKey")
ORG_NAME = os.getenv("orgName")

if not API_KEY:
    print("ERROR: API key not found in .env file. Please set 'apiKey' in your .env file.")
    exit(1)

if not ORG_NAME:
    print("ERROR: Organization name not found in .env file. Please set 'orgName' in your .env file.")
    exit(1)

# Initialize Meraki Dashboard API
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)

try:
    # Step 1: Get all organizations
    print(f"Fetching organizations...")
    organizations = dashboard.organizations.getOrganizations()
    
    # Step 2: Find the organization ID by name
    org_id = None
    for org in organizations:
        if org['name'] == ORG_NAME:
            org_id = org['id']
            print(f"\n✓ Found organization: {ORG_NAME}")
            print(f"  Organization ID: {org_id}")
            break
    
    if not org_id:
        print(f"\nERROR: Organization '{ORG_NAME}' not found.")
        print("\nAvailable organizations:")
        for org in organizations:
            print(f"  - {org['name']} (ID: {org['id']})")
        exit(1)
    
    # Step 3: Get all networks for the organization
    print(f"\nFetching networks for organization '{ORG_NAME}'...")
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    
    if not networks:
        print(f"\nNo networks found in organization '{ORG_NAME}'.")
        exit(0)
    
    # Step 4: Display networks with their IDs
    print(f"\n{'='*80}")
    print(f"Networks in '{ORG_NAME}':")
    print(f"{'='*80}")
    print(f"{'Network Name':<40} {'Network ID':<20} {'Type':<15}")
    print(f"{'-'*80}")
    
    for network in networks:
        network_name = network.get('name', 'N/A')
        network_id = network.get('id', 'N/A')
        network_type = network.get('type', 'N/A')
        print(f"{network_name:<40} {network_id:<20} {network_type:<15}")
    
    print(f"{'='*80}")
    print(f"\nTotal networks: {len(networks)}")
    print("\nCopy the Network ID you need and add it to your .env file as 'networkId'")

except meraki.APIError as e:
    print(f"\nERROR: Meraki API Error - {e.message}")
    if hasattr(e, 'status') and e.status == 401:
        print("  This usually means your API key is invalid or expired.")
    exit(1)
except Exception as e:
    print(f"\nERROR: {str(e)}")
    exit(1)
