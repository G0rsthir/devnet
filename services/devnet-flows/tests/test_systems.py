import pytest
from prefect.states import Failed

from devnet_core.exceptions import ConfigurationError, SystemConnectionError
from devnet_flows.systems import transient


@pytest.mark.parametrize(
    ("error", "retry"),
    [
        (SystemConnectionError("ise", "Connection timed out"), True),
        (SystemConnectionError("ise", "429 Too Many Requests", status_code=429), True),
        (SystemConnectionError("ise", "503 Service Unavailable", status_code=503), True),
        (SystemConnectionError("ise", "400 Bad Request", status_code=400), False),
        (ConfigurationError("systems.ise is not configured"), False),
    ],
)
def test_only_an_error_that_can_pass_is_retried(error: Exception, retry: bool) -> None:
    assert transient(None, None, Failed(data=error)) is retry  # type: ignore[arg-type]
