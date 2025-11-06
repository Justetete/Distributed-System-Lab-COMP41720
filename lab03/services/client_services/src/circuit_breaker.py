"""
Circuit Breaker Pattern Implementation

This module implements the Circuit Breaker pattern for handling persistent failures
in distributed systems. It prevents cascade failures by "opening" the circuit when
failures exceed a threshold, allowing the backend service to recover.

Circuit Breaker States:
    CLOSED: Normal operation, requests pass through
    OPEN: Failure threshold exceeded, requests fail fast
    HALF_OPEN: Testing if service has recovered

Usage:
    from circuit_breaker import CircuitBreaker
    
    cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    
    @cb.call
    def backend_request():
        return requests.get("http://backend/api")
"""

import time
import logging
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Callable, Any, Optional


# Configure logging
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """
    Circuit Breaker States
    
    CLOSED: Circuit is closed, requests pass through normally
    OPEN: Circuit is open, requests fail fast without calling backend
    HALF_OPEN: Circuit is testing if service has recovered
    """
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """
    Exception raised when circuit breaker is OPEN
    
    This indicates the circuit breaker is preventing calls to the backend
    because failure threshold has been exceeded.
    """
    pass


class CircuitBreakerConfig:
    """
    Configuration for Circuit Breaker
    
    Attributes:
        failure_threshold: Number of failures before opening circuit (default: 5)
        recovery_timeout: Seconds to wait before attempting HALF_OPEN (default: 30)
        success_threshold: Successes needed in HALF_OPEN to close circuit (default: 2)
        expected_exception: Exception type to count as failure (default: Exception)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception
    
    def __repr__(self):
        return (
            f"CircuitBreakerConfig(failure_threshold={self.failure_threshold}, "
            f"recovery_timeout={self.recovery_timeout}s, "
            f"success_threshold={self.success_threshold})"
        )


class CircuitBreaker:
    """
    Circuit Breaker implementation
    
    Protects against cascading failures by tracking failures and opening
    the circuit when failures exceed threshold.
    
    Example:
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        
        @cb.call
        def fetch_data():
            return requests.get("http://backend/api")
        
        try:
            data = fetch_data()
        except CircuitBreakerOpenError:
            # Circuit is open, use fallback
            data = get_cached_data()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
        expected_exception: type = Exception,
        name: str = "default"
    ):
        """
        Initialize Circuit Breaker
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying HALF_OPEN
            success_threshold: Successes needed to close from HALF_OPEN
            expected_exception: Exception type to track
            name: Name for this circuit breaker (for logging)
        """
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            expected_exception=expected_exception
        )
        
        self.name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = Lock()  # Thread-safe state changes
        
        logger.info(
            f"Circuit Breaker '{self.name}' initialized: {self.config}"
        )
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if (self._state == CircuitState.OPEN and 
                self._last_failure_time is not None):
                
                time_since_failure = time.time() - self._last_failure_time
                
                if time_since_failure >= self.config.recovery_timeout:
                    self._transition_to_half_open()
            
            return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count"""
        with self._lock:
            return self._failure_count
    
    @property
    def success_count(self) -> int:
        """Get current success count (in HALF_OPEN state)"""
        with self._lock:
            return self._success_count
    
    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN state"""
        logger.warning(
            f"⚡ Circuit Breaker '{self.name}' transitioning to HALF_OPEN. "
            f"Will attempt test call to check if service recovered."
        )
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        logger.error(
            f"💥 Circuit Breaker '{self.name}' OPENING! "
            f"Failure threshold ({self.config.failure_threshold}) exceeded. "
            f"Will fail fast for next {self.config.recovery_timeout}s."
        )
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        self._failure_count = 0  # Reset for next cycle
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        logger.info(
            f"✅ Circuit Breaker '{self.name}' CLOSING. "
            f"Service appears to be recovered. Resuming normal operation."
        )
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
    
    def _record_success(self):
        """Record a successful call"""
        with self._lock:
            current_state = self._state
            
            if current_state == CircuitState.HALF_OPEN:
                self._success_count += 1
                
                logger.info(
                    f"✓ Circuit Breaker '{self.name}' test call succeeded. "
                    f"Success count: {self._success_count}/{self.config.success_threshold}"
                )
                
                # Check if we should close the circuit
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            
            elif current_state == CircuitState.CLOSED:
                # Reset failure count on success
                if self._failure_count > 0:
                    logger.info(
                        f"Circuit Breaker '{self.name}' call succeeded. "
                        f"Resetting failure count (was {self._failure_count})."
                    )
                    self._failure_count = 0
    
    def _record_failure(self, exception: Exception):
        """Record a failed call"""
        with self._lock:
            current_state = self._state
            
            if current_state == CircuitState.HALF_OPEN:
                # Failed during test - back to OPEN
                logger.warning(
                    f"✗ Circuit Breaker '{self.name}' test call failed. "
                    f"Service not recovered. Re-opening circuit."
                )
                self._transition_to_open()
            
            elif current_state == CircuitState.CLOSED:
                self._failure_count += 1
                self._last_failure_time = time.time()
                
                logger.warning(
                    f"✗ Circuit Breaker '{self.name}' failure recorded. "
                    f"Failure count: {self._failure_count}/{self.config.failure_threshold} "
                    f"(Exception: {type(exception).__name__})"
                )
                
                # Check if we should open the circuit
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
    
    def call(self, func: Callable) -> Callable:
        """
        Decorator to protect a function with circuit breaker
        
        Args:
            func: Function to protect
        
        Returns:
            Protected function
        
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: Original exception from func if circuit is CLOSED/HALF_OPEN
        
        Example:
            @circuit_breaker.call
            def fetch_data():
                return requests.get("http://api/data")
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check current state
            current_state = self.state
            
            if current_state == CircuitState.OPEN:
                # Circuit is open - fail fast
                logger.warning(
                    f"🚫 Circuit Breaker '{self.name}' is OPEN. "
                    f"Rejecting call to {func.__name__} (failing fast)."
                )
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable, try again later."
                )
            
            # Circuit is CLOSED or HALF_OPEN - attempt the call
            try:
                if current_state == CircuitState.HALF_OPEN:
                    logger.info(
                        f"⚡ Circuit Breaker '{self.name}' is HALF_OPEN. "
                        f"Attempting test call to {func.__name__}."
                    )
                
                result = func(*args, **kwargs)
                
                # Call succeeded
                self._record_success()
                return result
                
            except self.config.expected_exception as e:
                # Call failed
                self._record_failure(e)
                raise  # Re-raise the original exception
        
        return wrapper
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection (without decorator)
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Result of function call
        
        Example:
            result = circuit_breaker.execute(requests.get, "http://api/data")
        """
        protected_func = self.call(func)
        return protected_func(*args, **kwargs)
    
    def reset(self):
        """
        Manually reset circuit breaker to CLOSED state
        
        Useful for testing or manual recovery
        """
        with self._lock:
            logger.info(f"🔄 Circuit Breaker '{self.name}' manually reset.")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
    
    def get_status(self) -> dict:
        """
        Get current circuit breaker status
        
        Returns:
            dict: Status information
        """
        with self._lock:
            status = {
                'name': self.name,
                'state': self._state.value,
                'failure_count': self._failure_count,
                'success_count': self._success_count,
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold
            }
            
            if self._last_failure_time:
                time_since_failure = time.time() - self._last_failure_time
                status['time_since_last_failure'] = f"{time_since_failure:.1f}s"
                
                if self._state == CircuitState.OPEN:
                    time_until_halfopen = self.config.recovery_timeout - time_since_failure
                    status['time_until_half_open'] = f"{max(0, time_until_halfopen):.1f}s"
            
            return status


# Example usage
if __name__ == "__main__":
    import requests
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Circuit Breaker Pattern Demo")
    print("=" * 60)
    
    # Create circuit breaker
    cb = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=10,
        success_threshold=2,
        name="demo"
    )
    
    print(f"\nInitial status: {cb.get_status()}")
    
    # Simulate failures
    @cb.call
    def unstable_api_call():
        raise requests.exceptions.ConnectionError("Simulated failure")
    
    print("\nSimulating failures...")
    for i in range(5):
        try:
            unstable_api_call()
        except (requests.exceptions.ConnectionError, CircuitBreakerOpenError) as e:
            print(f"Attempt {i+1}: {type(e).__name__}")
    
    print(f"\nFinal status: {cb.get_status()}")