from flask import Flask, jsonify, request
import json
import os
from models import Users
from fault_injector import FaultInjector

app = Flask(__name__)

# Initialize fault injector
# Configure failure rates via environment variables or defaults
fault_injector = FaultInjector(
    delay_rate=0.2,      # 20% chance of delay
    error_rate=0.1,      # 10% chance of error
    timeout_rate=0.05,   # 5% chance of timeout
    min_delay=0.5,       # Minimum 0.5s delay
    max_delay=3.0        # Maximum 3s delay
)

def load_initial_data():
    """
    Load initial user data from users.json file.
    This simulates a pre-populated database for testing purposes.
    """
    try:
        # Check if users.json exists
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Load main users list
                if 'users' in data:
                    for user_data in data['users']:
                        Users(
                            name=user_data['name'],
                            id=user_data['id'],
                            email=user_data['email']
                        )
                    print(f"[Initialization] Loaded {len(data['users'])} users from users.json")
                else:
                    print("[Initialization] No 'users' key found in users.json")
        else:
            print("[Initialization] users.json not found - starting with empty user list")
    
    except Exception as e:
        print(f"[Initialization] Error loading users.json: {str(e)}")

# Load initial data when app starts
load_initial_data()


# ==================== Health Check Endpoints ====================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Kubernetes liveness/readiness probes.
    Returns 200 OK if service is healthy.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'backend-service',
        'user_count': len(Users.user_lists)
    }), 200


@app.route('/fault-injector/status', methods=['GET'])
def get_fault_injector_status():
    """
    Get current fault injector configuration.
    Useful for debugging and testing.
    """
    return jsonify({
        'success': True,
        'data': fault_injector.get_status(),
        'message': 'Fault injector status retrieved'
    }), 200


@app.route('/fault-injector/config', methods=['POST'])
def configure_fault_injector():
    """
    Dynamically configure fault injection rates at runtime.
    
    Request body example:
    {
        "delay_rate": 0.3,
        "error_rate": 0.15,
        "timeout_rate": 0.05
    }
    """
    try:
        data = request.get_json()
        
        if 'delay_rate' in data:
            fault_injector.set_failure_rate(delay_rate=float(data['delay_rate']))
        
        if 'error_rate' in data:
            fault_injector.set_failure_rate(error_rate=float(data['error_rate']))
        
        if 'timeout_rate' in data:
            fault_injector.set_failure_rate(timeout_rate=float(data['timeout_rate']))
        
        return jsonify({
            'success': True,
            'data': fault_injector.get_status(),
            'message': 'Fault injector configuration updated'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Configuration error: {str(e)}'
        }), 400


# ==================== User CRUD Endpoints ====================

@app.route('/api/users', methods=['GET'])
@fault_injector.inject_faults
def get_users():
    """
    Retrieve all users from the system.
    Fault injection: May experience delays or errors.
    """
    try:
        users = Users.show_users()
        return jsonify({
            'success': True,
            'data': users,
            'count': len(users),
            'message': 'Users retrieved successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['GET'])
@fault_injector.inject_faults
def get_user(user_id):
    """
    Retrieve a specific user by ID.
    Fault injection: May experience delays or errors.
    
    Args:
        user_id: User ID to retrieve
    """
    try:
        user = Users.get_user(user_id)
        if user:
            return jsonify({
                'success': True,
                'data': user,
                'message': 'User retrieved successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'User with ID {user_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users', methods=['POST'])
@fault_injector.inject_faults
def create_user():
    """
    Create a new user.
    Fault injection: May experience delays or errors.
    
    Request body example:
    {
        "name": "John Doe",
        "id": 100,
        "email": "john.doe@example.com"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(key in data for key in ['name', 'id', 'email']):
            return jsonify({
                'success': False,
                'message': 'Missing required fields: name, id, email'
            }), 400
        
        # Check if user already exists
        if Users.user_exists(data['id']):
            return jsonify({
                'success': False,
                'message': f'User with ID {data["id"]} already exists'
            }), 409
        
        # Create new user
        new_user = Users(data['name'], data['id'], data['email'])
        return jsonify({
            'success': True,
            'data': {
                'id': new_user.id,
                'name': new_user.name,
                'email': new_user.email
            },
            'message': 'User created successfully'
        }), 201
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@fault_injector.inject_faults
def update_user(user_id):
    """
    Update an existing user.
    Fault injection: May experience delays or errors.
    
    Args:
        user_id: User ID to update
    
    Request body example:
    {
        "name": "Jane Doe",
        "email": "jane.doe@example.com"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Check if user exists
        if not Users.user_exists(user_id):
            return jsonify({
                'success': False,
                'message': f'User with ID {user_id} not found'
            }), 404
        
        # Update user
        updated_user = Users.update_user(user_id, data)
        
        return jsonify({
            'success': True,
            'data': updated_user,
            'message': 'User updated successfully'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@fault_injector.inject_faults
def delete_user(user_id):
    """
    Delete a user.
    Fault injection: May experience delays or errors.
    
    Args:
        user_id: User ID to delete
    """
    try:
        # Check if user exists
        if not Users.user_exists(user_id):
            return jsonify({
                'success': False,
                'message': f'User with ID {user_id} not found'
            }), 404
        
        # Delete user
        deleted_user = Users.delete_user(user_id)
        
        return jsonify({
            'success': True,
            'data': deleted_user,
            'message': 'User deleted successfully'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== Application Startup ====================

if __name__ == '__main__':
    print("=" * 60)
    print("Backend Service Starting...")
    print("=" * 60)
    print(f"Total Users Loaded: {len(Users.user_lists)}")
    print(f"Fault Injection Enabled: Yes")
    print(f"Port: 5000")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0', 
        port=5000,
        threaded=True, 
        debug=False
    )