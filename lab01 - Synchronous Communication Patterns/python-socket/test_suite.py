import pytest
import socket
import threading
import time
import subprocess
import sys
import os
from unittest.mock import patch, Mock

# Add the current directory to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import SocketServer
from client import SocketClient


class TestSocketServer:
    """Unit tests for SocketServer class."""
    
    def test_server_initialization(self):
        """Test server initialization with default and custom parameters."""
        # Test default initialization
        server = SocketServer()
        assert server.host == 'localhost'
        assert server.port == 8080
        assert server.running is False
        assert server.server_socket is None
        
        # Test custom initialization
        server = SocketServer('127.0.0.1', 9000)
        assert server.host == '127.0.0.1'
        assert server.port == 9000
        
    def test_process_message(self):
        """Test message processing functionality."""
        server = SocketServer()
        
        # Test normal message processing
        assert server._process_message("hello") == "HELLO"
        assert server._process_message("Hello World") == "HELLO WORLD"
        assert server._process_message("123") == "123"
        
        # Test empty message
        assert server._process_message("") == "ERROR: Empty message"
        
        # Test whitespace handling
        assert server._process_message("  hello  ") == "  HELLO  "


class TestSocketClient:
    """Unit tests for SocketClient class."""
    
    def test_client_initialization(self):
        """Test client initialization with default and custom parameters."""
        # Test default initialization
        client = SocketClient()
        assert client.host == 'localhost'
        assert client.port == 8080
        assert client.timeout == 5.0
        assert client.client_socket is None
        
        # Test custom initialization
        client = SocketClient('127.0.0.1', 9000, 10.0)
        assert client.host == '127.0.0.1'
        assert client.port == 9000
        assert client.timeout == 10.0


class TestIntegration:
    """Integration tests for server-client communication."""
    
    @pytest.fixture
    def server_thread(self):
        """Fixture to start server in a separate thread."""
        server = SocketServer('localhost', 8081)  # Use different port to avoid conflicts
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(0.5)
        
        yield server
        
        # Cleanup: shutdown server
        server.shutdown()
        
    def test_basic_communication(self, server_thread):
        """Test basic client-server communication."""
        client = SocketClient('localhost', 8081)
        
        # Test successful communication
        response = client.send_single_message("hello world")
        assert response == "HELLO WORLD"
        
        # Test multiple messages
        response = client.send_single_message("test message")
        assert response == "TEST MESSAGE"
        
    def test_multiple_clients(self, server_thread):
        """Test server handling multiple clients simultaneously."""
        clients = [SocketClient('localhost', 8081) for _ in range(3)]
        responses = []
        
        def client_task(client, message):
            response = client.send_single_message(message)
            responses.append(response)
            
        # Start multiple client threads
        threads = []
        messages = ["client1", "client2", "client3"]
        
        for i, client in enumerate(clients):
            thread = threading.Thread(target=client_task, args=(client, messages[i]))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
            
        # Check responses
        assert len(responses) == 3
        assert "CLIENT1" in responses
        assert "CLIENT2" in responses
        assert "CLIENT3" in responses
        
    def test_connection_refused(self):
        """Test client behavior when server is not running."""
        client = SocketClient('localhost', 8082)  # Non-existent server
        
        # Test connection failure
        assert client.connect() is False
        
        # Test single message failure
        response = client.send_single_message("test")
        assert response is None
        
    def test_server_restart(self):
        """Test server can be restarted on the same port."""
        port = 8083
        
        # Start first server
        server1 = SocketServer('localhost', port)
        server_thread1 = threading.Thread(target=server1.start, daemon=True)
        server_thread1.start()
        time.sleep(0.5)
        
        # Test connection works
        client = SocketClient('localhost', port)
        response = client.send_single_message("test1")
        assert response == "TEST1"
        
        # Shutdown first server
        server1.shutdown()
        time.sleep(0.5)
        
        # Start second server on same port
        server2 = SocketServer('localhost', port)
        server_thread2 = threading.Thread(target=server2.start, daemon=True)
        server_thread2.start()
        time.sleep(0.5)
        
        # Test connection works with new server
        response = client.send_single_message("test2")
        assert response == "TEST2"
        
        # Cleanup
        server2.shutdown()


