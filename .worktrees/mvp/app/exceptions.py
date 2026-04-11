class SaltyPickleError(Exception):
    def __init__(self, message: str = "An error occurred", details=None):
        self.message = message
        self.details = details
        super().__init__(message)


class ResourceNotFoundError(SaltyPickleError):
    def __init__(self, message: str = "Resource not found", details=None):
        super().__init__(message, details)


class IntegrationError(SaltyPickleError):
    def __init__(self, message: str = "Integration error", details=None):
        super().__init__(message, details)


class ValidationError(SaltyPickleError):
    def __init__(self, message: str = "Validation error", details=None):
        super().__init__(message, details)
