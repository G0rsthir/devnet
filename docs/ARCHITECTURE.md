# Architecture

How a change in NetBox reaches Cisco ISE and Prime Infrastructure.

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

    subgraph prefect["Prefect server · flows/prefect.yaml"]
        ise_on_change["sync-ise-device/on-change<br/>limit 1, ENQUEUE"]
        ise_nightly["reconcile-ise/nightly"]
        prime_on_change["sync-prime-device/on-change<br/>limit 1, ENQUEUE"]
        prime_nightly["reconcile-prime/nightly"]
    end

    subgraph worker["Process worker · devnet-automation container"]
        ise_flow["flows/ise.py<br/>retries, logs"]
        prime_flow["flows/prime.py<br/>retries, logs"]
    end

    subgraph packages["packages · business logic"]
        ise_pkg["ise<br/>in_scope, to_ise, plan, apply"]
        prime_pkg["prime<br/>in_scope, to_prime, plan, apply"]
        core["devnet-core<br/>settings, NetBox client"]
    end

    subgraph external["External APIs"]
        nb_api[("NetBox API")]
        ise_system[("Cisco ISE")]
        prime_system[("Prime Infrastructure")]
    end

    rule -->|webhook| verify
    verify --> dispatch
    dispatch -->|arun_deployment| ise_on_change
    dispatch -->|arun_deployment| prime_on_change
    ise_on_change --> ise_flow
    ise_nightly --> ise_flow
    prime_on_change --> prime_flow
    prime_nightly --> prime_flow
    ise_flow -->|sync_device| ise_pkg
    prime_flow -->|sync_device| prime_pkg
    ise_pkg --> core
    prime_pkg --> core
    core -->|read device| nb_api
    ise_pkg -->|create, update, delete| ise_system
    prime_pkg -->|create, update, delete| prime_system
```

| Part | Responsible for | Not responsible for |
| --- | --- | --- |
| NetBox | Source of truth. An Event Rule sends a webhook when a device is created, updated or deleted | Deciding which devices belong in ISE or Prime |
| devnet-api | Checks `X-Hook-Signature`, starts one run per system in `DEVICE_SYNCS`, returns 202 with the run IDs | Calling ISE or Prime, business rules, waiting for results |
| Prefect server + worker | Queueing (one sync per system at a time), retries, logs, run history, nightly reconcile | Business rules |
| [flows/](../flows/) | Calling the package's `sync_device()` and logging what changed | Mapping or comparing |
| `ise` and `prime` packages | Which devices belong in the system, mapping NetBox fields to the system's, comparing, create/update/delete through the system's API | Webhooks, scheduling |
| `devnet-core` | Settings base, NetBox client, shared errors | Anything specific to one system |

## When a device changes

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant NB as NetBox
    participant API as devnet-api
    participant PF as Prefect server
    participant W as Worker · flows/ise.py + ise package
    participant ISE as Cisco ISE

    User->>NB: Create, edit or delete a device
    NB->>API: POST /api/v1/webhooks/netbox/device<br/>with X-Hook-Signature
    API->>API: Check the signature, 401 if wrong
    API->>PF: arun_deployment sync-ise-device/on-change
    API->>PF: arun_deployment sync-prime-device/on-change
    Note over API,PF: idempotency_key = request_id, device_id, deployment
    PF-->>API: Two scheduled flow runs
    API-->>NB: 202 with the flow run IDs
    W->>PF: Poll the work pool
    PF-->>W: sync-ise-device with device_id
    W->>NB: Read the device, missing means deleted
    W->>ISE: Find the device by its NetBox ID
    W->>W: plan(desired, actual)
    W->>ISE: Create, update or delete, only if needed
    W-->>PF: Completed, the change is in the run logs
    Note over PF,ISE: The Prime run does the same against Prime Infrastructure
```

- **Redelivered webhooks don't start new runs.** The idempotency key is built from NetBox's `request_id`, the device ID and the deployment name, so the same webhook maps to the same runs. The device ID is part of the key because a bulk edit sends one webhook per device, all with the same `request_id`.
- **If Prefect can't be reached, the request fails with a 500**, so NetBox records a failed delivery instead of a 202 with no run behind it.

## How a sync decides what to do

```mermaid
flowchart TD
    start(["sync_device(device_id)"]) --> read["Read the device from NetBox"]
    read --> scope{"Exists and<br/>in_scope()?"}
    scope -->|yes| want["desired = to_ise(device)"]
    scope -->|no| want_none["desired = nothing"]
    want --> find["actual = the ISE device with this NetBox ID"]
    want_none --> find
    find --> plan{"plan(desired, actual)"}
    plan -->|desired only| create["Create in ISE"]
    plan -->|both, different| update["Update in ISE"]
    plan -->|actual only| delete["Delete from ISE"]
    plan -->|equal, or neither| skip["Do nothing"]
```

- **The sync ignores the webhook's created/updated/deleted.** It compares NetBox with ISE every time, so a retry is safe and the order webhooks arrive in doesn't matter.
- **`reconcile-ise` runs the same `sync_device()` every night**, for every NetBox device and every ISE device that devnet manages. It repairs webhooks that were lost (NetBox doesn't resend a failed one unless `RQ_RETRY_MAX` is set) and manual changes made in ISE.
- **Which devices belong in ISE is decided by `in_scope()`, not by Event Rule conditions.** Conditions are checked against the device after the change, so a condition like "has tag ise" never fires for the edit that removes the tag, and the device would stay in ISE.
- **The NetBox device ID is stored on the ISE object when it's created**, so the sync can still find it after the device is deleted from NetBox.

## Adding another system

1. Create `packages/<system>/` with `settings.py`, `client.py`, `mapping.py` (`in_scope`, `to_<system>`) and `sync.py` (`sync_device`, `devices_to_check`).
2. Add `flows/<system>.py` with a `sync_<system>_device` flow and a `reconcile_<system>` flow.
3. Add two deployments to [flows/prefect.yaml](../flows/prefect.yaml): `on-change` with limit 1 and `ENQUEUE`, and `nightly` with a schedule.
4. Add `sync-<system>-device/on-change` to `DEVICE_SYNCS` in [routes/netbox.py](../services/devnet-api/src/devnet_api/routes/netbox.py).
