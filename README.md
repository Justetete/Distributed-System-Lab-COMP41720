# Distributed-System-Lab-COMP41720
# Synchronous Communication Patterns

Made by Xinchi Jian(xinchi.jian@ucdconnect.ie), 24207756
## Document Structure

- Part one: Socket-based Client-server application
- Part two: REST APIs application
- Part three: gRPC application
- Part four: Performance Comparison

## Part one: Build Socket-Based Client-Server Application

### Features

- Created Server and Client by TCP protocol
- Message Processing:
  - Client 可以同時發送單個消息，並收到反饋
  - 也可以互動式連續發送多條消息
- Error handling
- Testing

### Project Structure

```bash
socket-lab/
├── server.py              # TCP Socket Server implementation
├── client.py              # TCP Socket Client implementation
├── test_socket.py         # Unit and integration tests
├── requirements.txt       # Python dependencies
├── Dockerfile             # Server side Container configuration
├── Dockerfile.client      # Client side Container configuration
├── docker-compose.yaml    # Deploye mulitiple Containers configuration
└── README.md              # This documentation
```

### Functionalities

#### 1. `server.py` 

Include Class SocketServer, 包含host, port number, server_socket, running status and client_threads.

The functions in class includes:
- `start()`: Create a TCP socket, setting the specific hostname and port number and start the socket server. Maintain the server loop and accept client connections
- `handle_client(client_socket, client_address)`: Handle individual client connections. Including receiving data from the client, decoding messages, processing messages and sending a response back to the client
- `process_message(message)`: Process incoming message and return response
- `shutdown()`: Gracefully shut down the server
- `cleanup()`: clean up resources

#### 2. `client.py` 文件功能

Include Class `SocketClient`, 包含host, port number, server_socket and timeout attributes.

The functions in class include:
- `connect()`: Establish connection to server and return message about if the connection successful
- `send_message(message)`: Send message to server and wait for response
- `disconnect()`: Close connection to server
- `send_single_message(message)`: Connect to server, send a single message, get response and disconnect
- `interactive_mode()`: Run client in interactive mode for multiple messages

### **Quick Start**

#### 1. Local running

Running the server
```bash
# directed to the socket-lab dictionary
cd ~/socket-lab

# Install dependenices
pip install -r requirements.txt

# Execute Server program
python server.py
```
The terminal would show these results:
```bash
2025-09-29 16:44:19,235 - INFO - Server bound to localhost:8080
2025-09-29 16:44:19,235 - INFO - Server listening for connections...
```
Running the Client (Two methods)(這裡需要插入截圖)
  - Single message mode:
```bash
python client.py --message "Hello World"
```
  - Interactive mode: type command python client.py -- interactive
```bash
python client.py --interactive
```
這裡添加兩張截圖：啟動server 和clinet 兩個終端的截圖放在一起

#### 2. Docker Development

### **Testing**
主要的測試功能包括

| **Testing Classes**   |    **Testing function**   |  **Description**    |
|--------------- |-----------------|---       |
|`TestSocketServer` - Unit tests for SocketServer class  | `test_server_initialization`|Test server initialisation with default and custom parameters.| 
| | `test_process_message` | Test message processing functionality.|
| `TestSocketClient` - unit tests for SocketClient class | `test_client_initialization` | Test client initialisation with default and custom parameters. |
| `TestIntegration` - Integration tests for server-client communication | `test_basic_communication` | Test basic client-server communication | 
| | `test_multiple_clients` | Test server handling multiple clients simultaneously |
| | `test_connection_refused` | Test client behaviour when the server is not running. |
| |`test_server_restart` | Test server can be restarted on the same port |
| `TestErrorConditions` - Tests for various error conditions| `test_invalid_host` | Test client behaviour with an invalid host |
| | `test_invalid_port` | Test client behaviour with an invalid port |
| | `test_connection_timeout` | Test client timeout behaviour |
| | `test_connection_closed_by_server` | Test client behaviour when the server closes the connection |
| | `test_malformed_input_handling` | Test server handling of malformed input |
| `TestCLIInterface` - Tests for command-line interface | `test_server_cli_arguments` |Test server command-line argument parsing |
| | `test_client_cli_arguments` | Test client command-line argument parsing |
| `TestPerformance` - Basic performance tests | `test_message_throughput` | Test message throughput under normal load


