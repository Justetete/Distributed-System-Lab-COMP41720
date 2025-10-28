import random
import time
import os
from functools import wraps
from flask import jsonify

class FaultInjector:
    """
    Fault injection utility for simulating various failure scenarios in distributed systems.
    This helps test resilience patterns like circuit breakers and retries.
    """
    
    def __init__(self, 
                 delay_rate=0.0, 
                 error_rate=0.0, 
                 timeout_rate=0.0,
                 min_delay=0.5, 
                 max_delay=3.0):
        """
        Initialize fault injector with configurable failure rates.
        
        Args:
            delay_rate: Probability (0.0-1.0) of injecting artificial delay
            error_rate: Probability (0.0-1.0) of returning 500 error
            timeout_rate: Probability (0.0-1.0) of simulating timeout (very long delay)
            min_delay: Minimum delay in seconds when delay is injected
            max_delay: Maximum delay in seconds when delay is injected
        """
        self.delay_rate = float(os.getenv('FAILURE_DELAY_RATE', delay_rate))
        self.error_rate = float(os.getenv('FAILURE_ERROR_RATE', error_rate))
        self.timeout_rate = float(os.getenv('FAILURE_TIMEOUT_RATE', timeout_rate))
        self.min_delay = float(os.getenv('MIN_DELAY', min_delay))
        self.max_delay = float(os.getenv('MAX_DELAY', max_delay))
        
        print(f"[FaultInjector] Initialized with:")
        print(f"  - Delay Rate: {self.delay_rate * 100}%")
        print(f"  - Error Rate: {self.error_rate * 100}%")
        print(f"  - Timeout Rate: {self.timeout_rate * 100}%")
        print(f"  - Delay Range: {self.min_delay}s - {self.max_delay}s")
    
    def inject_faults(self, f):
        """
        Decorator to inject faults into Flask route handlers.
        
        Usage:
            @app.route('/api/endpoint')
            @fault_injector.inject_faults
            def my_endpoint():
                return jsonify({'data': 'value'})
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Inject timeout (very long delay) - simulates unresponsive service
            if random.random() < self.timeout_rate:
                timeout_delay = random.uniform(10, 30)  # 10-30 seconds
                print(f"[FaultInjector] Injecting TIMEOUT: {timeout_delay:.2f}s delay")
                time.sleep(timeout_delay)
                return jsonify({
                    'success': False,
                    'message': 'Request timeout - service took too long to respond'
                }), 504  # Gateway Timeout
            
            # Inject normal delay - simulates slow service
            if random.random() < self.delay_rate:
                delay = random.uniform(self.min_delay, self.max_delay)
                print(f"[FaultInjector] Injecting DELAY: {delay:.2f}s")
                time.sleep(delay)
            
            # Inject error response - simulates internal server error
            if random.random() < self.error_rate:
                print(f"[FaultInjector] Injecting ERROR: 500 Internal Server Error")
                return jsonify({
                    'success': False,
                    'message': 'Simulated internal server error'
                }), 500
            
            # No fault injected - proceed normally
            return f(*args, **kwargs)
        
        return decorated_function
    
    def set_failure_rate(self, delay_rate=None, error_rate=None, timeout_rate=None):
        """
        Dynamically update failure rates at runtime.
        
        Args:
            delay_rate: New delay injection rate (0.0-1.0)
            error_rate: New error injection rate (0.0-1.0)
            timeout_rate: New timeout injection rate (0.0-1.0)
        """
        if delay_rate is not None:
            self.delay_rate = delay_rate
            print(f"[FaultInjector] Updated delay_rate to {delay_rate * 100}%")
        
        if error_rate is not None:
            self.error_rate = error_rate
            print(f"[FaultInjector] Updated error_rate to {error_rate * 100}%")
        
        if timeout_rate is not None:
            self.timeout_rate = timeout_rate
            print(f"[FaultInjector] Updated timeout_rate to {timeout_rate * 100}%")
    
    def get_status(self):
        """
        Get current fault injector configuration.
        
        Returns:
            dict: Current configuration settings
        """
        return {
            'delay_rate': self.delay_rate,
            'error_rate': self.error_rate,
            'timeout_rate': self.timeout_rate,
            'min_delay': self.min_delay,
            'max_delay': self.max_delay
        }