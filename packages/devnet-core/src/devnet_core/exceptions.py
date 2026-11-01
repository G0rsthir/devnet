class DomainError(Exception):
    """
    Base class for all domain-level errors
    """

    code = "domain_error"


class InfrastructureError(Exception):
    """
    Base class for internal/system errors
    """

    code = "infrastructure_error"


class DataIntegrityError(InfrastructureError):
    code = "data_integrity_error"


class UnsupportedOperationError(InfrastructureError):
    code = "unsupported_operation"


class ResourceLimitExceededError(InfrastructureError):
    code = "resource_limit_exceeded"


class ConfigurationError(InfrastructureError):
    code = "configuration_error"


class SystemConnectionError(DomainError):
    """
    An external system is unreachable, rejected the request or returned an unexpected response

    Args:
        status_code: The system's answer, if it rejected the request
    """

    code = "system_connection_error"

    def __init__(self, name: str, msg: str, *, status_code: int | None = None):
        self.name = name
        self.msg = msg
        self.status_code = status_code
        super().__init__(f"{name}: {msg}")
