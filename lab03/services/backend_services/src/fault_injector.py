"""
Fault Injector Module

This module provides fault injection capabilities for testing resilience patterns.
It can simulate various failure scenarios including delays, errors, and timeouts.

Usage:
    from fault_injector import fault_injector
    
    @app.route('/api/endpoint')
    @fault_injector.inject_faults
    def endpoint():
        return jsonify({'data': 'response'})
"""

import time
import random
import os
import logging
from functools import wraps
from flask import jsonify


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FaultInjector:
    """
    Fault Injector for simulating various failure scenarios
    
    This class provides decorators and methods to inject faults into
    Flask route handlers, useful for testing resilience patterns.
    """
    
    def __init__(self):
        """
        Initialize FaultInjector with configuration from environment variables
        """
        # Fault injection probabilities (0.0 to 1.0)
        self.delay_rate = float(os.environ.get('FAULT_DELAY_RATE', '0.3'))
        self.error_rate = float(os.environ.get('FAULT_ERROR_RATE', '0.2'))
        self.timeout_rate = float(os.environ.get('FAULT_TIMEOUT_RATE', '0.1'))
        
        # Delay configuration (in seconds)
        self.min_delay = float(os.environ.get('FAULT_MIN_DELAY', '1.0'))
        self.max_delay = float(os.environ.get('FAULT_MAX_DELAY', '5.0'))
        
        # Timeout configuration (in seconds)
        self.timeout_delay = float(os.environ.get('FAULT_TIMEOUT_DELAY', '30.0'))
        
        # Enable/disable fault injection
        self.enabled = os.environ.get('FAULT_INJECTION_ENABLED', 'true').lower() == 'true'
        
        logger.info(f"FaultInjector initialized: enabled={self.enabled}")
        if self.enabled:
            logger.info(f"  Delay rate: {self.delay_rate * 100}%")
            logger.info(f"  Error rate: {self.error_rate * 100}%")
            logger.info(f"  Timeout rate: {self.timeout_rate * 100}%")
    
    def inject_faults(self, f):
        """
        Decorator to inject faults into Flask route handlers
        
        This decorator will randomly inject:
        1. Delays (slow responses)
        2. HTTP 500 errors
        3. Timeouts (very long delays)
        
        Args:
            f: Flask route handler function
        
        Returns:
            Wrapped function with fault injection
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip fault injection if disabled
            if not self.enabled:
                return f(*args, **kwargs)
            
            # Inject timeout (highest priority - simulates complete hang)
            if random.random() < self.timeout_rate:
                logger.warning(f"💤 FAULT INJECTED: Timeout on {f.__name__} (sleeping {self.timeout_delay}s)")
                time.sleep(self.timeout_delay)
                return jsonify({
                    'success': False,
                    'message': 'Request timeout - service took too long to respond'
                }), 504
            
            # Inject error (medium priority - simulates server error)
            if random.random() < self.error_rate:
                logger.warning(f"💥 FAULT INJECTED: 500 Error on {f.__name__}")
                return jsonify({
                    'success': False,
                    'message': 'Simulated server error for testing resilience'
                }), 500
            
            # Inject delay (lowest priority - simulates slow response)
            if random.random() < self.delay_rate:
                delay = random.uniform(self.min_delay, self.max_delay)
                logger.warning(f"🐌 FAULT INJECTED: Delay on {f.__name__} ({delay:.2f}s)")
                time.sleep(delay)
            
            # Execute the original function
            return f(*args, **kwargs)
        
        return decorated_function
    
    def inject_delay_only(self, f):
        """
        Decorator to inject only delays (no errors)
        
        Useful for testing retry mechanisms without complete failures
        
        Args:
            f: Flask route handler function
        
        Returns:
            Wrapped function with delay injection
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.enabled:
                return f(*args, **kwargs)
            
            if random.random() < self.delay_rate:
                delay = random.uniform(self.min_delay, self.max_delay)
                logger.warning(f"🐌 DELAY INJECTED: {f.__name__} ({delay:.2f}s)")
                time.sleep(delay)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def inject_error_only(self, f):
        """
        Decorator to inject only errors (no delays)
        
        Useful for testing circuit breaker behavior
        
        Args:
            f: Flask route handler function
        
        Returns:
            Wrapped function with error injection
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.enabled:
                return f(*args, **kwargs)
            
            if random.random() < self.error_rate:
                logger.warning(f"💥 ERROR INJECTED: {f.__name__}")
                return jsonify({
                    'success': False,
                    'message': 'Simulated server error'
                }), 500
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def set_rates(self, delay_rate=None, error_rate=None, timeout_rate=None):
        """
        Dynamically adjust fault injection rates
        
        Args:
            delay_rate: Probability of delay injection (0.0 to 1.0)
            error_rate: Probability of error injection (0.0 to 1.0)
            timeout_rate: Probability of timeout injection (0.0 to 1.0)
        """
        if delay_rate is not None:
            self.delay_rate = delay_rate
            logger.info(f"Delay rate updated to {delay_rate * 100}%")
        
        if error_rate is not None:
            self.error_rate = error_rate
            logger.info(f"Error rate updated to {error_rate * 100}%")
        
        if timeout_rate is not None:
            self.timeout_rate = timeout_rate
            logger.info(f"Timeout rate updated to {timeout_rate * 100}%")
    
    def enable(self):
        """Enable fault injection"""
        self.enabled = True
        logger.info("Fault injection ENABLED")
    
    def disable(self):
        """Disable fault injection"""
        self.enabled = False
        logger.info("Fault injection DISABLED")
    
    def get_config(self):
        """
        Get current fault injection configuration
        
        Returns:
            dict: Current configuration
        """
        return {
            'enabled': self.enabled,
            'delay_rate': self.delay_rate,
            'error_rate': self.error_rate,
            'timeout_rate': self.timeout_rate,
            'min_delay': self.min_delay,
            'max_delay': self.max_delay,
            'timeout_delay': self.timeout_delay
        }


# Singleton instance
fault_injector = FaultInjector()