"""
Integration Test for Backend Client with Circuit Breaker + Retry

This script demonstrates the combined behavior of:
1. Circuit Breaker (handles persistent failures)
2. Retry Logic (handles transient failures)

Test Scenarios:
- Transient errors → Retry handles them
- Persistent errors → Circuit breaker opens
- Mixed errors → Both patterns work together
"""

import time
import requests
from backend_client import backend_client


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_status():
    """Print current circuit breaker status"""
    status = backend_client.get_circuit_breaker_status()
    state_color = {
        'CLOSED': Colors.GREEN,
        'OPEN': Colors.RED,
        'HALF_OPEN': Colors.YELLOW
    }.get(status['state'], Colors.RESET)
    
    print(f"\n{Colors.BOLD}Circuit Breaker Status:{Colors.RESET}")
    print(f"  State: {state_color}{status['state']}{Colors.RESET}")
    print(f"  Failure Count: {status['failure_count']}/{status['failure_threshold']}")
    if 'time_since_last_failure' in status:
        print(f"  Time Since Last Failure: {status['time_since_last_failure']}")
    if 'time_until_half_open' in status:
        print(f"  Time Until HALF_OPEN: {status['time_until_half_open']}")


def configure_backend_errors(failure_rate):
    """Configure backend error rate"""
    try:
        response = requests.post(
            'http://localhost:5000/configfailure',
            json={'failure_rate': failure_rate},
            timeout=5
        )
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓{Colors.RESET} Backend configured: {failure_rate*100}% error rate")
            return True
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.RESET} Cannot configure backend: {e}")
        print(f"{Colors.YELLOW}Note: Make sure backend is running with port-forward{Colors.RESET}")
    return False


def configure_backend_latency(delay_ms, delay_rate):
    """Configure backend latency"""
    try:
        response = requests.post(
            'http://localhost:5000/configlatency',
            json={'delay_ms': delay_ms, 'delay_rate': delay_rate},
            timeout=5
        )
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓{Colors.RESET} Backend configured: {delay_ms}ms delay at {delay_rate*100}% rate")
            return True
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.RESET} Cannot configure backend: {e}")
    return False


def test_scenario_1_normal():
    """Scenario 1: Normal operation (no errors)"""
    print_header("SCENARIO 1: Normal Operation")
    
    print("Testing normal operation with no backend errors...")
    configure_backend_errors(0.0)
    configure_backend_latency(0, 0.0)
    
    print("\nMaking 5 requests...")
    for i in range(5):
        response = backend_client.get_users()
        if response['success']:
            print(f"{Colors.GREEN}✓{Colors.RESET} Request {i+1}: SUCCESS")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} Request {i+1}: FAILED")
    
    print_status()
    print(f"\n{Colors.GREEN}Expected: All requests succeed, circuit stays CLOSED{Colors.RESET}")


def test_scenario_2_transient_errors():
    """Scenario 2: Transient errors (retry handles them)"""
    print_header("SCENARIO 2: Transient Errors (Retry Logic)")
    
    print("Configuring 30% error rate (transient failures)...")
    configure_backend_errors(0.3)
    
    print("\nMaking 10 requests (watch for retry logs)...")
    successes = 0
    for i in range(10):
        print(f"\n--- Request {i+1} ---")
        response = backend_client.get_users()
        if response['success']:
            print(f"{Colors.GREEN}✓{Colors.RESET} SUCCESS")
            successes += 1
        else:
            print(f"{Colors.RED}✗{Colors.RESET} FAILED after retries")
        time.sleep(0.5)
    
    print(f"\nResults: {successes}/10 successful")
    print_status()
    print(f"\n{Colors.YELLOW}Expected: Most requests succeed (retry recovers from transient errors){Colors.RESET}")
    print(f"{Colors.YELLOW}Circuit should remain CLOSED{Colors.RESET}")


def test_scenario_3_persistent_errors():
    """Scenario 3: Persistent errors (circuit breaker opens)"""
    print_header("SCENARIO 3: Persistent Errors (Circuit Breaker)")
    
    print("Configuring 100% error rate (persistent failures)...")
    configure_backend_errors(1.0)
    
    print("\nMaking requests until circuit opens...")
    for i in range(10):
        print(f"\n--- Request {i+1} ---")
        response = backend_client.get_users()
        
        status = backend_client.get_circuit_breaker_status()
        
        if response['success']:
            print(f"{Colors.GREEN}✓{Colors.RESET} SUCCESS")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} FAILED: {response['data'].get('message', 'Unknown error')}")
        
        print(f"Circuit State: {status['state']} (Failures: {status['failure_count']}/5)")
        
        if status['state'] == 'OPEN':
            print(f"\n{Colors.RED}🔥 Circuit Breaker OPENED!{Colors.RESET}")
            break
        
        time.sleep(0.5)
    
    print_status()
    
    # Try more requests - should fail fast
    print(f"\n{Colors.YELLOW}Now making 3 more requests (should fail fast)...{Colors.RESET}")
    for i in range(3):
        start = time.time()
        response = backend_client.get_users()
        elapsed = time.time() - start
        
        print(f"Request {i+1}: FAILED in {elapsed:.3f}s (fast!)")
    
    print(f"\n{Colors.GREEN}Expected:{Colors.RESET}")
    print(f"  1. After 5 failures, circuit opens")
    print(f"  2. Subsequent requests fail immediately (no retry)")
    print(f"  3. Response time is very fast (no backend call)")


