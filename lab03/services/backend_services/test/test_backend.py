import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_ID = 9999

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(test_name: str, success: bool, message: str = ""):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"     {message}")

def make_request(method: str, endpoint: str, data: Dict = None) -> tuple:
    """Make HTTP request and return response and success status"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return None, False
        
        return response, True
    except requests.exceptions.Timeout:
        print(f"     ⚠ Request timeout (might be fault injection)")
        return None, False
    except requests.exceptions.RequestException as e:
        print(f"     ⚠ Request error: {str(e)}")
        return None, False

def test_health_check():
    """Test health check endpoint"""
    print_section("Health Check Tests")
    
    response, success = make_request("GET", "/health")
    if success and response.status_code == 200:
        data = response.json()
        print_result("Health check endpoint", True, 
                    f"Status: {data.get('status')}, Users: {data.get('user_count')}")
    else:
        print_result("Health check endpoint", False)

def test_fault_injector_status():
    """Test fault injector status endpoint"""
    print_section("Fault Injector Tests")
    
    response, success = make_request("GET", "/fault-injector/status")
    if success and response.status_code == 200:
        data = response.json()
        config = data.get('data', {})
        print_result("Get fault injector status", True)
        print(f"     Delay Rate: {config.get('delay_rate') * 100}%")
        print(f"     Error Rate: {config.get('error_rate') * 100}%")
        print(f"     Timeout Rate: {config.get('timeout_rate') * 100}%")
    else:
        print_result("Get fault injector status", False)

def test_configure_fault_injector():
    """Test dynamic fault injector configuration"""
    config_data = {
        "delay_rate": 0.5,
        "error_rate": 0.2,
        "timeout_rate": 0.1
    }
    
    response, success = make_request("POST", "/fault-injector/config", config_data)
    if success and response.status_code == 200:
        print_result("Configure fault injector", True, 
                    "Rates updated successfully")
    else:
        print_result("Configure fault injector", False)
    
    # Reset to lower rates for remaining tests
    reset_data = {
        "delay_rate": 0.1,
        "error_rate": 0.05,
        "timeout_rate": 0.0
    }
    make_request("POST", "/fault-injector/config", reset_data)

def test_get_all_users():
    """Test getting all users"""
    print_section("User CRUD Tests")
    
    response, success = make_request("GET", "/api/users")
    if success and response.status_code == 200:
        data = response.json()
        user_count = data.get('count', 0)
        print_result("Get all users", True, 
                    f"Retrieved {user_count} users")
    else:
        print_result("Get all users", False)

def test_get_single_user():
    """Test getting a single user"""
    response, success = make_request("GET", "/api/users/1")
    if success and response.status_code == 200:
        data = response.json()
        user = data.get('data', {})
        print_result("Get single user", True, 
                    f"User: {user.get('name')} ({user.get('email')})")
    else:
        print_result("Get single user", False)

def test_get_nonexistent_user():
    """Test getting a non-existent user"""
    response, success = make_request("GET", f"/api/users/{TEST_USER_ID}")
    if success and response.status_code == 404:
        print_result("Get non-existent user (404)", True)
    else:
        print_result("Get non-existent user (404)", False)

def test_create_user():
    """Test creating a new user"""
    user_data = {
        "name": "Test User",
        "id": TEST_USER_ID,
        "email": "test.user@lab3.com"
    }
    
    response, success = make_request("POST", "/api/users", user_data)
    if success and response.status_code == 201:
        print_result("Create user", True, 
                    f"Created user ID {TEST_USER_ID}")
        return True
    else:
        print_result("Create user", False)
        return False

def test_create_duplicate_user():
    """Test creating a duplicate user (should fail)"""
    user_data = {
        "name": "Duplicate User",
        "id": TEST_USER_ID,
        "email": "duplicate@lab3.com"
    }
    
    response, success = make_request("POST", "/api/users", user_data)
    if success and response.status_code == 409:
        print_result("Create duplicate user (409)", True)
    else:
        print_result("Create duplicate user (409)", False)

def test_create_user_missing_fields():
    """Test creating user with missing fields"""
    user_data = {
        "name": "Incomplete User"
        # Missing 'id' and 'email'
    }
    
    response, success = make_request("POST", "/api/users", user_data)
    if success and response.status_code == 400:
        print_result("Create user with missing fields (400)", True)
    else:
        print_result("Create user with missing fields (400)", False)

def test_update_user():
    """Test updating an existing user"""
    update_data = {
        "name": "Updated Test User",
        "email": "updated.test@lab3.com"
    }
    
    response, success = make_request("PUT", f"/api/users/{TEST_USER_ID}", update_data)
    if success and response.status_code == 200:
        data = response.json()
        user = data.get('data', {})
        print_result("Update user", True, 
                    f"Updated to: {user.get('name')} ({user.get('email')})")
    else:
        print_result("Update user", False)

def test_update_nonexistent_user():
    """Test updating a non-existent user"""
    update_data = {
        "name": "Ghost User"
    }
    
    response, success = make_request("PUT", f"/api/users/88888", update_data)
    if success and response.status_code == 404:
        print_result("Update non-existent user (404)", True)
    else:
        print_result("Update non-existent user (404)", False)

def test_delete_user():
    """Test deleting a user"""
    response, success = make_request("DELETE", f"/api/users/{TEST_USER_ID}")
    if success and response.status_code == 200:
        print_result("Delete user", True, 
                    f"Deleted user ID {TEST_USER_ID}")
    else:
        print_result("Delete user", False)

def test_delete_nonexistent_user():
    """Test deleting a non-existent user"""
    response, success = make_request("DELETE", f"/api/users/{TEST_USER_ID}")
    if success and response.status_code == 404:
        print_result("Delete non-existent user (404)", True)
    else:
        print_result("Delete non-existent user (404)", False)

def test_fault_injection_behavior():
    """Test fault injection by making multiple requests"""
    print_section("Fault Injection Behavior Test")
    
    # Configure higher fault rates
    config_data = {
        "delay_rate": 0.4,
        "error_rate": 0.3,
        "timeout_rate": 0.0  # Avoid timeouts for this test
    }
    make_request("POST", "/fault-injector/config", config_data)
    
    print("Making 10 requests to observe fault injection...")
    delays = 0
    errors = 0
    successes = 0
    
    for i in range(10):
        start_time = time.time()
        response, success = make_request("GET", "/api/users")
        elapsed = time.time() - start_time
        
        if success:
            if response.status_code == 500:
                errors += 1
                print(f"  Request {i+1}: ✗ ERROR 500")
            elif response.status_code == 200:
                if elapsed > 1.0:
                    delays += 1
                    print(f"  Request {i+1}: ⏱ DELAY ({elapsed:.2f}s)")
                else:
                    successes += 1
                    print(f"  Request {i+1}: ✓ SUCCESS ({elapsed:.2f}s)")
        else:
            print(f"  Request {i+1}: ⚠ TIMEOUT/ERROR")
    
    print(f"\nResults: {successes} successes, {delays} delays, {errors} errors")
    
    # Reset fault rates
    reset_data = {
        "delay_rate": 0.2,
        "error_rate": 0.1,
        "timeout_rate": 0.05
    }
    make_request("POST", "/fault-injector/config", reset_data)

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  BACKEND SERVICE TEST SUITE")
    print("  Target: " + BASE_URL)
    print("=" * 60)
    
    # Check if service is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ Backend service is not responding correctly!")
            print("   Please start the service first: python app.py")
            return
    except:
        print("\n❌ Cannot connect to backend service!")
        print("   Please start the service first: python app.py")
        return
    
    # Run tests
    test_health_check()
    test_fault_injector_status()
    test_configure_fault_injector()
    test_get_all_users()
    test_get_single_user()
    test_get_nonexistent_user()
    
    # Create user for CRUD tests
    if test_create_user():
        test_create_duplicate_user()
        test_create_user_missing_fields()
        test_update_user()
        test_update_nonexistent_user()
        test_delete_user()
        test_delete_nonexistent_user()
    
    # Test fault injection behavior
    test_fault_injection_behavior()
    
    print("\n" + "=" * 60)
    print("  TEST SUITE COMPLETED")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()