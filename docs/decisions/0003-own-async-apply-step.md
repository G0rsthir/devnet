# 0003. Own Async Apply Step

- Status: Accepted
- Date: 2026-11-19

devnet uses DiffSync for the models and the diff, and applies the diff with its own async code: `apply_diff()` in `devnet_core.sync`. This replaces the DiffSync sync in a worker thread of [0002](0002-diffsync-for-reconciliation.md)

## Why

- The DiffSync sync is blocking code. It calls `create`, `update` and `delete` without `await`. DiffSync has no async support, and no issue or pull request upstream asks for it
- The worker thread needed a bridge for each write (`anyio.from_thread.run`) and a flag to stop a thread that is still alive after a cancel
- devnet uses few rules of the DiffSync sync: the order of the diff, children after their parent, `NATURAL_DELETION_ORDER`, and the children of a failed object are skipped. `apply_diff()` has them in 90 lines. The device import tests check them

## Consequences

- devnet maintains the apply rules. A new sync feature of DiffSync, e.g. bulk writes, needs work in `apply_diff()`
- `SKIP_CHILDREN_ON_DELETE` and `sync_complete()` are not supported. No feature uses them
- A cancelled run cancels the write in progress
- `sync_from()` is not used. A `DiffAsyncModel` raises an error if it is called
- Every devnet model is a `DiffAsyncModel`: a contract model subclasses it, and a target model subclasses the contract model. `RemoteModel` is gone

## Alternatives

| Alternative                             | Why not                                                                                      |
| --------------------------------------- | -------------------------------------------------------------------------------------------- |
| DiffSync sync in a worker thread (0002) | A thread, a bridge for each write and a cancel flag, around a loop that only calls the hooks |
| Async support in DiffSync upstream      | Nobody asks for it upstream, and an open pull request (#345) changes the same code           |
