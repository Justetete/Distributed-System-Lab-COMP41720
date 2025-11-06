"""
Backend Client with Circuit Breaker and Retry Logic

This module provides an HTTP client for communicating with the Backend Service,
with built-in resilience patterns:
- Circuit Breaker: Protects against persistent failures
- Retry Logic: Handles transient failures

Architecture:
    Request → Circuit Breaker → Retry Logic → Backend API
"""

import requests
import logging
from config import config
from retry_logic import retry_on_transient_error, RetryConfig
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# Retry configuration - for transient errors
retry_config = RetryConfig(
    max_attempts=3,      # Retry up to 3 times
    min_wait=1.0,        # Start with 1 second wait
    max_wait=10.0,       # Max 10 seconds wait
    multiplier=2.0       # Double the wait time each retry (exponential backoff)
)

# Circuit breaker configuration - for persistent failures
# These values are set LOW for demo purposes (as suggested in hints)
circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 consecutive failures
    recovery_timeout=30.0,    # Wait 30 seconds before trying HALF_OPEN
    success_threshold=2,      # Need 2 successes to close from HALF_OPEN
    expected_exception=Exception,
    name="backend-service"
)


# ============================================================================
# Backend Client Class
# ============================================================================

class BackendClient:
    """
    HTTP Client for Backend Service communication with resilience patterns
    
    This class encapsulates all API calls to the Backend Service with:
    1. Circuit Breaker protection (handles persistent failures)
    2. Automatic retries with exponential backoff (handles transient failures)
    3. Centralized error handling and logging
    
    Attributes:
        base_url: Base URL of the backend API
        timeout: Request timeout in seconds
        circuit_breaker: Circuit breaker instance for this client
    """
    
    def __init__(self, base_url=None, timeout=None):
        """
        Initialize Backend Client
        
        Args:
            base_url: Backend API base URL (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.base_url = base_url or config.get_backend_api_url()
        self.timeout = timeout or config.REQUEST_TIMEOUT
        self.circuit_breaker = circuit_breaker  # Use shared circuit breaker
        
        logger.info(f"BackendClient initialized with base_url: {self.base_url}")
        logger.info(f"Circuit Breaker config: {self.circuit_breaker.get_status()}")
        logger.info(f"Retry config: {retry_config}")
    
    def _make_request_with_retry(self, method, endpoint, **kwargs):
        """
        Internal method to make HTTP requests with retry logic (no circuit breaker)
        
        This method is wrapped by the circuit breaker in _make_request()
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/users')
            **kwargs: Additional arguments for requests library
        
        Returns:
            dict: Response data with success flag and data/error
        
        Raises:
            requests.exceptions.HTTPError: On retryable HTTP errors
            requests.exceptions.RequestException: On connection/timeout errors
        """
        url = f"{self.base_url}{endpoint}"
        
        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        logger.info(f"Making {method} request to {url}")
        
        # Make the request
        response = requests.request(method, url, **kwargs)
        
        logger.info(f"Response status: {response.status_code}")
        
        # Check if this is a retryable HTTP error status
        # These are transient errors that retry logic will handle
        if response.status_code in [429, 500, 502, 503, 504]:
            logger.warning(f"Retryable HTTP error: {response.status_code}")
            # Raise HTTPError to trigger retry
            response.raise_for_status()
        
        # Check for other HTTP errors (4xx errors - not retryable)
        if response.status_code >= 400:
            # These will NOT be retried by retry logic
            response.raise_for_status()
        
        # Parse JSON response
        try:
            response_data = response.json()
        except ValueError:
            response_data = {'message': response.text}
        
        # Return response with status code
        return {
            'status_code': response.status_code,
            'data': response_data,
            'success': 200 <= response.status_code < 300
        }
    
    @retry_on_transient_error(retry_config)
    def _make_request_with_circuit_breaker(self, method, endpoint, **kwargs):
        """
        Internal method combining circuit breaker and retry logic
        
        Flow:
        1. Circuit breaker checks state (if OPEN, fail fast)
        2. If CLOSED/HALF_OPEN, proceed to retry logic
        3. Retry logic handles transient failures
        4. Results reported back to circuit breaker
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Request arguments
        
        Returns:
            dict: Response data
        
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: If all retries fail
        """
        # This method is protected by @retry decorator
        # The circuit breaker's call() method wraps this entire method
        return self._make_request_with_retry(method, endpoint, **kwargs)
    
    def _make_request(self, method, endpoint, **kwargs):
        """
        Public method to make HTTP requests with full resilience
        
        This method combines:
        1. Circuit Breaker (outer layer)
        2. Retry Logic (inner layer)
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Request arguments
        
        Returns:
            dict: Response data with success flag
        """
        try:
            # Use circuit breaker's execute method
            # This wraps the retry logic
            return self.circuit_breaker.execute(
                self._make_request_with_circuit_breaker,
                method,
                endpoint,
                **kwargs
            )
            
        except CircuitBreakerOpenError as e:
            # Circuit breaker is OPEN - fail fast
            logger.error(f"Circuit breaker OPEN: {str(e)}")
            return {
                'status_code': 503,
                'data': {
                    'success': False,
                    'message': 'Backend service unavailable (circuit breaker open)',
                    'circuit_breaker_status': self.circuit_breaker.get_status()
                },
                'success': False
            }
            
        except requests.exceptions.HTTPError as e:
            # All retries failed with HTTP error
            status_code = e.response.status_code if e.response else 500
            logger.error(f"Failed after all retries: HTTP {status_code}")
            return {
                'status_code': status_code,
                'data': {
                    'success': False,
                    'message': f'Backend service error after retries: {status_code}'
                },
                'success': False
            }
            
        except Exception as e:
            # All retries failed with other error
            logger.error(f"Failed after all retries: {str(e)}")
            return {
                'status_code': 503,
                'data': {
                    'success': False,
                    'message': 'Backend service unavailable after retries'
                },
                'success': False
            }
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    def get_users(self):
        """
        Get all users from backend service
        
        Returns:
            dict: Response containing list of users
        """
        logger.info("Fetching all users from backend")
        return self._make_request('GET', '/users')
    
    def get_user(self, user_id):
        """
        Get a specific user by ID
        
        Args:
            user_id: ID of the user to retrieve
        
        Returns:
            dict: Response containing user data or error
        """
        logger.info(f"Fetching user {user_id} from backend")
        return self._make_request('GET', f'/users/{user_id}')
    
    def create_user(self, user_data):
        """
        Create a new user
        
        Args:
            user_data: Dictionary containing user information
                Required keys: name, id, email
        
        Returns:
            dict: Response containing created user data
        """
        logger.info(f"Creating user in backend: {user_data.get('name')}")
        return self._make_request(
            'POST',
            '/users',
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
    
    def update_user(self, user_id, user_data):
        """
        Update an existing user
        
        Args:
            user_id: ID of the user to update
            user_data: Dictionary containing fields to update
                Optional keys: name, email
        
        Returns:
            dict: Response containing updated user data
        """
        logger.info(f"Updating user {user_id} in backend")
        return self._make_request(
            'PUT',
            f'/users/{user_id}',
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
    
    def delete_user(self, user_id):
        """
        Delete a user
        
        Args:
            user_id: ID of the user to delete
        
        Returns:
            dict: Response containing deleted user data
        """
        logger.info(f"Deleting user {user_id} from backend")
        return self._make_request('DELETE', f'/users/{user_id}')
    
    def health_check(self):
        """
        Check backend service health
        
        Note: Health check does NOT use circuit breaker to avoid
        false positives during health check monitoring.
        
        Returns:
            dict: Health status response
        """
        logger.info("Checking backend service health")
        try:
            response = requests.get(
                f"{self.base_url.replace('/api', '')}/health",
                timeout=2
            )
            return {
                'status_code': response.status_code,
                'healthy': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            logger.error(f"Backend health check failed: {str(e)}")
            return {
                'status_code': 503,
                'healthy': False,
                'data': None
            }
    
    def get_circuit_breaker_status(self):
        """
        Get current circuit breaker status
        
        Returns:
            dict: Circuit breaker status information
        """
        return self.circuit_breaker.get_status()
    
    def reset_circuit_breaker(self):
        """
        Manually reset circuit breaker to CLOSED state
        
        Useful for testing or manual recovery
        """
        logger.info("Manually resetting circuit breaker")
        self.circuit_breaker.reset()


# ============================================================================
# Singleton Instance
# ============================================================================

# Singleton instance for easy import
backend_client = BackendClient()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("Backend Client with Circuit Breaker + Retry Logic")
    print("=" * 60)
    
    # Show configuration
    print(f"\nCircuit Breaker: {backend_client.get_circuit_breaker_status()}")
    print(f"Retry Config: {retry_config}")
    
    # Test health check
    print("\nTesting health check...")
    health = backend_client.health_check()
    print(f"Backend healthy: {health['healthy']}")
    
    # Test get users
    print("\nTesting get users...")
    response = backend_client.get_users()
    print(f"Success: {response['success']}")
    if response['success']:
        print(f"User count: {len(response['data'].get('data', []))}")
    else:
        print(f"Error: {response['data'].get('message')}")