如何進行測試

測試結果如下

---

## Part Two: REST APIs application

### Features
- Complete **CRUD** Operations: Full support for **creating, reading, updating**, and **deleting** user records
- **RESTful Architecture**: Follows REST principles with proper HTTP methods and status codes
- **JSON Response Format**: Standardised JSON responses with success/error indicators
- **Error Handling**: Comprehensive exception handling with meaningful error messages. All endpoints are wrapped in try-except blocks to catch unexpected errors
- **Input Validation**: Validates required fields and data integrity before processing
- **Dockerized** Deployment: Container-ready with optimised Dockerfile and docker-compose configuration
- **Synchronous Communication**: Implements a blocking request-response pattern
- In-Memory Storage: using dictionary (user_lists) for data storage

### Project Structure
```bash
python-rest-lab/
├── app.py                  # Main Flask application with route handlers
├── models.py               # User model with business logic
├── requirements.txt        # Python dependencies
├── users.json             # Sample user data for testing
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-container orchestration
├── .dockerignore          # Files to exclude from Docker build
└── README.md              # Project documentation
```

### File Descriptions
#### 1. `app.py`
- Main application entry point
- Defines all API endpoints and route handlers
- Implements request validation and error handling
- Returns standardised JSON responses
#### 2. `models.py`
- Contains the Users class with static methods
- Manages user data storage using class-level dictionary
- Implements CRUD operations (show_users, get_user, update_user, delete_user)
- Provides helper methods for data validation (user_exists)
#### 3. Dockerfile
- Production-ready container configuration
- Multi-stage optimisation for smaller image size
- Non-root user for enhanced security
- Health check implementation for container monitoring

### API Endpoints
| **Method** | **Endpoint** | **Description** |**Status Codes** |
|--- | ---|---|---|
|**GET** | `/api/users` | Retrieve all users |200, 500 |
|**GET**|`/api/users/<id>`|Retrieve specific user by ID|200, 404, 500|
|**POST**|`/api/users`|Create new user|201, 400, 409, 500|
|**PUT**|`/api/users`/<id>|Update existing user|200, 400, 404, 500|
|**DELETE** | `/api/users/<id>` | Delete user |200, 404, 500 |

#### Detailed Endpoint Specifications
##### 1. `GET /api/users`
- Purpose: Retrieve all users from the system
- Request: No parameters required
- Response:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "John Smith",
      "email": "john.smith@email.com"
    }
  ],
  "message": "Users retrieved successfully"
}
```

##### 2. `GET /api/users/<id>`
- Purpose: Retrieve a specific user by ID
- Parameters: id (integer): User ID in URL path
- Success Response (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Smith",
    "email": "john.smith@email.com"
  },
  "message": "User retrieved successfully"
}
```
- Error Response (404):
```json
{
  "success": false,
  "message": "User not found."
}
```