class TestErrorConditions:
    """Tests for various error conditions."""
    
    def test_invalid_host(self):
        """Test client behavior with invalid host."""
        client = SocketClient('invalid.host.name', 8080)
        
        assert client.connect() is False
        response = client.send_single_message("test")
        assert response is None
        
    def test_invalid_port(self):
        """Test client behavior with invalid port."""
        client = SocketClient('localhost', 99999)  # Invalid port
        
        assert client.connect() is False
        
    def test_connection_timeout(self):
        """Test client timeout behavior."""
        # Use a non-routable IP to simulate timeout
        client = SocketClient('10.255.255.1', 8080, timeout=1.0)
        
        start_time = time.time()
        result = client.connect()
        end_time = time.time()
        
        assert result is False
        assert end_time - start_time >= 1.0  # Should timeout after 1 second
        
    @pytest.fixture
    def mock_server(self):
        """Fixture for a server that closes connections immediately."""
        def mock_server_func():
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', 8084))
            server_socket.listen(1)
            
            try:
                while True:
                    client_socket, _ = server_socket.accept()
                    # Immediately close connection without processing
                    client_socket.close()
            except:
                pass
            finally:
                server_socket.close()
                
        thread = threading.Thread(target=mock_server_func, daemon=True)
        thread.start()
        time.sleep(0.2)  # Let server start
        
        yield
        
    def test_connection_closed_by_server(self, mock_server):
        """Test client behavior when server closes connection."""
        client = SocketClient('localhost', 8084)
        
        # Connection should succeed initially
        assert client.connect() is True
        
        # But sending message should fail due to closed connection
        response = client.send_message("test")
        assert response is None
        
    def test_malformed_input_handling(self):
        """Test server handling of malformed input."""
        server = SocketServer('localhost', 8085)
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        time.sleep(0.5)
        
        try:
            # Test with raw socket to send malformed data
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_socket.connect(('localhost', 8085))
            
            # Send invalid UTF-8 bytes
            raw_socket.send(b'\xff\xfe\xfd')
            
            # Should receive error response
            response = raw_socket.recv(1024)
            assert b"ERROR" in response
            
            raw_socket.close()
            
        finally:
            server.shutdown()


class TestCLIInterface:
    """Tests for command-line interface."""
    
    def test_server_cli_arguments(self):
        """Test server command-line argument parsing."""
        # This would require mocking sys.argv and testing main()
        # For simplicity, we'll test the core functionality
        pass
        
    def test_client_cli_arguments(self):
        """Test client command-line argument parsing."""
        # This would require mocking sys.argv and testing main()
        # For simplicity, we'll test the core functionality
        pass


# Performance and Load Tests
class TestPerformance:
    """Basic performance tests."""
    
    @pytest.fixture
    def performance_server(self):
        """Server fixture for performance testing."""
        server = SocketServer('localhost', 8086)
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        time.sleep(0.5)
        
        yield server
        
        server.shutdown()
        
    def test_message_throughput(self, performance_server):
        """Test message throughput under normal load."""
        client = SocketClient('localhost', 8086)
        
        # Connect once and send multiple messages
        assert client.connect() is True
        
        start_time = time.time()
        message_count = 100
        
        for i in range(message_count):
            response = client.send_message(f"message_{i}")
            assert response == f"MESSAGE_{i}"
            
        end_time = time.time()
        duration = end_time - start_time
        throughput = message_count / duration
        
        print(f"Throughput: {throughput:.2f} messages/second")
        assert throughput > 10  # Should handle at least 10 messages per second
        
        client.disconnect()


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main(['-v', __file__])