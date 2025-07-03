"""Custom exception classes for AI Tester."""


class AITesterError(Exception):
    """Base exception class for AI Tester."""
    pass


class ValidationError(AITesterError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(AITesterError):
    """Raised when configuration is invalid or missing."""
    pass


class QuestionSourceError(AITesterError):
    """Raised when question source operations fail."""
    pass


class OutputDestinationError(AITesterError):
    """Raised when output destination operations fail."""
    pass


class ProcessingError(AITesterError):
    """Raised when question processing fails."""
    pass


class NetworkError(AITesterError):
    """Raised when network operations fail."""
    pass


class RetryExhaustedError(AITesterError):
    """Raised when retry attempts are exhausted."""
    
    def __init__(self, message: str, attempts: int, last_error: Exception = None):
        """Initialize with retry information."""
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error