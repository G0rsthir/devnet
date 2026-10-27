# Architecture

How a change in NetBox reaches the systems devnet keeps in sync with it

## Components

```mermaid
---
config:
  flowchart:
    wrappingWidth: 320
---
flowchart TB
    rule["NetBox Event Rule<br/>created / updated / deleted"]

    subgraph api["devnet-api"]
        verify["Check Authentication: JWT Header"]
        dispatch["Start one run per system"]
    end

    subgraph prefect["Prefect server · prefect.yaml"]
        deploy_change["sync-#lt;system#gt;/on-change<br/>limit 1, ENQUEUE"]
        deploy_nightly["reconcile-#lt;system#gt;/schedule"]
    end

    subgraph worker["Process worker · devnet-automation container"]
        system_flow["flows/#lt;system#gt;.py<br/>retries, logs"]
    end

    subgraph packages["packages · business logic"]
        system_pkg["#lt;system#gt;<br/>plan, apply"]
        core["devnet-core<br/>shared code"]
        system_pkg --> core
    end

    subgraph external["External APIs"]
        system_api[("#lt;system#gt; API")]
    end

    rule -->|webhook| verify
    verify --> dispatch
    dispatch -->|arun_deployment| deploy_change
    deploy_change --> system_flow
    deploy_nightly --> system_flow
    system_flow -->|execute| system_pkg
    system_pkg -->|create, update, delete| system_api
```

## Regenerate NetBox API types

```bash
# Regenerate NetBox API types after a NetBox upgrade (dev NetBox running)
cd packages/system-netbox
curl -fsS 'http://127.0.0.1:8080/api/schema/?format=yaml' -o schema/netbox.yaml
uv run datamodel-codegen
```
