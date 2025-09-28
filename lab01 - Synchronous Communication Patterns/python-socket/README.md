# Socket-Based Client-Server Application

This is Phase 1 implementation of the Distributed Systems Lab, featuring a TCP socket-based client-server application with Python.

## Features

- **TCP Server**: Multi-threaded server with graceful shutdown
- **TCP Client**: Flexible client with interactive and single-message modes
- **Message Processing**: Converts messages to uppercase as a simple transformation
- **Error Handling**: Comprehensive error handling for network issues
- **Testing**: Complete unit and integration test suite
- **Docker Support**: Containerized deployment

## Project Structure

```
socket-lab/
├── server.py              # TCP Socket Server implementation
├── client.py              # TCP Socket Client implementation
├── test_socket.py         # Unit and integration tests
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
└── README.md             # This documentation
```

## Quick Start

### Running the Server

```bash
# Basic usage
python server.py

# Custom host and port
python server.py --host 0.0.0.0 --port 9000

# Verbose logging
python server.py --verbose
```

### Running the Client

```bash
# Single message mode
python client.py --message "Hello World"

# Interactive mode
python client.py --interactive

# Read from stdin
echo "test message" | python client.py

# Connect to custom server
python client.py --host 192.168.1.100 --port 9000 --message "Hello"
```

## Usage Examples

### Server Usage

The server starts on `localhost:8080` by default and accepts multiple concurrent connections:

```bash
$ python server.py
2024-01-15 10:30:00,123 - INFO - Server bound to localhost:8080
2024-01-15 10:30:00,124 - INFO - Server listening for connections...
```

### Client Usage

**Single Message Mode:**
```bash
$ python client.py --message "hello world"
Server response: HELLO WORLD
```

**Interactive Mode:**
```bash
$ python client.py --interactive
Socket Client - Interactive Mode
Type 'quit' or 'exit' to disconnect
----------------------------------------
Enter message: hello world
Server response: HELLO WORLD
Enter message: test 123
Server response: TEST 123
Enter message: quit
Goodbye!
```

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest test_socket.py -v

# Run with coverage
python -m pytest test_socket.py --cov=. --cov-report=html

# Run specific test categories
python -m pytest test_socket.py::TestSocketServer -v
python -m pytest test_socket.py::TestIntegration -v
python -m pytest test_socket.py::TestErrorConditions -v
```

### Test Categories

- **Unit Tests**: Test individual components (server, client classes)
- **Integration Tests**: Test client-server communication
- **Error Condition Tests**: Test network failures, malformed input, timeouts
- **Performance Tests**: Basic throughput and load testing

## Docker Deployment

### Building the Container

```bash
# Build the Docker image
docker build -t socket-server .

# Run the container
docker run -p 8080:8080 socket-server

# Run with custom configuration
docker run -p 9000:9000 socket-server python server.py --host 0.0.0.0 --port 9000
```

### Docker Compose (Optional)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  socket-server:
    build: .
    ports:
      - "8080:8080"
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

## Architecture and Design

### Server Design

The server implements a **multi-threaded architecture** with the following key components:

- **Main Thread**: Accepts incoming connections and spawns handler threads
- **Client Handler Threads**: Process individual client requests
- **Graceful Shutdown**: Signal handling for clean termination
- **Error Recovery**: Robust error handling for network issues

### Communication Protocol

- **Transport**: TCP sockets for reliable communication
- **Encoding**: UTF-8 for text messages
- **Message Flow**: Simple request-response pattern
- **Processing**: Converts messages to uppercase as demonstration

### Key Features

1. **Synchronous Communication**: Client waits for server response before proceeding
2. **Multi-client Support**: Server handles multiple concurrent connections
3. **Error Handling**: Comprehensive error detection and reporting
4. **Graceful Shutdown**: Clean termination with SIGINT/SIGTERM handling
5. **Flexible Client**: Support for single messages and interactive sessions

## API Reference

### Server Class: `SocketServer`

```python
server = SocketServer(host='localhost', port=8080)
server.start()          # Start the server (blocking)
server.shutdown()       # Graceful shutdown
```

### Client Class: `SocketClient`

```python
client = SocketClient(host='localhost', port=8080, timeout=5.0)
client.connect()                           # Establish connection
response = client.send_message("hello")    # Send message and get response
client.disconnect()                        # Close connection

# Or use convenience method
response = client.send_single_message("hello")  # Connect, send, disconnect
```

## Error Handling

The implementation handles various error conditions:

- **Connection Refused**: Server not running or port blocked
- **Network Timeouts**: Configurable timeout for operations
- **Invalid Data**: Malformed UTF-8 encoding
- **Server Shutdown**: Graceful handling of server termination
- **Resource Cleanup**: Proper socket and thread cleanup

## Performance Characteristics

- **Throughput**: Handles 100+ messages/second on typical hardware
- **Concurrency**: Supports multiple simultaneous client connections
- **Memory**: Efficient resource usage with thread cleanup
- **Latency**: Low-latency request-response communication

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8080
   # Kill the process or use a different port
   python server.py --port 8081
   ```

2. **Connection Refused**
   ```bash
   # Ensure server is running
   python server.py &
   # Test with telnet
   telnet localhost 8080
   ```

3. **Docker Permission Issues**
   ```bash
   # Run as current user
   docker run --user $(id -u):$(id -g) -p 8080:8080 socket-server
   ```

### Debugging

Enable verbose logging for troubleshooting:

```bash
python server.py --verbose
python client.py --verbose --message "test"
```

## Security Considerations

- **Input Validation**: Server validates UTF-8 encoding
- **Resource Limits**: Thread-based architecture prevents resource exhaustion
- **Non-root User**: Docker container runs as non-root user
- **Network Binding**: Default binding to localhost for security

## Contributing

1. **Code Style**: Follow PEP 8 guidelines
2. **Testing**: Add tests for new features
3. **Documentation**: Update README for changes
4. **Error Handling**: Implement robust error handling

## License

This project is for educational purposes as part of the Distributed Systems lab assignment.

## Assignment Requirements Fulfillment

✅ **TCP Server**: Implemented with localhost:8080 binding by default  
✅ **Message Processing**: Converts messages to uppercase  
✅ **Graceful Shutdown**: Signal handling for clean termination  
✅ **Client Implementation**: Connect, send, receive, print functionality  
✅ **Testing**: Comprehensive pytest suite with unit and integration tests  
✅ **Docker Support**: Minimal Dockerfile with port 8080 exposure  
✅ **Error Handling**: Connection refused, malformed input, timeouts  
✅ **Clean Code**: Well-structured, documented, and maintainable code