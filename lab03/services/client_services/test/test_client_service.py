"""
Test Suite for Client Service

This test file provides comprehensive testing for the Client Service,
including all CRUD operations, error handling, and edge cases.

Usage:
    python test_client_service.py
    
Requirements:
    - Client Service running on http://localhost:8080
    - Backend Service running on http://localhost:5000
    - requests library installed
"""

import requests
import json
import time
import sys
from typing import Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ClientServiceTester:
    """
    Test suite for Client Service
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the tester
        
        Args:
            base_url: Base URL of the client service
        """
        self.base_url = base_url
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_tests = 0
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    def print_test(self, test_name: str):
        """Print test name"""
        print(f"{Colors.YELLOW}Test: {test_name}{Colors.RESET}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ PASS: {message}{Colors.RESET}")
        self.passed_tests += 1
    
    def print_failure(self, message: str):
        """Print failure message"""
        print(f"{Colors.RED}✗ FAIL: {message}{Colors.RESET}")
        self.failed_tests += 1
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"  {message}")
    
    def assert_response(self, response: requests.Response, 
                       expected_status: int, 
                       test_name: str) -> bool:
        """
        Assert response status code
        
        Args:
            response: HTTP response object
            expected_status: Expected status code
            test_name: Name of the test
        
        Returns:
            True if assertion passes, False otherwise
        """
        self.total_tests += 1
        
        if response.status_code == expected_status:
            self.print_success(f"{test_name} - Status code: {response.status_code}")
            return True
        else:
            self.print_failure(
                f"{test_name} - Expected {expected_status}, got {response.status_code}"
            )
            self.print_info(f"Response: {response.text}")
            return False
    
    def test_health_check(self):
        """Test 1: Health check endpoint"""
        self.print_test("1. Health Check")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if self.assert_response(response, 200, "Health check"):
                data = response.json()
                self.print_info(f"Service status: {data.get('status')}")
                self.print_info(f"Backend connected: {data.get('backend', {}).get('connected')}")
                
                # Check if response has expected structure
                if 'status' in data and 'backend' in data:
                    self.print_success("Health check response structure is correct")
                    self.total_tests += 1
                else:
                    self.print_failure("Health check response structure is incorrect")
                    self.total_tests += 1
                    
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Health check - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_root_endpoint(self):
        """Test 2: Root endpoint"""
        self.print_test("2. Root Endpoint")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            
            if self.assert_response(response, 200, "Root endpoint"):
                data = response.json()
                self.print_info(f"Service: {data.get('service')}")
                self.print_info(f"Version: {data.get('version')}")
                
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Root endpoint - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_get_all_users(self):
        """Test 3: Get all users"""
        self.print_test("3. Get All Users")
        
        try:
            response = requests.get(f"{self.base_url}/client/users", timeout=5)
            
            if self.assert_response(response, 200, "Get all users"):
                data = response.json()
                
                # Check if response has expected structure
                if 'success' in data and 'data' in data:
                    self.print_success("Response structure is correct")
                    self.total_tests += 1
                    
                    users = data.get('data', [])
                    self.print_info(f"Number of users: {len(users)}")
                    
                    if len(users) > 0:
                        self.print_info(f"First user: {users[0].get('name')}")
                else:
                    self.print_failure("Response structure is incorrect")
                    self.total_tests += 1
                    
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Get all users - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_create_user(self):
        """Test 4: Create a new user"""
        self.print_test("4. Create User")
        
        user_data = {
            "name": "Test User",
            "id": 9999,
            "email": "test.user@example.com"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/client/users",
                json=user_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if self.assert_response(response, 201, "Create user"):
                data = response.json()
                self.print_info(f"Created user: {data.get('data', {}).get('name')}")
                
                # Verify created user data
                created_user = data.get('data', {})
                if (created_user.get('id') == user_data['id'] and
                    created_user.get('name') == user_data['name'] and
                    created_user.get('email') == user_data['email']):
                    self.print_success("Created user data matches input")
                    self.total_tests += 1
                else:
                    self.print_failure("Created user data doesn't match input")
                    self.total_tests += 1
                    
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Create user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_get_specific_user(self):
        """Test 5: Get a specific user"""
        self.print_test("5. Get Specific User (ID: 9999)")
        
        try:
            response = requests.get(f"{self.base_url}/client/users/9999", timeout=5)
            
            if self.assert_response(response, 200, "Get specific user"):
                data = response.json()
                user = data.get('data', {})
                self.print_info(f"User name: {user.get('name')}")
                self.print_info(f"User email: {user.get('email')}")
                
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Get specific user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_update_user(self):
        """Test 6: Update an existing user"""
        self.print_test("6. Update User")
        
        update_data = {
            "name": "Updated Test User",
            "email": "updated.test@example.com"
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/client/users/9999",
                json=update_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if self.assert_response(response, 200, "Update user"):
                data = response.json()
                updated_user = data.get('data', {})
                self.print_info(f"Updated name: {updated_user.get('name')}")
                self.print_info(f"Updated email: {updated_user.get('email')}")
                
                # Verify updated data
                if (updated_user.get('name') == update_data['name'] and
                    updated_user.get('email') == update_data['email']):
                    self.print_success("User data updated correctly")
                    self.total_tests += 1
                else:
                    self.print_failure("User data not updated correctly")
                    self.total_tests += 1
                    
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Update user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_delete_user(self):
        """Test 7: Delete a user"""
        self.print_test("7. Delete User")
        
        try:
            response = requests.delete(f"{self.base_url}/client/users/9999", timeout=5)
            
            if self.assert_response(response, 200, "Delete user"):
                data = response.json()
                deleted_user = data.get('data', {})
                self.print_info(f"Deleted user: {deleted_user.get('name')}")
                
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Delete user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_get_nonexistent_user(self):
        """Test 8: Get non-existent user (404 test)"""
        self.print_test("8. Get Non-existent User (404 Test)")
        
        try:
            response = requests.get(f"{self.base_url}/client/users/99999", timeout=5)
            
            self.assert_response(response, 404, "Get non-existent user")
            
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Get non-existent user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_create_user_missing_fields(self):
        """Test 9: Create user with missing fields (400 test)"""
        self.print_test("9. Create User with Missing Fields (400 Test)")
        
        invalid_data = {
            "name": "Incomplete User"
            # Missing 'id' and 'email'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/client/users",
                json=invalid_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            self.assert_response(response, 400, "Create user with missing fields")
            
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Create user with missing fields - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_create_duplicate_user(self):
        """Test 10: Create duplicate user (409 test)"""
        self.print_test("10. Create Duplicate User (409 Test)")
        
        # First, create a user
        user_data = {
            "name": "Duplicate Test User",
            "id": 8888,
            "email": "duplicate@example.com"
        }
        
        try:
            # Create first user
            response1 = requests.post(
                f"{self.base_url}/client/users",
                json=user_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response1.status_code == 201:
                self.print_info("First user created successfully")
                
                # Try to create duplicate
                response2 = requests.post(
                    f"{self.base_url}/client/users",
                    json=user_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                
                self.assert_response(response2, 409, "Create duplicate user")
                
                # Cleanup: delete the test user
                requests.delete(f"{self.base_url}/client/users/8888", timeout=5)
                
            else:
                self.print_failure("Failed to create first user for duplicate test")
                self.total_tests += 1
                
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Create duplicate user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_update_nonexistent_user(self):
        """Test 11: Update non-existent user (404 test)"""
        self.print_test("11. Update Non-existent User (404 Test)")
        
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com"
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/client/users/77777",
                json=update_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            self.assert_response(response, 404, "Update non-existent user")
            
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Update non-existent user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_delete_nonexistent_user(self):
        """Test 12: Delete non-existent user (404 test)"""
        self.print_test("12. Delete Non-existent User (404 Test)")
        
        try:
            response = requests.delete(f"{self.base_url}/client/users/77777", timeout=5)
            
            self.assert_response(response, 404, "Delete non-existent user")
            
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Delete non-existent user - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_invalid_endpoint(self):
        """Test 13: Invalid endpoint (404 test)"""
        self.print_test("13. Invalid Endpoint (404 Test)")
        
        try:
            response = requests.get(f"{self.base_url}/invalid/endpoint", timeout=5)
            
            self.assert_response(response, 404, "Invalid endpoint")
            
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Invalid endpoint - Connection error: {str(e)}")
            self.total_tests += 1
    
    def test_response_time(self):
        """Test 14: Response time check"""
        self.print_test("14. Response Time Check")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/client/users", timeout=5)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            self.print_info(f"Response time: {response_time:.2f} ms")
            
            self.total_tests += 1
            if response_time < 1000:  # Less than 1 second
                self.print_success("Response time is acceptable (< 1000ms)")
            else:
                self.print_failure(f"Response time is too slow ({response_time:.2f} ms)")
                
        except requests.exceptions.RequestException as e:
            self.print_failure(f"Response time check - Connection error: {str(e)}")
            self.total_tests += 1
    
    def run_all_tests(self):
        """Run all tests"""
        self.print_header("CLIENT SERVICE TEST SUITE")
        
        print(f"{Colors.BLUE}Testing Client Service at: {self.base_url}{Colors.RESET}\n")
        
        # Check if service is reachable
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            print(f"{Colors.GREEN}✓ Client Service is reachable{Colors.RESET}\n")
        except requests.exceptions.RequestException:
            print(f"{Colors.RED}✗ Client Service is not reachable at {self.base_url}{Colors.RESET}")
            print(f"{Colors.RED}  Please make sure the service is running.{Colors.RESET}\n")
            return
        
        # Run all tests
        self.test_health_check()
        print()
        
        self.test_root_endpoint()
        print()
        
        self.test_get_all_users()
        print()
        
        self.test_create_user()
        print()
        
        self.test_get_specific_user()
        print()
        
        self.test_update_user()
        print()
        
        self.test_delete_user()
        print()
        
        self.test_get_nonexistent_user()
        print()
        
        self.test_create_user_missing_fields()
        print()
        
        self.test_create_duplicate_user()
        print()
        
        self.test_update_nonexistent_user()
        print()
        
        self.test_delete_nonexistent_user()
        print()
        
        self.test_invalid_endpoint()
        print()
        
        self.test_response_time()
        print()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        print(f"Total Tests:  {self.total_tests}")
        print(f"{Colors.GREEN}Passed:       {self.passed_tests}{Colors.RESET}")
        print(f"{Colors.RED}Failed:       {self.failed_tests}{Colors.RESET}")
        
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"\nPass Rate:    {pass_rate:.1f}%")
        
        if self.failed_tests == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! 🎉{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Please review the output above.{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Client Service')
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8080',
        help='Base URL of the client service (default: http://localhost:8080)'
    )
    
    args = parser.parse_args()
    
    tester = ClientServiceTester(base_url=args.url)
    tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if tester.failed_tests == 0 else 1)


if __name__ == '__main__':
    main()