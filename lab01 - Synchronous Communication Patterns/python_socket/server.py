import socket
import threading
import signal
import sys
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SocketServer:
    """TCP Socket Server with graceful shutdown support."""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        """
        Initialize the socket server.
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.client_threads = []
        
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
        
    def start(self):
        """Start the socket server."""
        try:
            # Create TCP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Allow socket reuse
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address
            self.server_socket.bind((self.host, self.port))
            logger.info(f"Server bound to {self.host}:{self.port}")
            
            # Listen for connections (max 5 pending connections)
            self.server_socket.listen(5)
            logger.info("Server listening for connections...")
            
            self.running = True
            self.setup_signal_handlers()
            
            # Main server loop
            while self.running:
                try:
                    # Accept client connection
                    client_socket, client_address = self.server_socket.accept()
                    logger.info(f"New connection from {client_address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    self.client_threads.append(client_thread)
                    
                except socket.error as e:
                    if self.running:  # Only log if not shutting down
                        logger.error(f"Socket error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()
            
    def _handle_client(self, client_socket: socket.socket, client_address: tuple):
        """
        Handle individual client connection.
        
        Args:
            client_socket: Client socket connection
            client_address: Client address tuple
        """
        try:
            with client_socket:
                while True:
                    # Receive data from client
                    data = client_socket.recv(1024)
                    if not data:
                        logger.info(f"Client {client_address} disconnected")
                        break
                        
                    # Decode message
                    message = data.decode('utf-8').strip()
                    logger.info(f"Received from {client_address}: {message}")
                    
                    # Process message (convert to uppercase)
                    response = self._process_message(message)
                    
                    # Send response back to client
                    client_socket.send(response.encode('utf-8'))
                    logger.info(f"Sent to {client_address}: {response}")
                    
        except socket.error as e:
            logger.error(f"Error handling client {client_address}: {e}")
        except UnicodeDecodeError as e:
            logger.error(f"Invalid UTF-8 data from {client_address}: {e}")
            try:
                error_response = "ERROR: Invalid UTF-8 encoding"
                client_socket.send(error_response.encode('utf-8'))
            except:
                pass
        except Exception as e:
            logger.error(f"Unexpected error with client {client_address}: {e}")
        finally:
            logger.info(f"Connection with {client_address} closed")
            
    def _process_message(self, message: str) -> str:
        """
        Process incoming message and return response.
        
        Args:
            message: Input message from client
            
        Returns:
            Processed response message
        """
        if not message:
            return "ERROR: Empty message"
            
        # Simple transformation: convert to uppercase
        return message.upper()
        
    def shutdown(self):
        """Gracefully shutdown the server."""
        logger.info("Shutting down server...")
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")
                
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up server resources...")
        
        # Wait for client threads to finish (with timeout)
        for thread in self.client_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
                
        logger.info("Server shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='TCP Socket Server')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start server
    server = SocketServer(args.host, args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()