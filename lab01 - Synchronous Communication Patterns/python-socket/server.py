#!/usr/bin/env python3
"""
Enhanced TCP Server Implementation
Handles multiple client connections with proper error handling and logging.
"""

import socket
import sys
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TCPServer:
    def __init__(self, host: str = 'localhost', port: int = 8080, buffer_size: int = 1024):
        """
        Initialize TCP Server
        
        Args:
            host: Server host address
            port: Server port number  
            buffer_size: Buffer size for receiving data
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
        
    def start_server(self) -> None:
        """Start the TCP server and listen for connections"""
        try:
            # Create TCP/IP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Allow socket reuse (prevents "Address already in use" error)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address and port
            server_address = (self.host, self.port)
            self.socket.bind(server_address)
            logger.info(f"Server starting on {self.host}:{self.port}")
            
            # Listen for incoming connections (max 5 queued connections)
            self.socket.listen(5)
            logger.info("Server is listening for connections...")
            
            # Main server loop
            while True:
                try:
                    self._handle_client_connection()
                except KeyboardInterrupt:
                    logger.info("Server shutdown requested")
                    break
                except Exception as e:
                    logger.error(f"Error in main server loop: {e}")
                    continue
                    
        except socket.error as e:
            logger.error(f"Socket error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self._cleanup()
            
    def _handle_client_connection(self) -> None:
        """Handle individual client connection"""
        connection = None
        try:
            # Accept client connection
            logger.info("Waiting for connection...")
            connection, client_address = self.socket.accept()
            logger.info(f"Connection established from {client_address}")
            
            # Process client data
            self._process_client_data(connection, client_address)
            
        except socket.timeout:
            logger.warning("Connection timeout")
        except socket.error as e:
            logger.error(f"Socket error while handling client: {e}")
        finally:
            if connection:
                connection.close()
                logger.info("Client connection closed")
                
    def _process_client_data(self, connection: socket.socket, client_address: Tuple[str, int]) -> None:
        """
        Process data from client
        
        Args:
            connection: Client socket connection
            client_address: Client address tuple
        """
        try:
            while True:
                # Receive data from client
                data = connection.recv(self.buffer_size)
                
                if not data:
                    logger.info(f"No more data from {client_address}")
                    break
                    
                # Decode and process the message
                message = data.decode('utf-8').strip()
                logger.info(f"Received from {client_address}: '{message}'")
                
                # Process the data (echo back for now)
                processed_data = self._process_message(message)
                
                # Send response back to client
                response = processed_data.encode('utf-8')
                connection.sendall(response)
                logger.info(f"Sent response to {client_address}: '{processed_data}'")
                
        except socket.error as e:
            logger.error(f"Socket error while processing client data: {e}")
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {e}")
            # Send error response
            error_msg = "Error: Invalid message encoding"
            connection.sendall(error_msg.encode('utf-8'))
        except Exception as e:
            logger.error(f"Unexpected error while processing client data: {e}")
            
    def _process_message(self, message: str) -> str:
        """
        Process the received message (customize this method for your needs)
        
        Args:
            message: Received message from client
            
        Returns:
            Processed message to send back
        """
        # Simple echo server - customize this for your specific use case
        if message.lower() == 'quit':
            return "Server: Goodbye!"
        elif message.lower().startswith('hello'):
            return f"Server: Hello! You said: {message}"
        else:
            return f"Server: Echo - {message}"
    
    def _cleanup(self) -> None:
        """Clean up server resources"""
        if self.socket:
            self.socket.close()
            logger.info("Server socket closed")

def main():
    """Main function to run the server"""
    server = TCPServer(host='localhost', port=8080)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()