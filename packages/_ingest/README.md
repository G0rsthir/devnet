# Ingest

Prototype of the ingest framework and of the device import. Design and next steps: [docs/plans/ingest-framework.md](../../docs/plans/ingest-framework.md)

- `ingest.sync`: the framework, a thin layer over [DiffSync](https://github.com/networktocode/diffsync)
- `ingest.device`: serial, interfaces, IP addresses and MAC addresses of a network device -> NetBox

```bash
uv run --package ingest pytest packages/_ingest/tests
```

The tests use a NetBox in memory. Nothing connects to a real NetBox or to a device.
