# Architecture

## System Overview

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

## Components

| Part                    | Responsible for                                                                                                                     | Not responsible for                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| NetBox                  | Source of truth. An Event Rule sends a webhook when a something is created, updated or deleted                                      | Deciding which devices belong in which system               |
| devnet-api              | Checks `Authorization` header, starts one run per system, returns 202 with the run IDs                                              | Calling a system's API, business rules, waiting for results |
| Prefect server + worker | Queueing (one sync per system at a time), retries, logs, run history, nightly reconcile                                             | Business rules                                              |
| `packages/<system>/`    | Which devices belong in the system, mapping NetBox fields to the system's, comparing, create/update/delete through the system's API | Webhooks, scheduling                                        |
| `packages/devnet-core`  | Settings base, shared logic                                                                                                         | Anything specific to one system                             |

## Design Principles

- **When devnet creates a device in a system, it stores the NetBox device ID on it**, so the sync can still find it after the device is deleted from NetBox
- **Each service provisions what it depends on**: devnet-flows its Prefect concurrency limits, devnet-api the NetBox webhook and event rule that call it
