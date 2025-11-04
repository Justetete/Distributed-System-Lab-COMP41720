from flask import Flask, jsonify, request
from models import Users
from fault_injector import fault_injector
import json
import os
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


def load_initial_users():
    """
    Load initial users from users.json file
    
    This function reads the users.json file and populates the
    Users.user_lists with initial data for testing purposes.
    """
    try:
        # Check if users.json exists
        if not os.path.exists('users.json'):
            logger.warning("users.json not found, skipping initial data load")
            return
        
        with open('users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load main users list
        users_list = data.get('users', [])
        loaded_count = 0
        
        for user_data in users_list:
            # Check if user already exists
            if not Users.user_exists(user_data['id']):
                Users(
                    name=user_data['name'],
                    id=user_data['id'],
                    email=user_data['email']
                )
                loaded_count += 1
        
        logger.info(f"✅ Loaded {loaded_count} initial users from users.json")
        logger.info(f"📊 Total users in system: {len(Users.user_lists)}")
        
    except Exception as e:
        logger.error(f"❌ Error loading initial users: {str(e)}")


# ============================================================================
# Health Check & Status Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns service health status and configuration information
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'backend-service',
        'user_count': len(Users.user_lists),
        'fault_injection': fault_injector.get_config()
    }), 200


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get detailed service status
    
    Returns:
        JSON response with detailed status information
    """
    return jsonify({
        'success': True,
        'data': {
            'service': 'backend-service',
            'version': '2.0.0',
            'user_count': len(Users.user_lists),
            'fault_injection': fault_injector.get_config()
        },
        'message': 'Service status retrieved successfully'
    }), 200


# ============================================================================
# Fault Injection Control Endpoints (for testing)
# ============================================================================

@app.route('/api/fault-injection/enable', methods=['POST'])
def enable_fault_injection():
    """Enable fault injection"""
    fault_injector.enable()
    return jsonify({
        'success': True,
        'message': 'Fault injection enabled',
        'config': fault_injector.get_config()
    }), 200


@app.route('/api/fault-injection/disable', methods=['POST'])
def disable_fault_injection():
    """Disable fault injection"""
    fault_injector.disable()
    return jsonify({
        'success': True,
        'message': 'Fault injection disabled',
        'config': fault_injector.get_config()
    }), 200


@app.route('/api/fault-injection/config', methods=['GET'])
def get_fault_config():
    """Get current fault injection configuration"""
    return jsonify({
        'success': True,
        'data': fault_injector.get_config(),
        'message': 'Fault injection configuration retrieved'
    }), 200


@app.route('/api/fault-injection/config', methods=['PUT'])
def update_fault_config():
    """
    Update fault injection configuration
    
    Request body:
        {
            "delay_rate": 0.3,
            "error_rate": 0.2,
            "timeout_rate": 0.1
        }
    """
    data = request.get_json()
    
    if 'delay_rate' in data:
        fault_injector.set_rates(delay_rate=data['delay_rate'])
    
    if 'error_rate' in data:
        fault_injector.set_rates(error_rate=data['error_rate'])
    
    if 'timeout_rate' in data:
        fault_injector.set_rates(timeout_rate=data['timeout_rate'])
    
    return jsonify({
        'success': True,
        'data': fault_injector.get_config(),
        'message': 'Fault injection configuration updated'
    }), 200


# ============================================================================
# Simplified Control Endpoints (as suggested by instructor)
# ============================================================================

@app.route('/configfailure', methods=['POST'])
def config_failure():
    """
    Configure failure rate (simplified endpoint as suggested by instructor)
    
    Request body:
        {
            "failure_rate": 0.5
        }
    
    This sets the probability of returning 500 errors.
    """
    try:
        data = request.get_json()
        
        if not data or 'failure_rate' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: failure_rate'
            }), 400
        
        failure_rate = float(data['failure_rate'])
        
        # Validate range
        if not 0.0 <= failure_rate <= 1.0:
            return jsonify({
                'success': False,
                'message': 'failure_rate must be between 0.0 and 1.0'
            }), 400
        
        # Update error rate
        fault_injector.set_rates(error_rate=failure_rate)
        
        logger.info(f"✅ Failure rate configured to {failure_rate * 100}%")
        
        return jsonify({
            'success': True,
            'message': f'Failure rate set to {failure_rate}',
            'config': {
                'failure_rate': failure_rate,
                'current_config': fault_injector.get_config()
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Invalid failure_rate value: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error configuring failure: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/configlatency', methods=['POST'])
def config_latency():
    """
    Configure latency injection (simplified endpoint as suggested by instructor)
    
    Request body:
        {
            "delay_ms": 2000,
            "delay_rate": 0.5
        }
    
    This sets:
    - delay_ms: The delay in milliseconds (will be converted to seconds)
    - delay_rate: The probability of injecting this delay
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Get delay_ms (optional, defaults to current value)
        delay_ms = data.get('delay_ms')
        delay_rate = data.get('delay_rate')
        
        if delay_ms is None and delay_rate is None:
            return jsonify({
                'success': False,
                'message': 'At least one of delay_ms or delay_rate is required'
            }), 400
        
        # Update delay duration if provided
        if delay_ms is not None:
            delay_seconds = float(delay_ms) / 1000.0
            
            if delay_seconds < 0:
                return jsonify({
                    'success': False,
                    'message': 'delay_ms must be non-negative'
                }), 400
            
            # Set both min and max delay to this value for consistent behavior
            fault_injector.min_delay = delay_seconds
            fault_injector.max_delay = delay_seconds
            logger.info(f"✅ Delay duration configured to {delay_ms}ms ({delay_seconds}s)")
        
        # Update delay rate if provided
        if delay_rate is not None:
            delay_rate_float = float(delay_rate)
            
            if not 0.0 <= delay_rate_float <= 1.0:
                return jsonify({
                    'success': False,
                    'message': 'delay_rate must be between 0.0 and 1.0'
                }), 400
            
            fault_injector.set_rates(delay_rate=delay_rate_float)
            logger.info(f"✅ Delay rate configured to {delay_rate_float * 100}%")
        
        return jsonify({
            'success': True,
            'message': 'Latency configuration updated',
            'config': {
                'delay_ms': fault_injector.min_delay * 1000,
                'delay_rate': fault_injector.delay_rate,
                'current_config': fault_injector.get_config()
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Invalid parameter value: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error configuring latency: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================================================
# User CRUD Endpoints (with fault injection)
# ============================================================================

@app.route('/api/users', methods=['GET'])
@fault_injector.inject_faults
def get_users():
    """
    Get all users
    
    This endpoint has fault injection enabled, so it may:
    - Return normally
    - Be delayed (slow response)
    - Return 500 error
    - Timeout
    
    Returns:
        JSON response with list of users
    """
    try:
        logger.info("GET /api/users - Fetching all users")
        users = Users.show_users()
        
        return jsonify({
            'success': True,
            'data': users,
            'message': 'Users retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_users: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['GET'])
@fault_injector.inject_faults
def get_user(user_id):
    """
    Get a specific user by ID
    
    Args:
        user_id: ID of the user to retrieve
    
    Returns:
        JSON response with user data or 404
    """
    try:
        logger.info(f"GET /api/users/{user_id} - Fetching user")
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
                'message': 'User not found.'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in get_user: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users', methods=['POST'])
@fault_injector.inject_faults
def create_user():
    """
    Create a new user
    
    Request body:
        {
            "name": "string",
            "id": integer,
            "email": "string"
        }
    
    Returns:
        JSON response with created user data
    """
    try:
        logger.info("POST /api/users - Creating new user")
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
                'message': 'User with this ID already exists'
            }), 409
        
        # Create new user
        new_user = Users(data['name'], data['id'], data['email'])
        logger.info(f"User created: {new_user.name} (ID: {new_user.id})")
        
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
        logger.error(f"Error in create_user: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@fault_injector.inject_faults
def update_user(user_id):
    """
    Update an existing user
    
    Args:
        user_id: ID of the user to update
    
    Request body:
        {
            "name": "string" (optional),
            "email": "string" (optional)
        }
    
    Returns:
        JSON response with updated user data
    """
    try:
        logger.info(f"PUT /api/users/{user_id} - Updating user")
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
                'message': 'User not found'
            }), 404
        
        # Update user
        updated_user = Users.update_user(user_id, data)
        logger.info(f"User updated: {updated_user['name']} (ID: {user_id})")
        
        return jsonify({
            'success': True,
            'data': updated_user,
            'message': 'User updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in update_user: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@fault_injector.inject_faults
def delete_user(user_id):
    """
    Delete a user
    
    Args:
        user_id: ID of the user to delete
    
    Returns:
        JSON response with deleted user data
    """
    try:
        logger.info(f"DELETE /api/users/{user_id} - Deleting user")
        
        # Check if user exists
        if not Users.user_exists(user_id):
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Delete user
        deleted_user = Users.delete_user(user_id)
        logger.info(f"User deleted: {deleted_user['name']} (ID: {user_id})")
        
        return jsonify({
            'success': True,
            'data': deleted_user,
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in delete_user: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================================================
# Application Startup
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Starting Backend Service with Fault Injection")
    logger.info("=" * 70)
    
    # Load initial users
    load_initial_users()
    
    # Display configuration
    logger.info("\n📋 Fault Injection Configuration:")
    config = fault_injector.get_config()
    logger.info(f"  Enabled: {config['enabled']}")
    logger.info(f"  Delay Rate: {config['delay_rate'] * 100}%")
    logger.info(f"  Error Rate: {config['error_rate'] * 100}%")
    logger.info(f"  Timeout Rate: {config['timeout_rate'] * 100}%")
    logger.info(f"  Delay Range: {config['min_delay']}s - {config['max_delay']}s")
    
    logger.info("\n🌐 Available Endpoints:")
    logger.info("  GET    /health")
    logger.info("  GET    /api/status")
    logger.info("  GET    /api/users")
    logger.info("  GET    /api/users/<id>")
    logger.info("  POST   /api/users")
    logger.info("  PUT    /api/users/<id>")
    logger.info("  DELETE /api/users/<id>")
    logger.info("  POST   /api/fault-injection/enable")
    logger.info("  POST   /api/fault-injection/disable")
    logger.info("  GET    /api/fault-injection/config")
    logger.info("  PUT    /api/fault-injection/config")
    
    logger.info("\n" + "=" * 70)
    logger.info("🚀 Backend Service starting on http://0.0.0.0:5000")
    logger.info("=" * 70 + "\n")
    
    # Start Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,
        debug=False
    )