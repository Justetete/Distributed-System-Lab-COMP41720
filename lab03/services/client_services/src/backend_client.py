import requests
import logging
from config import config


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackendClient:
    """
    HTTP Client for Backend Service communication
    
    This class encapsulates all API calls to the Backend Service,
    providing a clean interface and centralized error handling.
    
    Attributes:
        base_url: Base URL of the backend API
        timeout: Request timeout in seconds
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
        logger.info(f"BackendClient initialized with base_url: {self.base_url}")
    
    def _make_request(self, method, endpoint, **kwargs):
        """
        Internal method to make HTTP requests with error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/users')
            **kwargs: Additional arguments for requests library
        
        Returns:
            dict: Response data with success flag and data/error
        """
        url = f"{self.base_url}{endpoint}"
        
        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        try:
            logger.info(f"Making {method} request to {url}")
            response = requests.request(method, url, **kwargs)
            
            logger.info(f"Response status: {response.status_code}")
            
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
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for {method} {url}")
            return {
                'status_code': 504,
                'data': {
                    'success': False,
                    'message': 'Backend service request timeout'
                },
                'success': False,
                'error_type': 'timeout'
            }
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {method} {url}")
            return {
                'status_code': 503,
                'data': {
                    'success': False,
                    'message': 'Backend service unavailable'
                },
                'success': False,
                'error_type': 'connection'
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {method} {url}: {str(e)}")
            return {
                'status_code': 500,
                'data': {
                    'success': False,
                    'message': f'Backend service error: {str(e)}'
                },
                'success': False,
                'error_type': 'request'
            }
    
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


# Singleton instance for easy import
backend_client = BackendClient()