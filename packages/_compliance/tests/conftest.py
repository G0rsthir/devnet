import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def netbox_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETBOX_TOKEN", "test")
