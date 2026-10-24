```
packages/ise/src/ise/
├── settings.py   # IseEnvSettings(BaseEnvSettings): ISE_URL, ISE_USERNAME, ISE_PASSWORD
├── client.py     # ISE API calls only: auth, paging, errors
├── mapping.py    # in_scope(), to_ise(): which devices go to ISE; site → location group, role → device type
└── sync.py       # sync_device(): read both sides, plan the change, apply it
```

```
# packages/ise/src/ise/sync.py
def sync_device(device_id: int, *, dry_run: bool = False) -> Change:
    device = netbox.get_device(device_id)                    # None once deleted in NetBox
    desired = to_ise(device) if device and in_scope(device) else None
    actual = client.find_device(netbox_id=device_id)
    change = plan(desired, actual)                           # create | update | delete | none
    if not dry_run:
        apply(change)
    return change
```
