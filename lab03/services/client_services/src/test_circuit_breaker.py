"""
Circuit Breaker Test Suite

Comprehensive tests for the Circuit Breaker pattern implementation.
Tests all three states (CLOSED, OPEN, HALF_OPEN) and state transitions.

Usage:
    python test_circuit_breaker.py
"""

import time
import logging
from circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    CircuitBreakerConfig
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestCircuitBreaker:
    """Test suite for Circuit Breaker"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def print_header(self, text):
        """Print test section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    def assert_equal(self, actual, expected, test_name):
        """Assert equality"""
        self.total += 1
        if actual == expected:
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET}: {test_name}")
            print(f"  Expected: {expected}, Got: {actual}")
            self.passed += 1
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.RESET}: {test_name}")
            print(f"  Expected: {expected}, Got: {actual}")
            self.failed += 1
            return False
    
    def assert_true(self, condition, test_name):
        """Assert condition is true"""
        self.total += 1
        if condition:
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET}: {test_name}")
            self.passed += 1
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.RESET}: {test_name}")
            self.failed += 1
            return False
    
    def test_initial_state(self):
        """Test 1: Initial state should be CLOSED"""
        self.print_header("TEST 1: Initial State")
        
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5, name="test1")
        
        self.assert_equal(
            cb.state,
            CircuitState.CLOSED,
            "Initial state is CLOSED"
        )
        
        self.assert_equal(
            cb.failure_count,
            0,
            "Initial failure count is 0"
        )
        
        print(f"\nStatus: {cb.get_status()}")
    
    def test_successful_calls(self):
        """Test 2: Successful calls keep circuit CLOSED"""
        self.print_header("TEST 2: Successful Calls")
        
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5, name="test2")
        
        @cb.call
        def successful_call():
            return "success"
        
        # Make multiple successful calls
        for i in range(5):
            result = successful_call()
            print(f"Call {i+1}: {result}")
        
        self.assert_equal(
            cb.state,
            CircuitState.CLOSED,
            "Circuit remains CLOSED after successful calls"
        )
        
        self.assert_equal(
            cb.failure_count,
            0,
            "Failure count remains 0"
        )
    
    def test_transition_to_open(self):
        """Test 3: Circuit opens after failure threshold"""
        self.print_header("TEST 3: Transition to OPEN State")
        
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5, name="test3")
        
        @cb.call
        def failing_call():
            raise Exception("Simulated failure")
        
        print("Making failing calls...")
        
        # Make calls that exceed threshold
        for i in range(3):
            try:
                failing_call()
            except Exception as e:
                print(f"Call {i+1}: Failed with {type(e).__name__}")
        
        self.assert_equal(
            cb.state,
            CircuitState.OPEN,
            "Circuit is OPEN after exceeding failure threshold"
        )
        
        print(f"\nStatus: {cb.get_status()}")
    
    def test_fail_fast_when_open(self):
        """Test 4: Circuit breaker fails fast when OPEN"""
        self.print_header("TEST 4: Fail Fast When OPEN")
        
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=5, name="test4")
        
        @cb.call
        def backend_call():
            raise Exception("Backend error")
        
        # Trigger circuit to OPEN
        for i in range(2):
            try:
                backend_call()
            except Exception:
                pass
        
        print(f"Circuit state: {cb.state}")
        
        # Now try calling - should fail fast
        exception_raised = False
        try:
            backend_call()
        except CircuitBreakerOpenError as e:
            exception_raised = True
            print(f"✓ Circuit breaker open error raised: {e}")
        except Exception as e:
            print(f"✗ Wrong exception type: {type(e).__name__}")
        
        self.assert_true(
            exception_raised,
            "CircuitBreakerOpenError raised when circuit is OPEN"
        )
    
    def test_transition_to_half_open(self):
        """Test 5: Circuit transitions to HALF_OPEN after timeout"""
        self.print_header("TEST 5: Transition to HALF_OPEN")
        
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=2,  # Short timeout for testing
            name="test5"
        )
        
        @cb.call
        def backend_call():
            raise Exception("Backend error")
        
        # Open the circuit
        print("Opening circuit...")
        for i in range(2):
            try:
                backend_call()
            except Exception:
                pass
        
        print(f"State after failures: {cb.state}")
        self.assert_equal(cb.state, CircuitState.OPEN, "Circuit is OPEN")
        
        # Wait for recovery timeout
        print(f"\nWaiting {cb.config.recovery_timeout}s for recovery timeout...")
        time.sleep(cb.config.recovery_timeout + 0.5)
        
        # Check state (should transition to HALF_OPEN when we check)
        current_state = cb.state
        print(f"State after timeout: {current_state}")
        
        self.assert_equal(
            current_state,
            CircuitState.HALF_OPEN,
            "Circuit transitions to HALF_OPEN after recovery timeout"
        )
    
    def test_half_open_to_closed(self):
        """Test 6: HALF_OPEN to CLOSED on successful test calls"""
        self.print_header("TEST 6: HALF_OPEN → CLOSED Recovery")
        
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=2,
            success_threshold=2,
            name="test6"
        )
        
        call_count = 0
        
        @cb.call
        def backend_call():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Initial failures")
            return "success"
        
        # Open the circuit
        print("Opening circuit with failures...")
        for i in range(2):
            try:
                backend_call()
            except Exception:
                pass
        
        print(f"State: {cb.state}")
        
        # Wait for HALF_OPEN
        print(f"\nWaiting for HALF_OPEN...")
        time.sleep(cb.config.recovery_timeout + 0.5)
        
        print(f"State: {cb.state}")
        
        # Make successful calls to close circuit
        print("\nMaking successful test calls...")
        for i in range(2):
            try:
                result = backend_call()
                print(f"Call {i+1}: {result} (State: {cb.state})")
            except Exception as e:
                print(f"Call {i+1}: Failed - {e}")
        
        self.assert_equal(
            cb.state,
            CircuitState.CLOSED,
            "Circuit closes after successful test calls"
        )
    
    def test_half_open_to_open(self):
        """Test 7: HALF_OPEN back to OPEN on failed test call"""
        self.print_header("TEST 7: HALF_OPEN → OPEN on Failure")
        
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=2,
            name="test7"
        )
        
        @cb.call
        def backend_call():
            raise Exception("Still failing")
        
        # Open the circuit
        print("Opening circuit...")
        for i in range(2):
            try:
                backend_call()
            except Exception:
                pass
        
        # Wait for HALF_OPEN
        print(f"\nWaiting for HALF_OPEN...")
        time.sleep(cb.config.recovery_timeout + 0.5)
        
        print(f"State before test call: {cb.state}")
        
        # Test call fails - should go back to OPEN
        print("\nAttempting test call (will fail)...")
        try:
            backend_call()
        except Exception:
            pass
        
        print(f"State after failed test call: {cb.state}")
        
        self.assert_equal(
            cb.state,
            CircuitState.OPEN,
            "Circuit re-opens after failed test call"
        )
    
    def test_manual_reset(self):
        """Test 8: Manual reset"""
        self.print_header("TEST 8: Manual Reset")
        
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=5, name="test8")
        
        @cb.call
        def failing_call():
            raise Exception("Error")
        
        # Open the circuit
        print("Opening circuit...")
        for i in range(2):
            try:
                failing_call()
            except Exception:
                pass
        
        print(f"State: {cb.state}")
        self.assert_equal(cb.state, CircuitState.OPEN, "Circuit is OPEN")
        
        # Manual reset
        print("\nManually resetting circuit...")
        cb.reset()
        
        print(f"State after reset: {cb.state}")
        
        self.assert_equal(
            cb.state,
            CircuitState.CLOSED,
            "Circuit is CLOSED after manual reset"
        )
        
        self.assert_equal(
            cb.failure_count,
            0,
            "Failure count reset to 0"
        )
    
    def test_execute_method(self):
        """Test 9: Execute method (non-decorator usage)"""
        self.print_header("TEST 9: Execute Method")
        
        cb = CircuitBreaker(failure_threshold=3, name="test9")
        
        def successful_function():
            return "success"
        
        def failing_function():
            raise Exception("Error")
        
        # Execute successful call
        print("Executing successful function...")
        result = cb.execute(successful_function)
        print(f"Result: {result}")
        
        self.assert_equal(result, "success", "Execute method works for successful calls")
        
        # Execute failing calls
        print("\nExecuting failing function multiple times...")
        for i in range(3):
            try:
                cb.execute(failing_function)
            except Exception as e:
                print(f"Call {i+1}: {type(e).__name__}")
        
        # Circuit should be OPEN
        exception_raised = False
        try:
            cb.execute(failing_function)
        except CircuitBreakerOpenError:
            exception_raised = True
            print("\n✓ Circuit breaker correctly prevents call when OPEN")
        
        self.assert_true(
            exception_raised,
            "Execute method respects circuit breaker state"
        )
    
    def test_config_object(self):
        """Test 10: CircuitBreakerConfig object"""
        self.print_header("TEST 10: CircuitBreakerConfig")
        
        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30,
            success_threshold=2
        )
        
        print(f"Config: {config}")
        
        self.assert_equal(
            config.failure_threshold,
            5,
            "Config failure_threshold is correct"
        )
        
        self.assert_equal(
            config.recovery_timeout,
            30,
            "Config recovery_timeout is correct"
        )
        
        self.assert_equal(
            config.success_threshold,
            2,
            "Config success_threshold is correct"
        )
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'CIRCUIT BREAKER TEST SUITE':^70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
        
        self.test_initial_state()
        self.test_successful_calls()
        self.test_transition_to_open()
        self.test_fail_fast_when_open()
        self.test_transition_to_half_open()
        self.test_half_open_to_closed()
        self.test_half_open_to_open()
        self.test_manual_reset()
        self.test_execute_method()
        self.test_config_object()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'TEST SUMMARY':^70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
        
        print(f"Total Tests:  {self.total}")
        print(f"{Colors.GREEN}Passed:       {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed:       {self.failed}{Colors.RESET}")
        
        pass_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        print(f"\nPass Rate:    {pass_rate:.1f}%")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! 🎉{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Review output above.{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


if __name__ == "__main__":
    tester = TestCircuitBreaker()
    tester.run_all_tests()