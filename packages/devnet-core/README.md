# Core

Shared code used by every other package

- `devnet_core.sync`: the sync framework, a thin layer over [DiffSync](https://github.com/networktocode/diffsync). See [docs/plans/ingest-framework.md](../../docs/plans/ingest-framework.md)

```bash
uv run pytest packages/devnet-core/tests
```
