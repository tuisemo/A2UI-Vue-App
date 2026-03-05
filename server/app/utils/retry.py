"""
Retry Utility - Exponential backoff retry decorator for async operations
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts fail"""
    def __init__(self, message: str, last_error: Exception, attempts: int):
        self.message = message
        self.last_error = last_error
        self.attempts = attempts
        super().__init__(message)


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None
):
    """
    Decorator for async functions with exponential backoff retry
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 30.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to delay (default: True)
        retryable_exceptions: Tuple of exception types to retry (default: all Exception)
    """
    if retryable_exceptions is None:
        retryable_exceptions = (Exception,)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"Attempt {attempt}/{max_attempts} for {func.__name__}")
                    return await func(*args, **kwargs)
                
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {str(e)}",
                            last_error=e,
                            attempts=max_attempts
                        )
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    if jitter:
                        import random
                        delay += random.uniform(0, 0.1 * delay)
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here
            raise RetryError(
                f"Unexpected retry loop exit for {func.__name__}",
                last_error=last_exception,
                attempts=max_attempts
            )
        
        return wrapper
    return decorator


# Predefined exception tuples for common use cases
LLM_RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
)

NETWORK_RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
    OSError,
)
