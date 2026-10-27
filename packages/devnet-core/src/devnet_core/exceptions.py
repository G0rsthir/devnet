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
    """

    code = "system_connection_error"

    def __init__(self, name: str, msg: str):
        self.name = name
        self.msg = msg
        super().__init__(f"{name}: {msg}")
