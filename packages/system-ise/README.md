# Cisco Identity Services Engine (ISE) integration

## Design

Official ISE API documentation: <https://developer.cisco.com/docs/identity-services-engine/latest/cisco-ise-api-framework/>

## ISE Configuration

Enable ERS API on ISE

- Admin > System > Settings > ERS Settings > Enable ERS API

```bash
# TODO
# Create a new ERS API user with the following permissions:
# - Read/Write: Network Access > Network Devices
# - Read/Write: Network Access > Network Device Groups
# - Read/Write: Location > Locations
## ada

```

## Regenerate ISE API types

```bash
# Regenerate ISE API types after an ISE upgrade (dev ISE running)
# -k: the ISE certificate is self-signed. curl prompts for the password
cd packages/system-ise
curl -fsSk -u <user> 'https://192.168.101.241/ers/pages/ERS_V1.json' -o schema/ise.json
uv run datamodel-codegen
```
