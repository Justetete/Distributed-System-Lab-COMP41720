#!/usr/bin/env python3
"""
Test Suite for TCP Socket Implementation
Tests connection establishment, message exchange, and error handling.
"""

import unittest
import socket
import threading
import time
import sys
import os
from unittest.mock import patch, MagicMock

# Add the current directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the server and client classes for testing
class MockTCPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
    def start_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        self.running = True
        
        while self.running:
            try:
                self.socket.settimeout(1)  # Short timeout for testing
                connection, client_address = self.socket.accept()
                self._handle_client(connection)
            except socket.timeout:
                continue
            except:
                break
                
    def _handle_client(self, connection):
        try:
            data = connection.recv(1024)
            if data:
                # Echo the message back
                connection.sendall(data)
        finally:
            connection.close()
            
    def stop_server(self):
        self.running = False
        if self.socket:
            self.socket.close()

class TestTCPSocketImplementation(unittest.TestCase):
    """Test cases for TCP socket implementation"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.server = MockTCPServer('localhost', 8081)  # Use different port for testing
        self.server_thread = None
        
    def tearDown(self):
        """Clean up after each test method"""
        if self.server_thread:
            self.server.stop_server()
            self.server_thread.join(timeout=2)
            
    def start_test_server(self):
        """Start the test server in a separate thread"""
        self.server_thread = threading.Thread(target=self.server.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(0.1)  # Give server time to start
        
    def test_connection_establishment(self):
        """Test 1: Socket connection establishment"""
        print("\n=== Test 1: Connection Establishment ===")
        
        self.start_test_server()
        
        # Test successful connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        
        try:
            client_socket.connect(('localhost', 8081))
            print("✓ Connection established successfully")
            self.assertTrue(True)  # Connection successful
        except Exception as e:
            self.fail(f"Connection failed: {e}")
        finally:
            client_socket.close()
            
    def test_message_sending_receiving(self):
        """Test 2: Message sending and receiving"""
        print("\n=== Test 2: Message Sending/Receiving ===")
        
        self.start_test_server()
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        
        try:
            client_socket.connect(('localhost', 8081))
            
            # Test message exchange
            test_message = "Hello, Server!"
            client_socket.sendall(test_message.encode('utf-8'))
            
            # Receive echo
            response = client_socket.recv(1024)
            received_message = response.decode('utf-8')
            
            print(f"✓ Sent: '{test_message}'")
            print(f"✓ Received: '{received_message}'")
            
            self.assertEqual(test_message, received_message)
            
        except Exception as e:
            self.fail(f"Message exchange failed: {e}")
        finally:
            client_socket.close()
            
    def test_multiple_messages(self):
        """Test 3: Multiple message exchange"""
        print("\n=== Test 3: Multiple Message Exchange ===")
        
        self.start_test_server()
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        
        try:
            client_socket.connect(('localhost', 8081))
            
            messages = ["Message 1", "Message 2", "Message 3"]
            
            for i, msg in enumerate(messages, 1):
                client_socket.sendall(msg.encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                print(f"✓ Message {i}: Sent '{msg}', Received '{response}'")
                self.assertEqual(msg, response)
                
        except Exception as e:
            self.fail(f"Multiple message exchange failed: {e}")
        finally:
            client_socket.close()
            
    def test_invalid_connection_handling(self):
        """Test 4: Error handling for invalid connections"""
        print("\n=== Test 4: Invalid Connection Handling ===")
        
        # Test connection to non-existent server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(2)
        
        with self.assertRaises((socket.error, ConnectionRefusedError)):
            client_socket.connect(('localhost', 9999))  # Non-existent server
            
        print("✓ Invalid connection properly rejected")
        client_socket.close()
        
    def test_connection_timeout(self):
        """Test 5: Connection timeout handling"""
        print("\n=== Test 5: Connection Timeout ===")
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(1)  # Short timeout
        
        # Try to connect to a non-routable address (should timeout)
        with self.assertRaises(socket.timeout):
            client_socket.connect(('10.255.255.1', 8080))
            
        print("✓ Connection timeout handled properly")
        client_socket.close()
        
    def test_large_message_handling(self):
        """Test 6: Large message handling"""
        print("\n=== Test 6: Large Message Handling ===")
        
        self.start_test_server()
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)
        
        try:
            client_socket.connect(('localhost', 8081))
            
            # Create a large message
            large_message = "A" * 500  # 500 characters
            client_socket.sendall(large_message.encode('utf-8'))
            
            # Receive the echo (may need multiple recv calls)
            received_data = b''
            while len(received_data) < len(large_message):
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                received_data += chunk
                
            received_message = received_data.decode('utf-8')
            
            print(f"✓ Large message ({len(large_message)} chars) sent and received")
            self.assertEqual(large_message, received_message)
            
        except Exception as e:
            self.fail(f"Large message handling failed: {e}")
        finally:
            client_socket.close()
            
    def test_encoding_handling(self):
        """Test 7: Character encoding handling"""
        print("\n=== Test 7: Character Encoding ===")
        
        self.start_test_server()
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        
        try:
            client_socket.connect(('localhost', 8081))
            
            # Test with special characters
            special_message = "Hello 世界! 🌍"
            encoded_msg = special_message.encode('utf-8')
            client_socket.sendall(encoded_msg)
            
            response = client_socket.recv(1024)
            received_message = response.decode('utf-8')
            
            print(f"✓ Special characters: Sent '{special_message}', Received '{received_message}'")
            self.assertEqual(special_message, received_message)
            
        except Exception as e:
            self.fail(f"Encoding handling failed: {e}")
        finally:
            client_socket.close()

class TestPerformance(unittest.TestCase):
    """Performance tests for the socket implementation"""
    
    def setUp(self):
        self.server = MockTCPServer('localhost', 8082)
        self.server_thread = threading.Thread(target=self.server.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(0.1)
        
    def tearDown(self):
        self.server.stop_server()
        self.server_thread.join(timeout=2)
        
    def test_connection_speed(self):
        """Test connection establishment speed"""
        print("\n=== Performance Test: Connection Speed ===")
        
        start_time = time.time()
        
        # Test multiple rapid connections
        for i in range(10):
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            try:
                client_socket.connect(('localhost', 8082))
                client_socket.sendall(f"Message {i}".encode('utf-8'))
                response = client_socket.recv(1024)
            finally:
                client_socket.close()
                
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✓ 10 connections completed in {total_time:.3f} seconds")
        print(f"✓ Average time per connection: {total_time/10:.3f} seconds")
        
        # Should complete within reasonable time
        self.assertLess(total_time, 5.0)  # Should take less than 5 seconds

def run_manual_tests():
    """Run manual integration tests"""
    print("="*60)
    print("MANUAL INTEGRATION TESTS")
    print("="*60)
    
    print("\nTo run manual tests:")
    print("1. Start the server: python server.py")
    print("2. In another terminal, start the client: python client.py")
    print("3. Test various scenarios:")
    print("   - Send normal messages")
    print("   - Send 'hello' message")
    print("   - Send 'quit' to exit gracefully")
    print("   - Test Ctrl+C interruption")
    print("   - Test connection when server is down")

def main():
    """Main test runner"""
    print("="*60)
    print("TCP SOCKET IMPLEMENTATION TEST SUITE")
    print("="*60)
    
    # Run automated unit tests
    print("\nRunning automated tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run manual test instructions
    run_manual_tests()

if __name__ == '__main__':
    main()