"""
Demo Environment Middleware

Prevents demo data operations in production environment
and ensures demo data isolation.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DemoEnvironmentMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce demo environment restrictions
    
    - Blocks demo API endpoints in production
    - Logs demo operations
    - Ensures demo data isolation
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request through demo environment checks"""
        
        path = request.url.path
        
        # Check if this is a demo endpoint
        if path.startswith("/api/demo/"):
            
            # Block demo endpoints in production unless explicitly enabled
            if settings.ENVIRONMENT == "production" and not settings.DEMO_MODE_ENABLED:
                logger.warning(
                    f"Blocked demo endpoint access in production: {path}",
                    extra={"client_ip": request.client.host if request.client else "unknown"}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Demo endpoints are not available in production environment"
                )
            
            # Log all demo operations
            logger.info(
                f"Demo operation: {request.method} {path}",
                extra={
                    "method": request.method,
                    "path": path,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
        
        # Continue with the request
        response = await call_next(request)
        
        # Add demo environment header to responses
        if settings.DEMO_MODE_ENABLED:
            response.headers["X-Demo-Environment"] = "true"
        
        return response


def is_demo_environment() -> bool:
    """Check if demo mode is enabled"""
    return settings.DEMO_MODE_ENABLED


def require_demo_mode():
    """Dependency to ensure demo mode is enabled"""
    if not is_demo_environment():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires demo mode to be enabled"
        )