##### 3. `POST /api/users`
- Purpose: Create a new user
- Request Body:
```json
{
  "id": 1,
  "name": "John Smith",
  "email": "john.smith@email.com"
}
```
- Success Response (201):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Smith",
    "email": "john.smith@email.com"
  },
  "message": "User created successfully"
}
```
- Validation Errors: 
  - `400`: Missing required fields
  - `409`: User with ID already exists

#### 4. `PUT /api/users/<id>`
- Purpose: Update an existing user's information
- Parameters: id (integer): User ID in URL path
- Request Body (partial updates supported):
```json
{
  "name": "John Doe",
  "email": "john.doe@email.com"
}
```
- Success Response (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@email.com"
  },
  "message": "User updated successfully"
}
```
#### 5. `DELETE /api/users/<id>`
- Purpose: Remove a user from the system
- Parameters: id (integer): User ID in URL path
- Success Response (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Smith",
    "email": "john.smith@email.com"
  },
  "message": "User deleted successfully"
}
```
### Functionalities
#### 1. User Creation
The system validates all required fields (name, id, email) before creating a user. It checks for duplicate IDs and prevents conflicts by returning a 409 status code if a user with the same ID already exists.

#### 2. User Retrieval
Supports both individual and bulk user retrieval. `show_users()` method returns all users as a list, while `get_user()` retrieves a specific user by ID.

#### 3. User Update
Allows partial updates to user information. Only the provided fields are updated, leaving other fields unchanged.

#### 4. User Deletion
Removes a user from the system and returns the deleted user's information for confirmation.

#### 5. Error Handling
Comprehensive error handling throughout the application ensures robust operation and clear error messages. 

Error Scenarios:
- Missing required fields (`400` Bad Request)
- User not found (`404` Not Found)
- Duplicate user ID (`409` Conflict)
- Internal server errors (`500` Internal Server Error)

#### 6. Response Standardisation
All endpoints return consistent JSON responses with three fields:
- `success`: Boolean indicating operation success
- `data`: Response payload (user data or null)
- `message`: Human-readable status message
```json
# Success response
{ 
"success": true, 
"data": { ... }, 
"message": "Operation successful" 
}

# Error response
{ "success": false,
  "message": "Error description" }
```

### Quick Start
#### Preprequisties
- Python 3.9 or higher
- Docker
- curl or Postman (for API testing)

#### 1. Local Development Setup
Step 1: Install Dependencies
```bash
mkdir python-rest-lab 
cd python-rest-lab
```

Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

Step 3: Run Application
```bash
python app.py
```
The server will start on http://localhost:5000

#### 2. Docker development 
```bash
# Build the Docker image
docker build -t python-rest-api .

