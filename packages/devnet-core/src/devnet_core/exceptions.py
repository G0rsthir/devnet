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
