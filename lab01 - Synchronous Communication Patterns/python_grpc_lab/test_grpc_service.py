import grpc
import sys
sys.path.append('generated')
import user_service_pb2
import user_service_pb2_grpc

def run_tests():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = user_service_pb2_grpc.UserServiceStub(channel)
        
        # Test 1: Create User
        print("Test 1: Create User")
        response = stub.CreateUser(
            user_service_pb2.CreateUserRequest(
                name="Test User",
                id=1,
                email="test@example.com"
            )
        )
        assert response.success == True
        print("✓ Passed")
        
        # Test 2: Get User
        print("Test 2: Get User")
        response = stub.GetUser(
            user_service_pb2.GetUserRequest(id=1)
        )
        assert response.success == True
        assert response.user.name == "Test User"
        print("✓ Passed")
        
        # Test 3: Update User
        print("Test 3: Update User")
        response = stub.UpdateUser(
            user_service_pb2.UpdateUserRequest(
                id=1,
                name="Updated User",
                email="updated@example.com"
            )
        )
        assert response.success == True
        print("✓ Passed")
        
        # Test 4: Delete User
        print("Test 4: Delete User")
        response = stub.DeleteUser(
            user_service_pb2.DeleteUserRequest(id=1)
        )
        assert response.success == True
        print("✓ Passed")
        
        # Test 5: Get Non-existent User
        print("Test 5: Get Non-existent User")
        response = stub.GetUser(
            user_service_pb2.GetUserRequest(id=999)
        )
        assert response.success == False
        print("✓ Passed")
        
        print("\nAll tests passed! ✓")

if __name__ == '__main__':
    run_tests()