"""Custom exception hierarchy for Salty Pickle."""


class SaltyPickleError(Exception):
    """Base exception for all Salty Pickle errors."""

    pass


class ResourceNotFoundError(SaltyPickleError):
    """Raised when a requested resource is not found."""

    pass


class IntegrationError(SaltyPickleError):
    """Raised when an external integration fails."""

    pass


class ValidationError(SaltyPickleError):
    """Raised when input validation fails."""

    pass