# Run the container
docker run -p 5000:5000 python-rest-api
```

### Testing
The testing would be held manually on Postman

#### Test 1 - Create a User 
```
POST http://localhost:5000/api/users
```
Setting the Header key with “Content-Type” and value with “application/json”, then copy `{"name": "John Doe", "id": 1, "email": "john@example.com"}` in the body section. The result is shown below:

#### Test 2 - Retrieve all users 
```
GET http://localhost:5000/api/users
```

Successfully return all users' information, HTTP status code is 200.

#### Test 3 - Retrieve specific user by ID 
```
GET http://localhost:5000/api/users/4
```
Successfully return the user’s information with the ID is 4, HTTP status code is 200

#### Test 4 - Update User
```
PUT http://localhost:5000/api/users/1
```
Setting the Header key with “Content-Type” and value with “application/json”, then copy `{"name": "Alex James", "email": "alexjames@example.com"}` in the body section, then the user’s information is updated successfully, HTTP Status code is 200

#### Test 5 - Delete User 
```
DELETE http://localhost:5000/api/users/2
```
Entered `id:2` in the URL and deleted the user’s information successfully


#### Test 6 - Create Duplicate user
Create duplicate users with the same ID, return `409` conflict

#### Test 7 - Missing required fields
Lack ID and email Fields, return `400` Bad Request

#### Test 8 - User Not Found
Enter user ID not exist in Users database, return `404` Not Found

## Part Three: gRPC application
### Features

- Protocol Buffers Serialisation: Efficient binary serialisation using Protocol Buffers (protobuf) for data transmission
- Type-Safe Communication: Strongly-typed service definitions ensure compile-time type checking
- Bidirectional Communication: gRPC's HTTP/2-based protocol supports efficient client-server interaction
- In-Memory Data Storage: Lightweight user data management without external database dependencies
- Interactive Client Interface: User-friendly menu-driven client for testing and demonstration
- Comprehensive Error Handling: Robust exception handling for network failures and invalid operations
- Docker Support: Containerized deployment for consistent cross-platform execution and Docker health checks ensure service reliability

### Project Structure
```bash
python-grpc-lab/
├── proto/
│   └── user_service.proto          # Protocol Buffer service definition
├── generated/                       # Auto-generated gRPC code
│   ├── user_service_pb2.py         # Protocol Buffer message classes
│   └── user_service_pb2_grpc.py    # gRPC service stubs
├── server.py                        # gRPC server implementation
├── client.py                        # gRPC client with interactive menu
├── test_grpc_service.py             # gRPC automated testing script
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Server container configuration
├── Dockerfile.client                # Client container configuration
├── docker-compose.yml               # Multi-container orchestration
└── .dockerignore                    # Docker build exclusions
```

### File Description
#### 1. `user_service.proto`
- Defines data structures (User, Request/Response messages)
- Specifies service interface with five RPC methods
- Uses `proto3` syntax for modern Protocol Buffers features
#### 2. `server.py`
- Implements `UserServiceServicer` class with business logic
- Manages in-memory user storage using Python dictionary
- Handles concurrent requests via gRPC server with thread pool
- Runs on port 50051 by default
#### 3. `client.py`
- Provides interactive command-line interface
- Demonstrates all service operations with sample data
- Supports both manual testing and automated demo mode
- Configurable server connection via environment variables

### API Endpoints
#### 1. Get User
**Purpose**: Retrieve a specific user by ID
Request Message:
```protobuf
message GetUserRequest {
  int32 id = 1;
}
```
**Response Message**:
```protobuf
message GetUserResponse {
  bool success = 1;
  string message = 2;
  User user = 3;
}
```
**Behavior**:
- Returns user data if found
- Returns `success=false` with error message if user doesn't exist

#### 2. Create User
**Purpose**: Create a new user in the system
**Request Message**:
```protobuf
message CreateUserRequest {
  string name = 1;
  int32 id = 2;
  string email = 3;
}
```
**Response Message**:
```protobuf
message CreateUserResponse {
  bool success = 1;
  string message = 2;
  User user = 3;
}
```
**Behavior**:
- Validates that ID doesn't already exist
- Ensures name and email are provided
- Returns created user data on success

#### 3. Update User
**Purpose**: Modify existing user information
**Request Message**:
```protobuf
message UpdateUserRequest {
  int32 id = 1;
  string name = 2;
  string email = 3;
}
```
**Response Message**:
```protobuf
message UpdateUserResponse {
  bool success = 1;
  string message = 2;
  User user = 3;
}
```
**Behavior**:
- Updates only provided fields (name/email)
- Returns error if user ID doesn't exist
- Returns updated user data on success

#### 4. DeleteUser
**Purpose**: Remove a user from the system
**Request Message**:
```protobuf
message DeleteUserRequest {
  int32 id = 1;
}
```
**Response Message**:
```protobuf
message DeleteUserResponse {
  bool success = 1;
  string message = 2;
  User user = 3;
}
```
**Behavior**:
- Removes user from storage
- Returns deleted user data for confirmation
- Returns error if user doesn't exist

#### 5. GetAllUsers
**Purpose**: Retrieve all users in the system
**Request Message**:
```protobuf
message GetAllUsersRequest {
  // Empty request
}
```
**Response Message**:
```protobuf
message GetAllUsersResponse {
  bool success = 1;
  string message = 2;
  repeated User users = 3;
}
```
**Behavior**:
- Returns array of all users
- Returns empty array if no users exist
- Always succeeds with appropriate message

### Functionalities
#### 1. Server Implementation
UserService Class:
class UserService(user_service_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.users = {}  # In-memory storage
Key Features:
Thread-safe operations through gRPC's built-in concurrency handling
Comprehensive exception handling for all operations
Consistent response format across all methods
Validation logic for data integrity
Server Lifecycle:
Initialise gRPC server with ThreadPoolExecutor (10 workers)
Register UserService implementation
Bind to port 50051 on all network interfaces
Start server and wait for termination
Graceful shutdown on keyboard interrupt
#### 2. Client Implementation
Interactive Menu Options:
Create User: Add new user with name, ID, and email
Get User: Retrieve specific user by ID
Get All Users: List all users in the system
Update User: Modify user name and/or email
Delete User: Remove user from the system
Run Demo: Execute automated test scenario
Exit: Close client connection
#### 3. Demo Mode:
- Creates three sample users
- Retrieves all users
- Fetches specific user
- Updates user information
- Deletes a user
- Displays final state

## Quick Start
### 1. Local Development Setup
Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```
Step 2: Generate gRPC Code
```bash
# Create generated directory
mkdir -p generated
# Generate Python code from proto file
python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./generated \
    --grpc_python_out=./generated \
    proto/user_service.proto
```
Step 3: Start Server
```bash
python server.py
# Output: Starting gRPC server on port 50051...
```
Step 4: Run Client (in new terminal)
```bash
# Activate virtual environment
source distributed_system_lab/bin/activate
# Run client
python client.py
```
### 2. Docker Deployment
Step 1: Build and Start Services
```bash
# Build and start all services
docker-compose up --build

# OR run in background
docker-compose up -d --build
```
Step 2: Interact with Client
```bash
# Attach to running client container
docker attach grpc-client
```
3. Quick Test with Demo Mode
```bash
# Start server
python server.py

# In new terminal, run client and select option 6
python client.py
# Choose: 6. Run Demo
```
Expected Demo Output:
```bash
--- Creating User ---
Name: Alice Johnson, ID: 1, Email: alice.johnson@email.com
Success: True
Message: User created successfully

--- Getting All Users ---
Total users: 3
  User - ID: 1, Name: Alice Johnson, Email: alice.johnson@email.com
  User - ID: 2, Name: Bob Smith, Email: bob.smith@email.com
  User - ID: 3, Name: Charlie Brown, Email: charlie.brown@email.com

--- Updating User 1 ---
Success: True
Updated User - ID: 1, Name: Alice Johnson Updated

--- Deleting User 3 ---
Success: True
Deleted User - ID: 3, Name: Charlie Brown
```
### Testing
#### 1. Manual Testing Approach
- **Test Case 1: Create User**
```bash
Input: 
    Name="John Doe", ID=100, 
    Email="john@example.com"
```
- **Test Case 2: Duplicate ID Prevention**
```bash
Input: Create user with existing ID
Expected: Error message "User with this ID already exists"
```

