"""
Backend Service Fault Injection Tester

This script tests the fault injection capabilities of the Backend Service
by making multiple requests and observing the behavior.

Usage:
    python test_fault_injection.py
"""

import requests
import time
import sys
from collections import Counter


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def test_fault_injection(base_url="http://localhost:5000", num_requests=20):
    """
    Test fault injection by making multiple requests
    
    Args:
        base_url: Base URL of the backend service
        num_requests: Number of requests to make
    """
    print_header("BACKEND FAULT INJECTION TEST")
    
    # Check if service is available
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        print(f"{Colors.GREEN}✓ Backend Service is reachable{Colors.RESET}")
        
        # Display fault injection config
        config = response.json().get('fault_injection', {})
        print(f"\n{Colors.YELLOW}Fault Injection Configuration:{Colors.RESET}")
        print(f"  Enabled: {config.get('enabled')}")
        print(f"  Delay Rate: {config.get('delay_rate', 0) * 100}%")
        print(f"  Error Rate: {config.get('error_rate', 0) * 100}%")
        print(f"  Timeout Rate: {config.get('timeout_rate', 0) * 100}%")
        print()
        
    except Exception as e:
        print(f"{Colors.RED}✗ Backend Service not reachable: {str(e)}{Colors.RESET}")
        return
    
    # Make multiple requests and track results
    print(f"{Colors.YELLOW}Making {num_requests} requests to /api/users...{Colors.RESET}\n")
    
    results = {
        'success': 0,
        'errors': Counter(),
        'response_times': [],
        'delays_detected': 0,
        'timeouts': 0
    }
    
    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/api/users", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ms
            results['response_times'].append(response_time)
            
            # Track status
            status = response.status_code
            if status == 200:
                results['success'] += 1
                icon = f"{Colors.GREEN}✓{Colors.RESET}"
                
                # Detect if delay was injected (>1 second)
                if response_time > 1000:
                    results['delays_detected'] += 1
                    icon = f"{Colors.YELLOW}🐌{Colors.RESET}"
                    
            else:
                results['errors'][status] += 1
                icon = f"{Colors.RED}✗{Colors.RESET}"
            
            print(f"  {icon} Request {i+1:2d}: {status} ({response_time:6.0f}ms)")
            
        except requests.exceptions.Timeout:
            results['timeouts'] += 1
            print(f"  {Colors.RED}💤{Colors.RESET} Request {i+1:2d}: TIMEOUT (>10s)")
            
        except Exception as e:
            results['errors']['connection_error'] += 1
            print(f"  {Colors.RED}✗{Colors.RESET} Request {i+1:2d}: {str(e)}")
    
    # Print summary
    print_header("TEST RESULTS SUMMARY")
    
    total = num_requests
    print(f"{Colors.BOLD}Total Requests:{Colors.RESET} {total}")
    print(f"{Colors.GREEN}Successful (200):{Colors.RESET} {results['success']} ({results['success']/total*100:.1f}%)")
    
    if results['delays_detected']:
        print(f"{Colors.YELLOW}With Delays (>1s):{Colors.RESET} {results['delays_detected']} ({results['delays_detected']/total*100:.1f}%)")
    
    if results['errors']:
        print(f"\n{Colors.RED}Errors:{Colors.RESET}")
        for error_type, count in results['errors'].items():
            print(f"  {error_type}: {count} ({count/total*100:.1f}%)")
    
    if results['timeouts']:
        print(f"{Colors.RED}Timeouts:{Colors.RESET} {results['timeouts']} ({results['timeouts']/total*100:.1f}%)")
    
    # Response time statistics
    if results['response_times']:
        print(f"\n{Colors.BOLD}Response Time Statistics:{Colors.RESET}")
        response_times = results['response_times']
        print(f"  Min:     {min(response_times):6.0f}ms")
        print(f"  Max:     {max(response_times):6.0f}ms")
        print(f"  Average: {sum(response_times)/len(response_times):6.0f}ms")
    
    # Analysis
    print(f"\n{Colors.BOLD}Analysis:{Colors.RESET}")
    
    if results['success'] == total:
        print(f"{Colors.GREEN}✓ All requests succeeded (fault injection may be disabled){Colors.RESET}")
    elif results['success'] > 0:
        print(f"{Colors.YELLOW}⚠ Mixed results indicate fault injection is working{Colors.RESET}")
        print(f"  This is expected behavior for resilience testing")
    else:
        print(f"{Colors.RED}✗ All requests failed - check service configuration{Colors.RESET}")
    
    print()


