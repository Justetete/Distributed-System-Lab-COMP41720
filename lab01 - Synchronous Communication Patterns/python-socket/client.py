#!/usr/bin/env python3
"""
Enhanced TCP Client Implementation
Connects to server with proper error handling and message exchange capabilities.
"""

import socket
import sys
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TCPClient:
    def __init__(self, host: str = 'localhost', port: int = 8080, buffer_size: int = 1024):
        """
        Initialize TCP Client
        
        Args:
            host: Server host address
            port: Server port number
            buffer_size: Buffer size for receiving data
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
        
    def connect(self) -> bool:
        """
        Connect to the server
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create TCP/IP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set connection timeout
            self.socket.settimeout(10)  # 10 seconds timeout
            
            # Connect to server
            server_address = (self.host, self.port)
            logger.info(f"Connecting to {self.host}:{self.port}")
            self.socket.connect(server_address)
            
            logger.info("Successfully connected to server")
            return True
            
        except socket.timeout:
            logger.error("Connection timeout")
            return False
        except socket.error as e:
            logger.error(f"Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected connection error: {e}")
            return False
            
    def send_message(self, message: str) -> Optional[str]:
        """
        Send message to server and receive response
        
        Args:
            message: Message to send to server
            
        Returns:
            Server response or None if error occurred
        """
        if not self.socket:
            logger.error("Not connected to server")
            return None
            
        try:
            # Send message to server
            logger.info(f"Sending message: '{message}'")
            message_bytes = message.encode('utf-8')
            self.socket.sendall(message_bytes)
            
            # Receive response from server
            response = self._receive_full_message(len(message_bytes))
            
            if response:
                decoded_response = response.decode('utf-8')
                logger.info(f"Received response: '{decoded_response}'")
                return decoded_response
            else:
                logger.warning("No response received from server")
                return None
                
        except socket.timeout:
            logger.error("Send/receive timeout")
            return None
        except socket.error as e:
            logger.error(f"Socket error during message exchange: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during message exchange: {e}")
            return None
            
    def _receive_full_message(self, expected_length: int) -> Optional[bytes]:
        """
        Receive the complete message from server
        
        Args:
            expected_length: Expected length of the message
            
        Returns:
            Complete message bytes or None if error
        """
        received_data = b''
        bytes_received = 0
        
        # Continue receiving until we get the expected amount
        while bytes_received < expected_length:
            try:
                chunk = self.socket.recv(min(self.buffer_size, expected_length - bytes_received))
                if not chunk:
                    logger.warning("Connection closed by server")
                    break
                    
                received_data += chunk
                bytes_received += len(chunk)
                
            except socket.timeout:
                logger.error("Receive timeout")
                break
            except socket.error as e:
                logger.error(f"Error receiving data: {e}")
                break
                
        return received_data if bytes_received > 0 else None
    
    def interactive_session(self) -> None:
        """Start an interactive session with the server"""
        if not self.connect():
            logger.error("Failed to connect to server")
            return
            
        try:
            logger.info("Interactive session started. Type 'quit' to exit.")
            
            while True:
                try:
                    # Get user input
                    user_input = input("Enter message: ").strip()
                    
                    if not user_input:
                        print("Please enter a message")
                        continue
                        
                    # Send message and get response
                    response = self.send_message(user_input)
                    
                    if response:
                        print(f"Server response: {response}")
                        
                        # Check if server said goodbye
                        if "goodbye" in response.lower():
                            break
                    else:
                        print("Failed to get response from server")
                        break
                        
                except KeyboardInterrupt:
                    logger.info("Session interrupted by user")
                    break
                except EOFError:
                    logger.info("EOF received, ending session")
                    break
                    
        finally:
            self.disconnect()
            
    def send_single_message(self, message: str) -> Optional[str]:
        """
        Send a single message to server (connect, send, disconnect)
        
        Args:
            message: Message to send
            
        Returns:
            Server response or None
        """
        if self.connect():
            try:
                response = self.send_message(message)
                return response
            finally:
                self.disconnect()
        return None
    
    def disconnect(self) -> None:
        """Disconnect from server"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Disconnected from server")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.socket = None

def main():
    """Main function to run the client"""
    client = TCPClient(host='localhost', port=8080)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Send single message from command line
        message = ' '.join(sys.argv[1:])
        response = client.send_single_message(message)
        if response:
            print(f"Server response: {response}")
        else:
            print("Failed to communicate with server")
    else:
        # Start interactive session
        client.interactive_session()

if __name__ == "__main__":
    main()