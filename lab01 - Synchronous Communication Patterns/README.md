# COMP41720 Distributed System Lab1: Synchronous Communication Patterns

> Made by Xinchi Jian(xinchi.jian@ucdconnect.ie), 24207756

## Document Structure

- [Part one: Socket-based Client-server application](#part-one-build-socket-based-client-server-application)
- [Part two: REST APIs application](#part-two-rest-apis-application)
- [Part three: gRPC application](#part-three-grpc-application)
- [Part four: Performance Comparison](#part-four-performance-comparison---待修改)

```bash
lab01- Synchronous Communication Patterns/
├── python_socket/
│   ├── server.py              # TCP Socket Server implementation
│   ├── client.py              # TCP Socket Client implementation      
│   ├── Dockerfile             # Server side Container configuration
│   ├── Dockerfile.client      # Client side Container configuration
│   ├── docker-compose.yaml    # Deploye mulitiple Containers configuration
│   └── requirements.txt       # Python dependencies
├── python_rest_lab/
│   ├── app.py                  # Main Flask application with route handlers
│   ├── models.py               # User model with business logic
│   ├── users.json             # Sample user data for testing
│   ├── Dockerfile             # Container configuration
│   └── requirements.txt       # Python dependencies
├── python_grpc_lab/
│   ├── proto/
│   │   └── user_service.proto          # Protocol Buffer service definition
│   ├── generated/                       # Auto-generated gRPC code
│   │   ├── __init__.py         # Define generated folder as a regular package
│   │   ├── user_service_pb2.py         # Protocol Buffer message classes
│   │   └── user_service_pb2_grpc.py    # gRPC service stubs
│   ├── __init__.py         # Define this folder as a regular package
│   ├── server.py                        # gRPC server implementation
│   ├── client.py                        # gRPC client with interactive menu
│   ├── Dockerfile                       # Server container configuration
│   ├── Dockerfile.client                # Client container configuration
│   ├── docker-compose.yml               # Multi-container orchestration
│   ├── .dockerignore  
│   └── requirements.txt       # Python dependencies
├── test/
│   ├── test_grpc/
│   │   ├── test_grpc_service.py             # gRPC automated testing script
│   ├── test_socket/
│   │   ├── run_tests.py               # socket testingtesting script
│   │   ├── test_socket.py             # Unit and integration tests
├── benchmark.py                       # Benchmark script for performance comparison
├── docker-compose.yml                 # Docker compose file for performance comparison
├── requirements.txt                   # Python dependencies
└── README.md
```

## Part one: Build Socket-Based Client-Server Application

### Features
- **TCP Server**: Multi-threaded server with graceful shutdown
- **TCP Client**: Flexible client with interactive and single-message modes
- **Message Processing**: Converts messages to uppercase as a simple transformation
- **Error Handling**: Comprehensive error handling for network issues
- **Testing**: Complete unit and integration test suite
- **Docker Support**: Containerized deployment

### Functionalities

#### 1. `server.py` 

Include Class `SocketServer`, host, port number, server_socket, running status and client_threads.

The functions in class includes:
- `start()`: Create a TCP socket, setting the specific hostname and port number and start the socket server. Maintain the server loop and accept client connections
- `handle_client(client_socket, client_address)`: Handle individual client connections. Including receiving data from the client, decoding messages, processing messages and sending a response back to the client
- `process_message(message)`: Process incoming message and return response
- `shutdown()`: Gracefully shut down the server
- `cleanup()`: clean up resources

#### 2. `client.py`
- `connect()`: Establish connection to server and return message about if the connection successful
- `send_message(message)`: Send message to server and wait for response
- `disconnect()`: Close connection to server
- `send_single_message(message)`: Connect to server, send a single message, get response and disconnect
- `interactive_mode()`: Run client in interactive mode for multiple messages

### **Quick Start**

#### 1. Local running

a. Execute TCP server
```bash
# Install dependenices
pip install -r requirements.txt

# directed to the socket-lab dictionary
cd ~/python_socket

# Execute Server program
python server.py
```
The terminal would show these results:
```bash
2025-09-29 16:44:19,235 - INFO - Server bound to localhost:8080
2025-09-29 16:44:19,235 - INFO - Server listening for connections...
```
2. Execute Client (Two methods)
  - Single message mode:
```bash
python client.py --message "Hello World"
```
  - Interactive mode:
```bash
python client.py --interactive
```
![](/lab01%20-%20Synchronous%20Communication%20Patterns/image/socket_local_running.png)

#### 2. Docker Development
```bash
# 1. Build and start the server
docker-compose up -d socket-server

# 2. Send a single message
docker-compose run --rm socket-client

# 3. Run interactive client
docker-compose --profile interactive run --rm socket-client-interactive
```
### **Testing**
#### 1. Testing details
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

#### 2. Quick test
```bash
# redirect into test/test_socket folder
cd test/test_socket

# Run all testa with organised output
python run_tests.py
```

#### 3. Overall results
✅ All Tests Passed: 6/6 test categories (100% success rate)

|**Test Category**   |   **Tests**  | **Status**| **Duration**|
| ---|--- | ---| ---|
|Unit Tests | 3 | ✅ PASSED|0.14s|
|Error Condition Tests | 5 | ✅ PASSED | 1.26s |
|Integration Tests | 1 | ✅ PASSED | 0.44s |
|Multiple Client Test |  1 | ✅ PASSED | 0.44s |
|Connection Tests | 1 | ✅ PASSED | 0.02s |
|Performance Tests | 1 | ✅ PASSED | 0.13s |
| **Total** | **12** | ✅ **PASSED** | **2.43s** | 


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

### File Description
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
// Success response
{ 
"success": true, 
"data": { "users data" }, 
"message": "Operation successful" 
}

// Error response
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
pip install -r requirements.txt
```

Step 2: Install Dependencies
```bash
# direct to REST folder
cd python-rest-lab
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
Setting the Header key with “Content-Type” and value with “application/json”, then copy `{"name": "John Doe", "id": 1, "email": "john,doe@example.com"}` in the body section. The result is shown below:

![Create_a_user](/lab01%20-%20Synchronous%20Communication%20Patterns/image/rest_creat_user.png)


#### Test 2 - Retrieve all users 
```
GET http://localhost:5000/api/users
```
![Retrieve all users](/lab01%20-%20Synchronous%20Communication%20Patterns/image/retrieve%20specific%20user%20by%20id.png)

Successfully return all users' information, HTTP status code is 200.

#### Test 3 - Retrieve specific user by ID 
```
GET http://localhost:5000/api/users/4
```
Successfully return the user’s information with the ID is 4, HTTP status code is 200

![Retrieve specific user by ID](/lab01%20-%20Synchronous%20Communication%20Patterns/image/retrieve%20specific%20user%20by%20id.png)

#### Test 4 - Update User
```
PUT http://localhost:5000/api/users/1
```
Setting the Header key with “Content-Type” and value with “application/json”, then copy `{"name": "Alex James", "email": "alexjames@example.com"}` in the body section, then the user’s information is updated successfully, HTTP Status code is 200

![Update User](/lab01%20-%20Synchronous%20Communication%20Patterns/image/update%20user.png)

#### Test 5 - Delete User 
```
DELETE http://localhost:5000/api/users/2
```
Entered `id:2` in the URL and deleted the user’s information successfully

![Delete User](/lab01%20-%20Synchronous%20Communication%20Patterns/image/delete%20user.png)


#### Test 6 - Create Duplicate user
Create duplicate users with the same ID, return `409` conflict

![Create duplicate user](/lab01%20-%20Synchronous%20Communication%20Patterns/image/create%20duplicate%20user.png)

#### Test 7 - Missing required fields
Lack ID and email Fields, return `400` Bad Request

![Missing required fields](/lab01%20-%20Synchronous%20Communication%20Patterns/image/missing%20required%20fields.png)

#### Test 8 - User Not Found
Enter user ID not exist in Users database, return `404` Not Found

![User not found](/lab01%20-%20Synchronous%20Communication%20Patterns/image/User%20not%20found.png)

## Part Three: gRPC application
### Features

- **Protocol Buffers Serialisation**: Efficient binary serialisation using Protocol Buffers (protobuf) for data transmission
- **Type-Safe Communication**: Strongly-typed service definitions ensure compile-time type checking
- **Bidirectional Communication**: gRPC's HTTP/2-based protocol supports efficient client-server interaction
- In-Memory Data Storage: Lightweight user data management without external database dependencies
- **Interactive Client Interface**: User-friendly menu-driven client for testing and demonstration
- Comprehensive Error Handling: Robust exception handling for network failures and invalid operations
- **Docker Support**: Containerized deployment for consistent cross-platform execution and Docker health checks ensure service reliability

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
- Thread-safe operations through gRPC's built-in concurrency handling
- Comprehensive exception handling for all operations
- Consistent response format across all methods
- Validation logic for data integrity
#### 2. Client Implementation
```bash
# Interactive Menu Options:
1. Create User: Add new user with name, ID, and email
2. Get User: Retrieve specific user by ID
3. Get All Users: List all users in the system
4. Update User: Modify user name and/or email
5. Delete User: Remove user from the system
6. Run Demo: Execute automated test scenario
7. Exit: Close client connection
```
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
# Redirect to the gRPC folder
cd python_grpc_lab

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
![Create User](/lab01%20-%20Synchronous%20Communication%20Patterns/image/grpc_create_user.png)

- **Test Case 2: Duplicate ID Prevention**
```bash
Input: Create user with existing ID
Expected: Error message "User with this ID already exists"
```
![Duplicate ID Prevention](/lab01%20-%20Synchronous%20Communication%20Patterns/image/grpc_duplicate_id_prevention.png)

- **Test Case 3: Update User**
```bash
Input: 
    Update ID=100, Name="John Smith"
Expected: Success with updated name, email unchanged
```
![](/lab01%20-%20Synchronous%20Communication%20Patterns/image/grpc_update_user.png)

- **Test Case 4: Get Non-existent User**
```bash
Input: GetUser(999)
Expected: Error message "User not found"
```
![](/lab01%20-%20Synchronous%20Communication%20Patterns/image/grpc_get_not_found_user.png)

- **Test Case 5: Delete User**
```bash
Input: DeleteUser(100)
Expected: Success with deleted user details
```
![](/lab01%20-%20Synchronous%20Communication%20Patterns/image/grpc_delete_user.png)

- **Test Case 6: Get all users**
```bash
Input:GetAllUsers
Expected: Success with all user details
```
![](/lab01%20-%20Synchronous%20Communication%20Patterns/image/grpc_get_all_users.png)

#### 2. Automated Testing Script
Execute `test_grpc_service.py`:
```bash
# Start server in one terminal
python server.py

# Run tests in another terminal
python test_grpc_service.py
```
Test results shown below:
![](/lab01%20-%20Synchronous%20Communication%20Patterns/image/grpc_demo.png)

## Part Four: Performance Comparison
### Benchmark Script
I create a benchmarking script compares the performance of REST and gRPC implementations. It measures latency, throughput, and reliability under different conditions: 

1. Sequential Create Operations
    - Tests creating users one at a time
    - Measures baseline latency
2. Sequential Read Operations
    - Tests reading user data
    - Compares retrieval performance
3. Concurrent operations
    - Tests performance under load
    - Simulates multiple simultaneous requests

### Quick start
Step 1: build docker compose container
```bash
docker-compose up --build -d
```
Step 2: Execute `benchmark.py` file
```bash
python benchmark.py
```

Sample Output shown below:
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
### Key Findings
1. Latency Performance
gRPC demonstrates significantly superior latency performance across all test scenarios:

- **Sequential Create**: gRPC is 87.8% faster (0.23ms vs 1.87ms)
- **Sequential Read**: gRPC is 85.5% faster (0.24ms vs 1.67ms)
- **Concurrent Operations**: gRPC is 82.9% faster (1.55ms vs 9.07ms)

2. Throughput Analysis
The throughput advantage of gRPC is substantial:

- Sequential operations: gRPC achieves **8x higher throughput** (~4,200 req/s vs ~550 req/s)
- Concurrent operations: gRPC maintains **6x higher throughput** (646 req/s vs 110 req/s)

3. Performance Consistency
gRPC exhibits more consistent performance:

- Lower standard deviation across all tests (0.10-0.48ms vs 0.49-2.83ms)
- Tighter 95th/99th percentile ranges
- More predictable response times under load

4. Scalability Under Concurrency
Under concurrent load (10 workers), the performance gap widens:

- REST latency increases 5x (1.87ms → 9.07ms)
- gRPC latency increases only 7x (0.23ms → 1.55ms)
- gRPC demonstrates better scalability characteristics

5. Performance Comparison Metric

| Metric | gRPC | REST API | 
|---     |----- | -------- |
| Serialization | Binary (protobuf) | Text (JSON) |
| Payload Size | ~30% smaller | Baseline |
| Speed | ~2-5x faster | Baseline | 
| Type Safety | Compile-time | Runtime | 
| Browser Support | Limited | Full | 

### Conclusion
gRPC's binary Protocol Buffers serialization and HTTP/2 multiplexing provide substantial performance advantages over JSON-based REST APIs. The **80-88%** latency reduction and 6-8x throughput improvement make gRPC particularly suitable for high-performance, low-latency microservice architectures. However, REST remains valuable for its simplicity, debugging ease, and broader ecosystem support.




