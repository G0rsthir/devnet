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
