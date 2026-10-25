# Architecture

How a change in NetBox reaches the systems devnet keeps in sync with it.

## Components

```mermaid
---
config:
  flowchart:
    wrappingWidth: 320
---
flowchart TB
    rule["NetBox Event Rule<br/>device created / updated / deleted"]

    subgraph api["devnet-api"]
        verify["Check X-Hook-Signature"]
        dispatch["Start one run per system<br/>DEVICE_SYNCS"]
    end

    subgraph prefect["Prefect server · prefect.yaml"]
        deploy_change["sync-#lt;system#gt;-device/on-change<br/>limit 1, ENQUEUE"]
        deploy_nightly["reconcile-#lt;system#gt;/nightly"]
    end

    subgraph worker["Process worker · devnet-automation container"]
        system_flow["flows/#lt;system#gt;.py<br/>retries, logs"]
    end

    subgraph packages["packages · business logic"]
        system_pkg["#lt;system#gt;<br/>in_scope, to_#lt;system#gt;<br/>plan, apply"]
        core["devnet-core<br/>settings, NetBox client"]
    end

    subgraph external["External APIs"]
        nb_api[("NetBox API")]
        system_api[("#lt;system#gt; API")]
    end

    rule -->|webhook| verify
    verify --> dispatch
    dispatch -->|arun_deployment| deploy_change
    deploy_change --> system_flow
    deploy_nightly --> system_flow
    system_flow -->|sync_device| system_pkg
    system_pkg --> core
    core -->|read device| nb_api
    system_pkg -->|create, update, delete| system_api
```

| Part                    | Responsible for                                                                                                                     | Not responsible for                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| NetBox                  | Source of truth. An Event Rule sends a webhook when a device is created, updated or deleted                                         | Deciding which devices belong in which system               |
| devnet-api              | Checks `X-Hook-Signature`, starts one run per system in `DEVICE_SYNCS`, returns 202 with the run IDs                                | Calling a system's API, business rules, waiting for results |
| Prefect server + worker | Queueing (one sync per system at a time), retries, logs, run history, nightly reconcile                                             | Business rules                                              |
| `packages/<system>/`    | Which devices belong in the system, mapping NetBox fields to the system's, comparing, create/update/delete through the system's API | Webhooks, scheduling                                        |
| `devnet-core`           | Settings base, NetBox client, shared errors                                                                                         | Anything specific to one system                             |

- **Redelivered webhooks don't start new runs.** The idempotency key is built from NetBox's `request_id`,
- **When devnet creates a device in a system, it stores the NetBox device ID on it**, so the sync can still find it after the device is deleted from NetBox.
