from flask import Flask, jsonify, request
from models import Users

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    # Return list of all users
    try:
        users = Users.show_users()
        return jsonify({
            'success': True,
            'data': users,
            'message': 'Users retrieved successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Return specific user
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
                'message': 'User not found.'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    # Create new user from request data
    try:
        data = request.get_json()
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
def update_user(user_id):
    # Update existing user
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
                'message': 'User not found'
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
def delete_user(user_id):
    # Delete user
    try:
        # Check if user exists
        if not Users.user_exists(user_id):
            return jsonify({
                'success': False,
                'message': 'User not found'
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

if __name__ == '__main__':
    app.run(debug=True)