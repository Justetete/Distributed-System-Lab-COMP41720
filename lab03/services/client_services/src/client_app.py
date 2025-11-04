from flask import Flask, jsonify, request
import logging
from config import config
from backend_client import backend_client


# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for the client service
    
    Also checks backend service connectivity
    
    Returns:
        JSON response with health status
    """
    logger.info("Health check requested")
    
    # Check backend health
    backend_health = backend_client.health_check()
    
    return jsonify({
        'status': 'healthy',
        'service': 'client-service',
        'backend': {
            'url': config.BACKEND_URL,
            'connected': backend_health['healthy'],
            'status_code': backend_health['status_code']
        }
    }), 200


@app.route('/client/users', methods=['GET'])
def get_all_users():
    """
    Get all users from backend service
    
    Returns:
        JSON response with list of users
    """
    logger.info("GET /client/users - Fetching all users")
    
    # Call backend service
    response = backend_client.get_users()
    
    # Return response with appropriate status code
    return jsonify(response['data']), response['status_code']


@app.route('/client/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a specific user by ID from backend service
    
    Args:
        user_id: ID of the user to retrieve
    
    Returns:
        JSON response with user data or error
    """
    logger.info(f"GET /client/users/{user_id} - Fetching user")
    
    # Call backend service
    response = backend_client.get_user(user_id)
    
    # Return response with appropriate status code
    return jsonify(response['data']), response['status_code']


@app.route('/client/users', methods=['POST'])
def create_user():
    """
    Create a new user via backend service
    
    Expected JSON body:
        {
            "name": "string",
            "id": integer,
            "email": "string"
        }
    
    Returns:
        JSON response with created user data
    """
    logger.info("POST /client/users - Creating new user")
    
    # Get JSON data from request
    try:
        user_data = request.get_json()
        
        if not user_data:
            logger.warning("No data provided in request")
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'id', 'email']
        missing_fields = [field for field in required_fields if field not in user_data]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Call backend service
        response = backend_client.create_user(user_data)
        
        # Return response with appropriate status code
        return jsonify(response['data']), response['status_code']
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500


@app.route('/client/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update an existing user via backend service
    
    Args:
        user_id: ID of the user to update
    
    Expected JSON body:
        {
            "name": "string" (optional),
            "email": "string" (optional)
        }
    
    Returns:
        JSON response with updated user data
    """
    logger.info(f"PUT /client/users/{user_id} - Updating user")
    
    # Get JSON data from request
    try:
        user_data = request.get_json()
        
        if not user_data:
            logger.warning("No data provided in request")
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Call backend service
        response = backend_client.update_user(user_id, user_data)
        
        # Return response with appropriate status code
        return jsonify(response['data']), response['status_code']
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500


@app.route('/client/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user via backend service
    
    Args:
        user_id: ID of the user to delete
    
    Returns:
        JSON response with deleted user data
    """
    logger.info(f"DELETE /client/users/{user_id} - Deleting user")
    
    # Call backend service
    response = backend_client.delete_user(user_id)
    
    # Return response with appropriate status code
    return jsonify(response['data']), response['status_code']


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint - provides service information
    
    Returns:
        JSON response with service information
    """
    return jsonify({
        'service': 'client-service',
        'version': '1.0.0',
        'description': 'Client service for distributed systems lab',
        'endpoints': {
            'health': '/health',
            'get_all_users': '/client/users [GET]',
            'get_user': '/client/users/<id> [GET]',
            'create_user': '/client/users [POST]',
            'update_user': '/client/users/<id> [PUT]',
            'delete_user': '/client/users/<id> [DELETE]'
        },
        'backend_url': config.BACKEND_URL
    }), 200


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors
    
    Returns:
        JSON error response
    """
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors
    
    Returns:
        JSON error response
    """
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    logger.info("Starting Client Service")
    logger.info(f"Configuration: {config.display_config()}")
    
    app.run(
        host=config.CLIENT_HOST,
        port=config.CLIENT_PORT,
        threaded=True,
        debug=config.DEBUG
    )