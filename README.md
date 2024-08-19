# Meraki Update L7 Firewall (MX) rules

## Script Forked from:
This script is based off the Meraki API documentation and the Github of Xavier VALETTE (xvalette)
at https://github.com/xaviervalette/meraki-update-l7-firewall-rules.

## What is it?
This script is designed to pull any existing Layer 7 firewall rules and append those rules to new ones provided via JSON file, then push all those rules back to the firewall.

Example of python script to update the L7 firewall rules of a Meraki MX as follow :

<img width="1035" alt="image" src="https://user-images.githubusercontent.com/28600326/225572877-8f3d26bc-fc8b-4a5f-b449-207677317f8e.png">

## Source API
All the api calls were created using the Meraki API V1 Index at https://developer.cisco.com/meraki/api-v1/api-index/

## Prerequisites
- Meraki Dashboard access
- Meraki API key
- Meraki network ID

## Get started
1. Clone or download this repo
```console
git clone https://github.com/deawar/MerakiLayer7Rules
```
2. Install required packages
```console
python3 -m pip install -r requirements.txt
```
3. Rename sample_config.env and edit ```.env``` file as follow:
```diff
└── meraki-update-l7-firewall-rules/
+   ├── .env
    ├── requirements.txt
    └── src/
         └── main.py  
```
4. In the ```.env``` file, add the following variables:
```environment
#.env
---
apiKey = "<yourApiKey>"
networkId = "<yourNetworkId>"
...

```

5. Now you can run the code by using the following command:
```console
python3 src/main.py
```

## Output
The output should be as followed:
```console
Resulting ruleset:
{'rules': [{'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/101', 'name': 'CBS Sports'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/40', 'name': 'ESPN'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/96', 'name': 'foxsports.com'}}]}
```

## Author and Contributors
This script was written by Dean Warren with extensive help from 
- Jacob Warren
- Jared Haviland
- Patrick Kelley



