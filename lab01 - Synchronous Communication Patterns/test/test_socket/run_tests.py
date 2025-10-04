#!/usr/bin/env python3
"""
Test runner script for socket lab
Provides better control over test execution and cleanup
"""

import subprocess
import sys
import time
import socket
import threading
import signal
import os
from contextlib import contextmanager


def check_port_available(port):
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False


def wait_for_port_free(port, timeout=5):
    """Wait for a port to become free."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_port_available(port):
            return True
        time.sleep(0.1)
    return False


@contextmanager
def cleanup_environment():
    """Context manager for test environment cleanup."""
    # Kill any existing processes that might be using our test ports
    test_ports = [8081, 8082, 8083, 8084, 8085, 8086]
    
    print("Cleaning up test environment...")
    
    for port in test_ports:
        try:
            # Try to find and kill processes using these ports
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(0.1)
                    except (ProcessLookupError, ValueError):
                        pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # lsof might not be available on all systems
            pass
    
    # Wait for ports to be freed
    time.sleep(0.5)
    
    try:
        yield
    finally:
        print("Final cleanup...")
        time.sleep(0.2)


def run_specific_tests():
    """Run specific test categories separately for better control."""
    
    test_categories = [
        ("Unit Tests", ["test_socket.py::TestSocketServer", "test_socket.py::TestSocketClient"]),
        ("Error Condition Tests", ["test_socket.py::TestErrorConditions"]),
        ("Integration Tests", ["test_socket.py::TestIntegration::test_basic_communication"]),
        ("Multiple Client Test", ["test_socket.py::TestIntegration::test_multiple_clients"]),
        ("Connection Tests", ["test_socket.py::TestIntegration::test_connection_refused"]),
        ("Performance Tests", ["test_socket.py::TestPerformance"]),
    ]
    
    results = {}
    
    for category_name, test_patterns in test_categories:
        print(f"\n{'='*60}")
        print(f"Running {category_name}")
        print(f"{'='*60}")
        
        try:
            # Run tests with shorter timeout
            cmd = [
                sys.executable, "-m", "pytest",
                "--tb=short",
                "--timeout=30",  # 30 second timeout per test
                "-v"
            ] + test_patterns
            
            result = subprocess.run(
                cmd,
                timeout=120,  # 2 minute timeout for the entire category
                capture_output=False  # Show output in real-time
            )
            
            results[category_name] = result.returncode == 0
            
            if result.returncode == 0:
                print(f"✅ {category_name} PASSED")
            else:
                print(f"❌ {category_name} FAILED")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {category_name} TIMED OUT")
            results[category_name] = False
        except Exception as e:
            print(f"💥 {category_name} ERROR: {e}")
            results[category_name] = False
        
        # Wait between test categories
        time.sleep(1)
    
    return results


def run_quick_tests():
    """Run a quick subset of tests that are most reliable."""
    print("Running Quick Test Suite...")
    print("="*50)
    
    quick_tests = [
        "test_socket.py::TestSocketServer",
        "test_socket.py::TestSocketClient", 
        "test_socket.py::TestErrorConditions::test_invalid_host",
        "test_socket.py::TestErrorConditions::test_invalid_port",
        "test_socket.py::TestIntegration::test_connection_refused"
    ]
    
    cmd = [
        sys.executable, "-m", "pytest",
        "--tb=short",
        "-v"
    ] + quick_tests
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Socket Lab Test Runner')
    parser.add_argument('--quick', action='store_true', help='Run quick test suite only')
    parser.add_argument('--full', action='store_true', help='Run full test suite')
    parser.add_argument('--category', help='Run specific test category')
    
    args = parser.parse_args()
    
    with cleanup_environment():
        if args.quick:
            success = run_quick_tests()
            sys.exit(0 if success else 1)
        
        elif args.full:
            print("Running Full Test Suite...")
            cmd = [sys.executable, "-m", "pytest", "test_socket.py", "-v", "--tb=short"]
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        
        elif args.category:
            cmd = [sys.executable, "-m", "pytest", f"test_socket.py::{args.category}", "-v"]
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        
        else:
            # Default: run categorized tests
            results = run_specific_tests()
            
            print(f"\n{'='*60}")
            print("TEST SUMMARY")
            print(f"{'='*60}")
            
            passed = 0
            total = len(results)
            
            for category, success in results.items():
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"{category:30} {status}")
                if success:
                    passed += 1
            
            print(f"\nOverall: {passed}/{total} test categories passed")
            
            # Exit with appropriate code
            sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()