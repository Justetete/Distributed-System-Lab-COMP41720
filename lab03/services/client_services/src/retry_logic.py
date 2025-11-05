"""
Retry Logic Module with Exponential Backoff and Jitter

This module provides retry capabilities for handling transient failures
in distributed systems using the tenacity library.

Key Features:
- Exponential backoff: Wait time doubles with each retry
- Jitter: Random variation to prevent thundering herd
- Configurable retry conditions
- Detailed logging

Usage:
    from retry_logic import retry_on_transient_error
    
    @retry_on_transient_error()
    def my_api_call():
        return requests.get(...)
"""

import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
    RetryError
)
import requests
from typing import Callable, Any


# Configure logging
logger = logging.getLogger(__name__)


class RetryConfig:
    """
    Configuration class for retry behavior
    
    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3)
        min_wait: Minimum wait time in seconds (default: 1)
        max_wait: Maximum wait time in seconds (default: 10)
        multiplier: Exponential backoff multiplier (default: 2)
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 10.0,
        multiplier: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.multiplier = multiplier
    
    def __repr__(self):
        return (
            f"RetryConfig(max_attempts={self.max_attempts}, "
            f"min_wait={self.min_wait}s, max_wait={self.max_wait}s, "
            f"multiplier={self.multiplier})"
        )


# Default retry configuration
default_config = RetryConfig(
    max_attempts=3,
    min_wait=1.0,
    max_wait=10.0,
    multiplier=2.0
)


def is_transient_error(exception: Exception) -> bool:
    """
    Determine if an exception represents a transient error worth retrying
    
    Transient errors include:
    - Connection errors (network issues)
    - Timeout errors  
    - HTTP 429 (Too Many Requests)
    - HTTP 503 (Service Unavailable)
    - HTTP 504 (Gateway Timeout)
    
    Non-transient errors (should NOT retry):
    - HTTP 400 (Bad Request)
    - HTTP 401 (Unauthorized)
    - HTTP 403 (Forbidden)
    - HTTP 404 (Not Found)
    
    Args:
        exception: The exception to evaluate
    
    Returns:
        bool: True if the error is transient and should be retried
    """
    # Connection and timeout errors are transient
    if isinstance(exception, (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout
    )):
        logger.warning(f"Transient error detected: {type(exception).__name__}")
        return True
    
    # Check HTTP status codes for transient errors
    if isinstance(exception, requests.exceptions.HTTPError):
        status_code = exception.response.status_code if exception.response else None
        
        # Transient HTTP status codes
        transient_codes = [429, 503, 504]
        
        if status_code in transient_codes:
            logger.warning(f"Transient HTTP error detected: {status_code}")
            return True
        
        # Non-transient HTTP status codes
        non_transient_codes = [400, 401, 403, 404]
        
        if status_code in non_transient_codes:
            logger.info(f"Non-transient HTTP error: {status_code} - Not retrying")
            return False
    
    # Default: don't retry unknown exceptions
    return False


def retry_if_exception(predicate: Callable[[Exception], bool]):
    """
    Helper function to create a retry condition based on exception predicate
    
    Args:
        predicate: Function that takes an exception and returns True if should retry
    
    Returns:
        Retry condition function
    """
    def check_exception(retry_state):
        if retry_state.outcome.failed:
            exception = retry_state.outcome.exception()
            return predicate(exception)
        return False
    
    return check_exception


def retry_on_transient_error(config: RetryConfig = None):
    """
    Decorator factory for retrying operations with exponential backoff and jitter
    
    This decorator will:
    1. Retry on transient errors (connection issues, timeouts, 429, 503, 504)
    2. Use exponential backoff with jitter to prevent thundering herd
    3. Log all retry attempts
    4. Stop after max_attempts
    
    Args:
        config: RetryConfig object (uses default if None)
    
    Returns:
        Decorator function
    
    Example:
        @retry_on_transient_error()
        def fetch_data():
            return requests.get("http://api.example.com/data")
        
        # With custom config
        custom_config = RetryConfig(max_attempts=5, min_wait=2.0)
        @retry_on_transient_error(custom_config)
        def fetch_important_data():
            return requests.get("http://api.example.com/critical")
    """
    if config is None:
        config = default_config
    
    logger.info(f"Retry decorator configured with: {config}")
    
    def decorator(func: Callable) -> Callable:
        @retry(
            # Stop after max_attempts
            stop=stop_after_attempt(config.max_attempts),
            
            # Exponential backoff with jitter
            # Formula: min_wait * (multiplier ^ attempt) + random jitter
            # Example: 1s, 2s, 4s, 8s (with random jitter added)
            wait=wait_exponential(
                multiplier=config.multiplier,
                min=config.min_wait,
                max=config.max_wait
            ),
            
            # Only retry on transient errors
            retry=retry_if_exception(is_transient_error),
            
            # Log before sleeping (before retry)
            before_sleep=before_sleep_log(logger, logging.WARNING),
            
            # Log after successful retry
            after=after_log(logger, logging.INFO),
            
            # Reraise the exception if all retries fail
            reraise=True
        )
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except RetryError as e:
                # All retries exhausted
                logger.error(
                    f"All {config.max_attempts} retry attempts failed for {func.__name__}"
                )
                raise e.last_attempt.exception()
        
        return wrapper
    
    return decorator


# Convenience function for quick retry without decorator
def execute_with_retry(func: Callable, *args, config: RetryConfig = None, **kwargs) -> Any:
    """
    Execute a function with retry logic without using a decorator
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        config: RetryConfig object
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function call
    
    Example:
        result = execute_with_retry(
            requests.get,
            "http://api.example.com/data",
            timeout=5
        )
    """
    decorated_func = retry_on_transient_error(config)(func)
    return decorated_func(*args, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Retry Logic Module")
    print("=" * 50)
    print(f"Default configuration: {default_config}")
    print()
    
    # Test with a mock function
    attempt_count = 0
    
    @retry_on_transient_error()
    def mock_api_call():
        global attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count}")
        
        if attempt_count < 3:
            # Simulate transient error
            raise requests.exceptions.ConnectionError("Simulated connection error")
        
        return {"status": "success", "data": "Hello World"}
    
    try:
        print("Testing retry with simulated failures...")
        result = mock_api_call()
        print(f"Success after {attempt_count} attempts: {result}")
    except Exception as e:
        print(f"Failed after all retries: {e}")