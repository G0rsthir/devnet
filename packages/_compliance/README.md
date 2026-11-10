# Compliance

Prototype of the compliance framework. Design and next steps: [docs/plans/compliance-framework.md](../../docs/plans/compliance-framework.md)

- `compliance.core`: the engine. It knows no system and no driver
- `compliance.device`: the `DeviceCli` port for show commands, and the pyATS adapter
- `compliance.cisco`: running config of a Cisco device, from the device or from a file
- `compliance.netbox`: NetBox data of a device
- `compliance.intent`: rules that compare the config with NetBox
- `compliance.config`: the rules in the config file

```bash
uv run --package compliance pytest packages/_compliance/tests
```

The tests connect to no device and to no NetBox. Start with [tests/test_engine.py](tests/test_engine.py).

pyATS is not a dependency of the workspace, so the tests that open a pyATS session are skipped. To run them, use an environment with `pyats`, `unicon` and `genie`. They use the mock device of unicon.
