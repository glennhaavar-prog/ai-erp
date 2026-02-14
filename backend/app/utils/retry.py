"""
Retry logic with exponential backoff for AI calls and external services.

Following ERROR_HANDLING_SPEC.md:
- AI calls: 3 retries, exponential backoff (1s, 2s, 4s)
- Transient errors only (timeout, 503, 429)
- Permanent errors fail immediately
"""
import time
import asyncio
from typing import Callable, Any, TypeVar, Optional
from functools import wraps
import logging

from app.utils.errors import AIServiceError, AITimeoutError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (AIServiceError, AITimeoutError, ConnectionError)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt (0-indexed)."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


# Default configs for different service types
AI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    exponential_base=2.0,  # 1s, 2s, 4s
    retryable_exceptions=(AIServiceError, AITimeoutError, ConnectionError, TimeoutError)
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=0.5,
    exponential_base=2.0,  # 0.5s, 1s
    retryable_exceptions=(ConnectionError,)
)


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying functions with exponential backoff.
    
    Usage:
        @retry_with_backoff(AI_RETRY_CONFIG)
        def call_ai_service(prompt: str) -> str:
            # ... code that might fail
            return response
    
        @retry_with_backoff()  # Uses default config
        async def async_ai_call(prompt: str) -> str:
            # ... async code
            return response
    """
    if config is None:
        config = AI_RETRY_CONFIG
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                last_exception = None
                
                for attempt in range(config.max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    
                    except config.retryable_exceptions as e:
                        last_exception = e
                        
                        if attempt < config.max_attempts - 1:  # Not last attempt
                            delay = config.get_delay(attempt)
                            logger.warning(
                                f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                                f"Retrying in {delay}s..."
                            )
                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                f"All {config.max_attempts} attempts failed for {func.__name__}"
                            )
                    
                    except Exception as e:
                        # Non-retryable error - fail immediately
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                
                # All retries exhausted
                if last_exception:
                    raise last_exception
                else:
                    raise RuntimeError("Retry logic failed without exception")
            
            return async_wrapper
        
        else:  # Sync function
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                last_exception = None
                
                for attempt in range(config.max_attempts):
                    try:
                        return func(*args, **kwargs)
                    
                    except config.retryable_exceptions as e:
                        last_exception = e
                        
                        if attempt < config.max_attempts - 1:
                            delay = config.get_delay(attempt)
                            logger.warning(
                                f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                                f"Retrying in {delay}s..."
                            )
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"All {config.max_attempts} attempts failed for {func.__name__}"
                            )
                    
                    except Exception as e:
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                
                if last_exception:
                    raise last_exception
                else:
                    raise RuntimeError("Retry logic failed without exception")
            
            return sync_wrapper
    
    return decorator


async def retry_async(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Standalone async retry function (alternative to decorator).
    
    Usage:
        result = await retry_async(
            call_claude_api,
            prompt="Analyze this invoice",
            config=AI_RETRY_CONFIG
        )
    """
    if config is None:
        config = AI_RETRY_CONFIG
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed"
                )
        
        except Exception as e:
            logger.error(f"Non-retryable error: {e}")
            raise
    
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError("Retry logic failed")


def retry_sync(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Standalone sync retry function.
    
    Usage:
        result = retry_sync(
            parse_invoice,
            file_path="/path/to/invoice.pdf",
            config=RetryConfig(max_attempts=2)
        )
    """
    if config is None:
        config = AI_RETRY_CONFIG
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)
        
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed"
                )
        
        except Exception as e:
            logger.error(f"Non-retryable error: {e}")
            raise
    
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError("Retry logic failed")