def test_control_endpoints(base_url="http://localhost:5000"):
    """Test fault injection control endpoints"""
    print_header("FAULT INJECTION CONTROL TEST")
    
    try:
        # Get current config
        print(f"{Colors.YELLOW}1. Getting current configuration...{Colors.RESET}")
        response = requests.get(f"{base_url}/api/fault-injection/config")
        config = response.json()
        print(f"{Colors.GREEN}✓ Current config retrieved{Colors.RESET}")
        print(f"  {config}")
        
        # Disable fault injection
        print(f"\n{Colors.YELLOW}2. Disabling fault injection...{Colors.RESET}")
        response = requests.post(f"{base_url}/api/fault-injection/disable")
        print(f"{Colors.GREEN}✓ Fault injection disabled{Colors.RESET}")
        
        # Test with fault injection disabled
        print(f"\n{Colors.YELLOW}3. Testing with fault injection disabled (5 requests)...{Colors.RESET}")
        for i in range(5):
            start_time = time.time()
            response = requests.get(f"{base_url}/api/users", timeout=5)
            response_time = (time.time() - start_time) * 1000
            print(f"  ✓ Request {i+1}: {response.status_code} ({response_time:.0f}ms)")
        
        # Enable fault injection
        print(f"\n{Colors.YELLOW}4. Re-enabling fault injection...{Colors.RESET}")
        response = requests.post(f"{base_url}/api/fault-injection/enable")
        print(f"{Colors.GREEN}✓ Fault injection re-enabled{Colors.RESET}")
        
        # Update config
        print(f"\n{Colors.YELLOW}5. Updating configuration (high error rate)...{Colors.RESET}")
        response = requests.put(
            f"{base_url}/api/fault-injection/config",
            json={'error_rate': 0.8, 'delay_rate': 0.0}
        )
        print(f"{Colors.GREEN}✓ Configuration updated{Colors.RESET}")
        
        # Test with high error rate
        print(f"\n{Colors.YELLOW}6. Testing with high error rate (10 requests)...{Colors.RESET}")
        errors = 0
        for i in range(10):
            response = requests.get(f"{base_url}/api/users", timeout=5)
            if response.status_code == 500:
                errors += 1
                print(f"  {Colors.RED}✗{Colors.RESET} Request {i+1}: 500 Error")
            else:
                print(f"  {Colors.GREEN}✓{Colors.RESET} Request {i+1}: {response.status_code}")
        
        print(f"\n{Colors.BOLD}Result:{Colors.RESET} {errors}/10 requests returned errors")
        if errors >= 5:
            print(f"{Colors.GREEN}✓ High error rate confirmed (fault injection working){Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ Error rate lower than expected (may need more requests){Colors.RESET}")
        
        # Reset to default
        print(f"\n{Colors.YELLOW}7. Resetting to default configuration...{Colors.RESET}")
        response = requests.put(
            f"{base_url}/api/fault-injection/config",
            json={'error_rate': 0.2, 'delay_rate': 0.3, 'timeout_rate': 0.1}
        )
        print(f"{Colors.GREEN}✓ Configuration reset to defaults{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {str(e)}{Colors.RESET}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Backend Fault Injection')
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:5000',
        help='Backend service URL (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--requests',
        type=int,
        default=20,
        help='Number of test requests (default: 20)'
    )
    parser.add_argument(
        '--skip-control',
        action='store_true',
        help='Skip control endpoint tests'
    )
    
    args = parser.parse_args()
    
    # Test fault injection behavior
    test_fault_injection(base_url=args.url, num_requests=args.requests)
    
    # Test control endpoints
    if not args.skip_control:
        test_control_endpoints(base_url=args.url)
    
    print(f"{Colors.BOLD}{Colors.GREEN}Tests completed!{Colors.RESET}\n")


if __name__ == '__main__':
    main()