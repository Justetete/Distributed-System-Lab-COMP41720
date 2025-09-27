import grpc
import sys
import os

# Add the generated directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'generated'))

import user_service_pb2
import user_service_pb2_grpc

def create_user(stub, name, user_id, email):
    """Create a new user"""
    print(f"\n--- Creating User ---")
    print(f"Name: {name}, ID: {user_id}, Email: {email}")
    
    request = user_service_pb2.CreateUserRequest(
        name=name,
        id=user_id,
        email=email
    )
    
    try:
        response = stub.CreateUser(request)
        print(f"Success: {response.success}")
        print(f"Message: {response.message}")
        if response.success:
            user = response.user
            print(f"Created User - ID: {user.id}, Name: {user.name}, Email: {user.email}")
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")

def get_user(stub, user_id):
    """Get a specific user"""
    print(f"\n--- Getting User {user_id} ---")
    
    request = user_service_pb2.GetUserRequest(id=user_id)
    
    try:
        response = stub.GetUser(request)
        print(f"Success: {response.success}")
        print(f"Message: {response.message}")
        if response.success:
            user = response.user
            print(f"User - ID: {user.id}, Name: {user.name}, Email: {user.email}")
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")

def get_all_users(stub):
    """Get all users"""
    print(f"\n--- Getting All Users ---")
    
    request = user_service_pb2.GetAllUsersRequest()
    
    try:
        response = stub.GetAllUsers(request)
        print(f"Success: {response.success}")
        print(f"Message: {response.message}")
        if response.success:
            print(f"Total users: {len(response.users)}")
            for user in response.users:
                print(f"  User - ID: {user.id}, Name: {user.name}, Email: {user.email}")
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")

def update_user(stub, user_id, name=None, email=None):
    """Update a user"""
    print(f"\n--- Updating User {user_id} ---")
    
    request = user_service_pb2.UpdateUserRequest(
        id=user_id,
        name=name or "",
        email=email or ""
    )
    
    try:
        response = stub.UpdateUser(request)
        print(f"Success: {response.success}")
        print(f"Message: {response.message}")
        if response.success:
            user = response.user
            print(f"Updated User - ID: {user.id}, Name: {user.name}, Email: {user.email}")
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")

def delete_user(stub, user_id):
    """Delete a user"""
    print(f"\n--- Deleting User {user_id} ---")
    
    request = user_service_pb2.DeleteUserRequest(id=user_id)
    
    try:
        response = stub.DeleteUser(request)
        print(f"Success: {response.success}")
        print(f"Message: {response.message}")
        if response.success:
            user = response.user
            print(f"Deleted User - ID: {user.id}, Name: {user.name}, Email: {user.email}")
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")

def interactive_menu(stub):
    """Interactive menu for testing the gRPC service"""
    while True:
        print("\n" + "="*50)
        print("gRPC User Service Client")
        print("="*50)
        print("1. Create User")
        print("2. Get User")
        print("3. Get All Users")
        print("4. Update User")
        print("5. Delete User")
        print("6. Run Demo")
        print("0. Exit")
        print("-"*50)
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            name = input("Enter name: ").strip()
            user_id = int(input("Enter ID: ").strip())
            email = input("Enter email: ").strip()
            create_user(stub, name, user_id, email)
        
        elif choice == '2':
            user_id = int(input("Enter user ID: ").strip())
            get_user(stub, user_id)
        
        elif choice == '3':
            get_all_users(stub)
        
        elif choice == '4':
            user_id = int(input("Enter user ID to update: ").strip())
            name = input("Enter new name (or press Enter to skip): ").strip()
            email = input("Enter new email (or press Enter to skip): ").strip()
            update_user(stub, user_id, name if name else None, email if email else None)
        
        elif choice == '5':
            user_id = int(input("Enter user ID to delete: ").strip())
            delete_user(stub, user_id)
        
        elif choice == '6':
            run_demo(stub)
        
        elif choice == '0':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

def run_demo(stub):
    """Run a demo with sample data"""
    print("\n" + "="*50)
    print("RUNNING DEMO")
    print("="*50)
    
    # Create some users
    create_user(stub, "Alice Johnson", 1, "alice.johnson@email.com")
    create_user(stub, "Bob Smith", 2, "bob.smith@email.com")
    create_user(stub, "Charlie Brown", 3, "charlie.brown@email.com")
    
    # Get all users
    get_all_users(stub)
    
    # Get specific user
    get_user(stub, 1)
    
    # Update user
    update_user(stub, 1, name="Alice Johnson Updated")
    
    # Get updated user
    get_user(stub, 1)
    
    # Delete user
    delete_user(stub, 3)
    
    # Get all users again
    get_all_users(stub)
    
    print("\n" + "="*50)
    print("DEMO COMPLETED")
    print("="*50)

def main():
    """Main function"""
    # Create a channel to the server
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = user_service_pb2_grpc.UserServiceStub(channel)
        
        print("Connected to gRPC server at localhost:50051")
        
        # Check if server is running
        try:
            # Test connection with a simple call
            request = user_service_pb2.GetAllUsersRequest()
            response = stub.GetAllUsers(request)
            print("Server is running!")
            
            # Start interactive menu
            interactive_menu(stub)
            
        except grpc.RpcError as e:
            print(f"Failed to connect to server: {e}")
            print("Make sure the gRPC server is running on localhost:50051")

if __name__ == '__main__':
    main()