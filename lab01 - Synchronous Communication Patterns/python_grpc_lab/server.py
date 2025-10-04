import grpc
from concurrent import futures
import sys
import os

# Add the generated directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'generated'))

import user_service_pb2
import user_service_pb2_grpc

class UserService(user_service_pb2_grpc.UserServiceServicer):
    def __init__(self):
        # In-memory storage for users (similar to your REST API)
        self.users = {}
    
    def GetUser(self, request, context):
        """Get a specific user by ID"""
        try:
            user_id = request.id
            
            if user_id in self.users:
                user_data = self.users[user_id]
                user = user_service_pb2.User(
                    id=user_data['id'],
                    name=user_data['name'],
                    email=user_data['email']
                )
                return user_service_pb2.GetUserResponse(
                    success=True,
                    message="User retrieved successfully",
                    user=user
                )
            else:
                return user_service_pb2.GetUserResponse(
                    success=False,
                    message="User not found",
                    user=user_service_pb2.User()  # Empty user
                )
        except Exception as e:
            return user_service_pb2.GetUserResponse(
                success=False,
                message=f"Error: {str(e)}",
                user=user_service_pb2.User()
            )
    
    def CreateUser(self, request, context):
        """Create a new user"""
        try:
            user_id = request.id
            
            # Check if user already exists
            if user_id in self.users:
                return user_service_pb2.CreateUserResponse(
                    success=False,
                    message="User with this ID already exists",
                    user=user_service_pb2.User()
                )
            
            # Validate required fields
            if not request.name or not request.email:
                return user_service_pb2.CreateUserResponse(
                    success=False,
                    message="Name and email are required",
                    user=user_service_pb2.User()
                )
            
            # Create user
            user_data = {
                'id': user_id,
                'name': request.name,
                'email': request.email
            }
            self.users[user_id] = user_data
            
            user = user_service_pb2.User(
                id=user_data['id'],
                name=user_data['name'],
                email=user_data['email']
            )
            
            return user_service_pb2.CreateUserResponse(
                success=True,
                message="User created successfully",
                user=user
            )
            
        except Exception as e:
            return user_service_pb2.CreateUserResponse(
                success=False,
                message=f"Error: {str(e)}",
                user=user_service_pb2.User()
            )
    
    def UpdateUser(self, request, context):
        """Update an existing user"""
        try:
            user_id = request.id
            
            if user_id not in self.users:
                return user_service_pb2.UpdateUserResponse(
                    success=False,
                    message="User not found",
                    user=user_service_pb2.User()
                )
            
            # Update user data
            user_data = self.users[user_id]
            if request.name and request.name.strip():
                user_data['name'] = request.name
            if request.email and request.email.strip():
                user_data['email'] = request.email
            
            user = user_service_pb2.User(
                id=user_data['id'],
                name=user_data['name'],
                email=user_data['email']
            )
            
            return user_service_pb2.UpdateUserResponse(
                success=True,
                message="User updated successfully",
                user=user
            )
            
        except Exception as e:
            return user_service_pb2.UpdateUserResponse(
                success=False,
                message=f"Error: {str(e)}",
                user=user_service_pb2.User()
            )
    
    def DeleteUser(self, request, context):
        """Delete a user"""
        try:
            user_id = request.id
            
            if user_id not in self.users:
                return user_service_pb2.DeleteUserResponse(
                    success=False,
                    message="User not found",
                    user=user_service_pb2.User()
                )
            
            # Get user data before deletion
            user_data = self.users[user_id]
            user = user_service_pb2.User(
                id=user_data['id'],
                name=user_data['name'],
                email=user_data['email']
            )
            
            # Delete user
            del self.users[user_id]
            
            return user_service_pb2.DeleteUserResponse(
                success=True,
                message="User deleted successfully",
                user=user
            )
            
        except Exception as e:
            return user_service_pb2.DeleteUserResponse(
                success=False,
                message=f"Error: {str(e)}",
                user=user_service_pb2.User()
            )
    
    def GetAllUsers(self, request, context):
        """Get all users"""
        try:
            users = []
            for user_data in self.users.values():
                user = user_service_pb2.User(
                    id=user_data['id'],
                    name=user_data['name'],
                    email=user_data['email']
                )
                users.append(user)
            
            return user_service_pb2.GetAllUsersResponse(
                success=True,
                message="Users retrieved successfully",
                users=users
            )
            
        except Exception as e:
            return user_service_pb2.GetAllUsersResponse(
                success=False,
                message=f"Error: {str(e)}",
                users=[]
            )

def serve():
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    
    # Add insecure port
    server.add_insecure_port('[::]:50051')
    
    print("Starting gRPC server on port 50051...")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop(0)

if __name__ == '__main__':
    serve()