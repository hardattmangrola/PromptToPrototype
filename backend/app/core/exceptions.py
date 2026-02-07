"""
Custom exceptions for the Healthcare RAG backend.
Refusals and safety-related errors are first-class.
"""
from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class UnauthorizedError(AppException):
    """Authentication required or invalid token."""

    def __init__(self, message: str = "Not authenticated", details: Optional[dict] = None):
        super().__init__(message, status_code=401, details=details)


class ForbiddenError(AppException):
    """Insufficient permissions."""

    def __init__(self, message: str = "Forbidden", details: Optional[dict] = None):
        super().__init__(message, status_code=403, details=details)


class RefusalError(AppException):
    """
    System refused to answer (unsafe question, no evidence, or validation failure).
    Used for audit logging and consistent user messaging.
    """

    REFUSAL_MESSAGE = (
        "I cannot answer this question because it requires medical advice or "
        "information not present in the provided documents. "
        "Please consult a qualified healthcare professional."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        msg = message or self.REFUSAL_MESSAGE
        super().__init__(msg, status_code=422, details=details or {"reason": reason})


class ValidationError(AppException):
    """Output or claim validation failed."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=422, details=details)
