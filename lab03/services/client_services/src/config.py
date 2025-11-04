"""
Configuration module for Client Service

This module manages all configuration settings for the client service,
including backend service connection details, timeouts, and port settings.
"""

import os


class Config:
    """
    Configuration class for Client Service
    
    Attributes:
        BACKEND_URL: URL of the backend service
        CLIENT_PORT: Port on which client service runs
        REQUEST_TIMEOUT: Timeout for backend requests in seconds
        DEBUG: Debug mode flag
    """
    
    # Backend Service Configuration
    # In Kubernetes: http://backend-service:5000
    # In local dev: http://localhost:5000
    BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')
    
    # Client Service Configuration
    CLIENT_PORT = int(os.environ.get('CLIENT_PORT', 8080))
    CLIENT_HOST = os.environ.get('CLIENT_HOST', '0.0.0.0')
    
    # Request Configuration
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 5))  # seconds
    
    # Application Configuration
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_backend_api_url(cls):
        """
        Get the full backend API base URL
        
        Returns:
            str: Backend API base URL
        """
        return f"{cls.BACKEND_URL}/api"
    
    @classmethod
    def display_config(cls):
        """
        Display current configuration (for debugging)
        
        Returns:
            dict: Configuration dictionary
        """
        return {
            'backend_url': cls.BACKEND_URL,
            'client_port': cls.CLIENT_PORT,
            'client_host': cls.CLIENT_HOST,
            'request_timeout': cls.REQUEST_TIMEOUT,
            'debug': cls.DEBUG,
            'log_level': cls.LOG_LEVEL
        }


# For easy import
config = Config()