"""
Standardized error handling utilities for Kontali ERP.

Following ERROR_HANDLING_SPEC.md - all errors follow consistent format:
{
    "error": {
        "code": "SPECIFIC_ERROR_CODE",
        "message": "Human-readable Norwegian message",
        "details": {...},
        "request_id": "uuid",
        "timestamp": "ISO8601"
    }
}
"""
from typing import Any, Dict, Optional
from datetime import datetime
import uuid
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class KontaliError(Exception):
    """Base exception for all Kontali errors."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to standardized error response format."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    
    def to_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse."""
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict()
        )


# AI-related errors
class AIServiceError(KontaliError):
    """AI service (Claude, GPT, etc.) failed."""
    
    def __init__(self, message: str = "AI-tjenesten svarte ikke", details: Optional[Dict] = None):
        super().__init__(
            code="AI_SERVICE_ERROR",
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class AITimeoutError(KontaliError):
    """AI request timed out."""
    
    def __init__(self, timeout_seconds: int = 30, details: Optional[Dict] = None):
        super().__init__(
            code="AI_TIMEOUT",
            message=f"AI-forespørselen tok for lang tid (>{timeout_seconds}s)",
            details=details or {"timeout_seconds": timeout_seconds},
            status_code=status.HTTP_504_GATEWAY_TIMEOUT
        )


class AIConfidenceLowError(KontaliError):
    """AI confidence below threshold - not an error, but triggers manual review."""
    
    def __init__(self, confidence: float, threshold: float, details: Optional[Dict] = None):
        super().__init__(
            code="AI_CONFIDENCE_LOW",
            message=f"AI-konfidensen ({confidence:.1%}) er under terskel ({threshold:.1%})",
            details=details or {"confidence": confidence, "threshold": threshold},
            status_code=status.HTTP_200_OK  # Not an error - triggers queue
        )


# Validation errors
class ValidationError(KontaliError):
    """Input validation failed."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            details=error_details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# Database errors
class DatabaseError(KontaliError):
    """Database operation failed."""
    
    def __init__(self, message: str = "Database-feil oppstod", details: Optional[Dict] = None):
        super().__init__(
            code="DATABASE_ERROR",
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Business logic errors
class DuplicateEntryError(KontaliError):
    """Attempting to create duplicate entry."""
    
    def __init__(self, entity: str, identifier: str, details: Optional[Dict] = None):
        super().__init__(
            code="DUPLICATE_ENTRY",
            message=f"{entity} med ID '{identifier}' finnes allerede",
            details=details or {"entity": entity, "identifier": identifier},
            status_code=status.HTTP_409_CONFLICT
        )


class NotFoundError(KontaliError):
    """Requested resource not found."""
    
    def __init__(self, entity: str, identifier: str, details: Optional[Dict] = None):
        super().__init__(
            code="NOT_FOUND",
            message=f"{entity} med ID '{identifier}' ble ikke funnet",
            details=details or {"entity": entity, "identifier": identifier},
            status_code=status.HTTP_404_NOT_FOUND
        )


# Authentication/Authorization errors
class UnauthorizedError(KontaliError):
    """User not authenticated."""
    
    def __init__(self, message: str = "Autentisering påkrevd", details: Optional[Dict] = None):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenError(KontaliError):
    """User not authorized for this action."""
    
    def __init__(self, message: str = "Ingen tilgang til denne ressursen", details: Optional[Dict] = None):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


# Helper functions
def handle_exception(exc: Exception) -> JSONResponse:
    """
    Convert any exception to standardized error response.
    
    Usage in FastAPI endpoints:
    try:
        # ... your code
    except Exception as e:
        return handle_exception(e)
    """
    if isinstance(exc, KontaliError):
        return exc.to_response()
    
    # Unknown error - log and return generic 500
    import traceback
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())
    
    generic_error = KontaliError(
        code="INTERNAL_ERROR",
        message="En uventet feil oppstod. Kontakt support hvis problemet vedvarer.",
        details={"exception_type": type(exc).__name__},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return generic_error.to_response()