- **Test Case 3: Update User**
```bash
Input: 
    Update ID=100, Name="John Smith"
Expected: Success with updated name, email unchanged
```

- **Test Case 4: Get Non-existent User**
```bash
Input: GetUser(999)
Expected: Error message "User not found"
```

- **Test Case 5: Delete User**
```bash
Input: DeleteUser(100)
Expected: Success with deleted user details
```

- **Test Case 6: Get all users**
```bash
Input:GetAllUsers
Expected: Success with all user details
```
6.2 Automated Testing Script
Execute `test_grpc_service.py`:
```bash
# Start server in one terminal
python server.py

# Run tests in another terminal
python test_grpc_service.py
```
Test results shown below:


## Part Four: Performance Comparison - 待修改
7.1 Performance Comparison
Metric
gRPC
REST API
Serialization
Binary (protobuf)
Text (JSON)
Payload Size
~30% smaller
Baseline
Speed
~2-5x faster
Baseline
Type Safety
Compile-time
Runtime
Browser Support
Limited
Full

7.2 Use Case Recommendations
Use gRPC when:
Microservices communication
High-performance requirements
Strong typing needed
Streaming data required
Use REST when:
Public APIs
Browser clients
Simple CRUD operations
Wide compatibility needed


### Performance Comparison
```bash
============================================================
                  DISTRIBUTED SYSTEMS LAB                   
============================================================


============================================================
             REST vs gRPC Performance Benchmark             
============================================================

Configuration:
  Number of requests: 100
  Concurrent workers: 10
  REST endpoint: http://localhost:5000/api/users
  gRPC endpoint: localhost:50051

============================================================
                SEQUENTIAL CREATE OPERATIONS                
============================================================

Running REST API benchmark (Create)...
REST API - Create User
  Success Rate:  100.00% (100/100)
  Mean Latency:  1.87 ms
  Median:        1.66 ms
  Min:           1.33 ms
  Max:           8.74 ms
  Std Dev:       1.05 ms
  95th %ile:     2.81 ms
  99th %ile:     8.74 ms

Running gRPC benchmark (Create)...
gRPC - Create User
  Success Rate:  100.00% (100/100)
  Mean Latency:  0.23 ms
  Median:        0.20 ms
  Min:           0.15 ms
  Max:           1.46 ms
  Std Dev:       0.13 ms
  95th %ile:     0.35 ms
  99th %ile:     1.46 ms


============================================================
                   PERFORMANCE COMPARISON                   
============================================================

Mean Latency Comparison:
  REST:  1.87 ms
  gRPC:  0.23 ms
  ✓ gRPC is 87.8% faster

Throughput Comparison (requests/second):
  REST:  535.28 req/s
  gRPC:  4370.43 req/s


============================================================
                 SEQUENTIAL READ OPERATIONS                 
============================================================

Running REST API benchmark (Read)...
REST API - Read User
  Success Rate:  100.00% (100/100)
  Mean Latency:  1.67 ms
  Median:        1.57 ms
  Min:           1.32 ms
  Max:           6.14 ms
  Std Dev:       0.49 ms
  95th %ile:     2.00 ms
  99th %ile:     6.14 ms

Running gRPC benchmark (Read)...
gRPC - Read User
  Success Rate:  100.00% (100/100)
  Mean Latency:  0.24 ms
  Median:        0.22 ms
  Min:           0.19 ms
  Max:           1.15 ms
  Std Dev:       0.10 ms
  95th %ile:     0.31 ms
  99th %ile:     1.15 ms


============================================================
                   PERFORMANCE COMPARISON                   
============================================================

Mean Latency Comparison:
  REST:  1.67 ms
  gRPC:  0.24 ms
  ✓ gRPC is 85.5% faster

Throughput Comparison (requests/second):
  REST:  599.59 req/s
  gRPC:  4124.84 req/s


============================================================
                   CONCURRENT OPERATIONS                    
============================================================

Running REST API benchmark (Concurrent)...
REST API - Concurrent Requests
  Success Rate:  100.00% (100/100)
  Mean Latency:  9.07 ms
  Median:        8.55 ms
  Min:           4.78 ms
  Max:           18.54 ms
  Std Dev:       2.83 ms
  95th %ile:     14.51 ms
  99th %ile:     18.54 ms

Running gRPC benchmark (Concurrent)...
gRPC - Concurrent Requests
  Success Rate:  100.00% (100/100)
  Mean Latency:  1.55 ms
  Median:        1.48 ms
  Min:           0.77 ms
  Max:           3.03 ms
  Std Dev:       0.48 ms
  95th %ile:     2.51 ms
  99th %ile:     3.03 ms


============================================================
                   PERFORMANCE COMPARISON                   
============================================================

Mean Latency Comparison:
  REST:  9.07 ms
  gRPC:  1.55 ms
  ✓ gRPC is 82.9% faster

Throughput Comparison (requests/second):
  REST:  110.24 req/s
  gRPC:  646.28 req/s


============================================================
                          SUMMARY                           
============================================================

Key Observations:
1. Latency: Compare mean and median latencies
2. Consistency: Check standard deviation and percentiles
3. Concurrency: Evaluate performance under concurrent load
4. Reliability: Review success rates and error counts

Benchmark completed!
```
