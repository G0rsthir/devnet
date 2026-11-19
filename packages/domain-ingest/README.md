# Ingest

Features that make a system match another one. Design and next steps: [docs/plans/ingest-framework.md](../../docs/plans/ingest-framework.md)

- `ingest.device`: serial, interfaces, IP addresses and MAC addresses of a network device -> NetBox

The features are built on `devnet_core.sync`, a thin layer over [DiffSync](https://github.com/networktocode/diffsync).

```bash
uv run pytest packages/ingest/tests
```

The tests use a NetBox in memory. Nothing connects to a real NetBox or to a device.
