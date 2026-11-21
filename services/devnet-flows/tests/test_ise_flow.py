"""
The wiring of the ISE flow: feature flag, task, retries. The job is fake: domain-ingest tests the sync itself
"""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from prefect.testing.utilities import prefect_test_harness

import domain_ingest.ise
from devnet_core.exceptions import SystemConnectionError
from devnet_core.sync import SyncReport
from devnet_flows import systems
from devnet_flows.flows import ise as flows
from devnet_flows.tasks.ise import sync_device_to_ise

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="module", autouse=True)
def prefect_server() -> Iterator[None]:
    with prefect_test_harness():
        yield


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeClient:
    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None


class FakeJob:
    def __init__(self) -> None:
        self.calls: list[tuple[int, bool]] = []
        # Raised by the next calls, one for each call
        self.errors: list[Exception] = []

    async def __call__(self, netbox: object, ise: object, *, device_id: int, dry_run: bool) -> SyncReport:
        self.calls.append((device_id, dry_run))
        if self.errors:
            raise self.errors.pop(0)
        return SyncReport(source=f"netbox device {device_id}", target="ise", dry_run=dry_run)


def config(*, ise_sync: bool) -> SimpleNamespace:
    return SimpleNamespace(features=SimpleNamespace(ise_sync=ise_sync))


@pytest.fixture
def job(monkeypatch: pytest.MonkeyPatch) -> FakeJob:
    fake = FakeJob()
    monkeypatch.setattr(domain_ingest.ise, "sync_device", fake)
    monkeypatch.setattr(systems, "netbox", FakeClient)
    monkeypatch.setattr(systems, "ise", FakeClient)
    monkeypatch.setattr(flows, "get_config", lambda: config(ise_sync=True))
    # No wait before the retry
    monkeypatch.setattr(flows, "sync_device_to_ise", sync_device_to_ise.with_options(retry_delay_seconds=0))
    return fake


async def test_a_run_from_the_ui_is_a_dry_run(job: FakeJob) -> None:
    report = await flows.sync_ise_device(device_id=5)

    assert job.calls == [(5, True)]
    assert report.dry_run


async def test_feature_off_ends_the_run_before_the_task(job: FakeJob, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(flows, "get_config", lambda: config(ise_sync=False))

    state = await flows.sync_ise_device(device_id=5, return_state=True)

    assert state.is_completed()
    assert state.message == "features.ise_sync is off"
    assert job.calls == []


async def test_an_error_that_cannot_pass_fails_the_run(job: FakeJob) -> None:
    job.errors = [SystemConnectionError("ise", "400 Bad Request", status_code=400)]

    state = await flows.sync_ise_device(device_id=5, dry_run=False, return_state=True)

    assert state.is_failed()
    assert job.calls == [(5, False)]
