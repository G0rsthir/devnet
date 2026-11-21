# 0002. DiffSync For Reconciliation

- Status: Accepted
- Date: 2026-11-19

devnet uses [DiffSync](https://github.com/networktocode/diffsync) to compare two systems and to apply the difference.

Applies the diff with its own async code: `apply_diff()` in `devnet_core.sync`.

## Why

- It is the common library for this job in network automation. Nautobot SSoT and network-importer use it
- The DiffSync sync is blocking code