def test_scenario_4_recovery():
    """Scenario 4: Circuit breaker recovery"""
    print_header("SCENARIO 4: Circuit Breaker Recovery")
    
    # First open the circuit
    print("Step 1: Opening circuit with persistent errors...")
    configure_backend_errors(1.0)
    
    for i in range(6):
        backend_client.get_users()
        time.sleep(0.2)
    
    print_status()
    
    status = backend_client.get_circuit_breaker_status()
    if status['state'] != 'OPEN':
        print(f"{Colors.YELLOW}Circuit not open yet, trying more requests...{Colors.RESET}")
        for i in range(5):
            backend_client.get_users()
            time.sleep(0.2)
    
    print(f"\n{Colors.BLUE}Step 2: Fixing backend (setting error rate to 0%)...{Colors.RESET}")
    configure_backend_errors(0.0)
    
    print(f"\n{Colors.YELLOW}Step 3: Waiting for recovery timeout (30 seconds)...{Colors.RESET}")
    print("(This is when circuit will transition to HALF_OPEN)")
    
    # Wait and show countdown
    wait_time = 30
    for remaining in range(wait_time, 0, -5):
        print(f"  {remaining}s remaining...")
        time.sleep(5)
        print_status()
    
    print(f"\n{Colors.BLUE}Step 4: Circuit should now be HALF_OPEN, making test calls...{Colors.RESET}")
    
    # Make test calls
    for i in range(3):
        print(f"\nTest call {i+1}:")
        response = backend_client.get_users()
        
        if response['success']:
            print(f"{Colors.GREEN}✓{Colors.RESET} SUCCESS")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} FAILED")
        
        print_status()
        
        status = backend_client.get_circuit_breaker_status()
        if status['state'] == 'CLOSED':
            print(f"\n{Colors.GREEN}🎉 Circuit CLOSED! Recovery complete!{Colors.RESET}")
            break
        
        time.sleep(1)
    
    print(f"\n{Colors.GREEN}Expected:{Colors.RESET}")
    print(f"  1. Circuit opens with persistent errors")
    print(f"  2. After 30s, transitions to HALF_OPEN")
    print(f"  3. Test calls succeed → Circuit closes")
    print(f"  4. System fully recovered!")


def test_scenario_5_mixed():
    """Scenario 5: Mixed behavior"""
    print_header("SCENARIO 5: Mixed Errors + Delays")
    
    print("Configuring mixed conditions:")
    print("  - 20% errors (transient)")
    print("  - 30% delays (1000ms)")
    configure_backend_errors(0.2)
    configure_backend_latency(1000, 0.3)
    
    print("\nMaking 15 requests...")
    results = {'success': 0, 'failed': 0, 'slow': 0}
    
    for i in range(15):
        start = time.time()
        response = backend_client.get_users()
        elapsed = time.time() - start
        
        if response['success']:
            results['success'] += 1
            if elapsed > 1.0:
                results['slow'] += 1
                print(f"{Colors.YELLOW}🐌{Colors.RESET} Request {i+1}: SUCCESS (slow: {elapsed:.1f}s)")
            else:
                print(f"{Colors.GREEN}✓{Colors.RESET} Request {i+1}: SUCCESS ({elapsed:.1f}s)")
        else:
            results['failed'] += 1
            print(f"{Colors.RED}✗{Colors.RESET} Request {i+1}: FAILED")
        
        time.sleep(0.3)
    
    print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
    print(f"  Successful: {results['success']}/15")
    print(f"  Failed: {results['failed']}/15")
    print(f"  Slow (>1s): {results['slow']}/15")
    
    print_status()
    
    print(f"\n{Colors.GREEN}Expected:{Colors.RESET}")
    print(f"  - Retry logic handles transient errors")
    print(f"  - Some requests succeed despite errors")
    print(f"  - Some requests are slow due to delays")
    print(f"  - Circuit stays CLOSED (errors are transient)")


def main():
    """Run all test scenarios"""
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'BACKEND CLIENT INTEGRATION TEST':^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'Circuit Breaker + Retry Logic':^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}Prerequisites:{Colors.RESET}")
    print("1. Backend service running")
    print("2. Port-forward active: kubectl port-forward service/backend-service 5000:5000")
    print("3. Client service accessible")
    
    input(f"\n{Colors.YELLOW}Press Enter to start tests...{Colors.RESET}")
    
    try:
        # Reset circuit breaker
        print(f"\n{Colors.BLUE}Resetting circuit breaker...{Colors.RESET}")
        backend_client.reset_circuit_breaker()
        
        # Run scenarios
        test_scenario_1_normal()
        input(f"\n{Colors.YELLOW}Press Enter for next scenario...{Colors.RESET}")
        
        test_scenario_2_transient_errors()
        input(f"\n{Colors.YELLOW}Press Enter for next scenario...{Colors.RESET}")
        
        # Reset before persistent errors test
        backend_client.reset_circuit_breaker()
        test_scenario_3_persistent_errors()
        input(f"\n{Colors.YELLOW}Press Enter for recovery scenario...{Colors.RESET}")
        
        # Reset before recovery test
        backend_client.reset_circuit_breaker()
        test_scenario_4_recovery()
        input(f"\n{Colors.YELLOW}Press Enter for final scenario...{Colors.RESET}")
        
        # Reset before mixed test
        backend_client.reset_circuit_breaker()
        test_scenario_5_mixed()
        
        print_header("ALL SCENARIOS COMPLETED")
        print(f"{Colors.GREEN}Integration test finished!{Colors.RESET}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error during test: {e}{Colors.RESET}\n")


if __name__ == "__main__":
    main()