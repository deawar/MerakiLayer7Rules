# Meraki Update L7 Firewall (MX) rules

## What is it ?
Example of python script to update the L7 firewall rules of a Meraki MX as follow :

<img width="1035" alt="image" src="https://user-images.githubusercontent.com/28600326/225572877-8f3d26bc-fc8b-4a5f-b449-207677317f8e.png">

## Prerequisites
- Meraki Dashboard access
- Meraki API key
- Meraki network ID

## Get started
1. Clone or download this repo
```console
git clone https://github.com/xaviervalette/meraki-update-l7-firewall-rules
```
2. Install required packages
```console
python3 -m pip install -r requirements.txt
```
3. Add a ```config.yml``` file as follow:
```diff
└── meraki-update-l7-firewall-rules/
+   ├── config.yml
    ├── requirements.txt
    └── src/
         └── main.py  
```
4. In the ```config.yml``` file, add the following variables:
```yaml
#config.yml
---
apiKey: "<yourApiKey>"
networkId: "<yourNetworkId1>"
...

```

5. Now you can run the code by using the following command:
```console
python3 src/main.py
```

## Output
The output should be as followed:
```console
Request status code : 200 

{'rules': [{'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/101', 'name': 'CBS Sports'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/40', 'name': 'ESPN'}}, {'policy': 'deny', 'type': 'application', 'value': {'id': 'meraki:layer7/application/96', 'name': 'foxsports.com'}}]}
```




