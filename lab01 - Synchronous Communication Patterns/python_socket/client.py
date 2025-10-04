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


class SocketClient:
    """TCP Socket Client for communicating with server."""
    
    def __init__(self, host: str = 'localhost', port: int = 8080, timeout: float = 5.0):
        """
        Initialize the socket client.
        
        Args:
            host: Server host address
            port: Server port number
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client_socket: Optional[socket.socket] = None
        
    def connect(self) -> bool:
        """
        Establish connection to server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create TCP socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(self.timeout)
            
            # Connect to server
            self.client_socket.connect((self.host, self.port))
            logger.info(f"Connected to server at {self.host}:{self.port}")
            return True
            
        except socket.timeout:
            logger.error(f"Connection timeout to {self.host}:{self.port}")
            return False
        except ConnectionRefusedError:
            logger.error(f"Connection refused by {self.host}:{self.port}")
            return False
        except socket.gaierror as e:
            logger.error(f"Name resolution error: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
            
    def send_message(self, message: str) -> Optional[str]:
        """
        Send message to server and wait for response.
        
        Args:
            message: Message to send to server
            
        Returns:
            Server response or None if error occurred
        """
        if not self.client_socket:
            logger.error("Not connected to server")
            return None
            
        try:
            # Send message to server
            self.client_socket.send(message.encode('utf-8'))
            logger.info(f"Sent: {message}")
            
            # Receive response from server
            response_data = self.client_socket.recv(1024)
            if not response_data:
                logger.error("Server closed connection")
                return None
                
            response = response_data.decode('utf-8')
            logger.info(f"Received: {response}")
            return response
            
        except socket.timeout:
            logger.error("Response timeout from server")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Invalid UTF-8 response from server: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
            
    def disconnect(self):
        """Close connection to server."""
        if self.client_socket:
            try:
                self.client_socket.close()
                logger.info("Disconnected from server")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.client_socket = None
                
    def send_single_message(self, message: str) -> Optional[str]:
        """
        Connect, send a single message, get response, and disconnect.
        
        Args:
            message: Message to send
            
        Returns:
            Server response or None if error occurred
        """
        try:
            if not self.connect():
                return None
                
            response = self.send_message(message)
            return response
            
        finally:
            self.disconnect()
            
    def interactive_mode(self):
        """Run client in interactive mode for multiple messages."""
        print("Socket Client - Interactive Mode")
        print("Type 'quit' or 'exit' to disconnect")
        print("-" * 40)
        
        if not self.connect():
            return
            
        try:
            while True:
                try:
                    # Get user input
                    message = input("Enter message: ").strip()
                    
                    # Check for quit commands
                    if message.lower() in ['quit', 'exit', 'q']:
                        print("Goodbye!")
                        break
                        
                    if not message:
                        print("Please enter a non-empty message")
                        continue
                        
                    # Send message and get response
                    response = self.send_message(message)
                    if response is None:
                        print("Failed to get response from server")
                        break
                        
                    print(f"Server response: {response}")
                    
                except KeyboardInterrupt:
                    print("\nInterrupted by user")
                    break
                except EOFError:
                    print("\nEnd of input")
                    break
                    
        finally:
            self.disconnect()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='TCP Socket Client')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--timeout', type=float, default=5.0, help='Connection timeout (default: 5.0)')
    parser.add_argument('--message', '-m', help='Send single message and exit')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create client
    client = SocketClient(args.host, args.port, args.timeout)
    
    try:
        if args.message:
            # Single message mode
            response = client.send_single_message(args.message)
            if response:
                print(f"Server response: {response}")
                sys.exit(0)
            else:
                print("Failed to send message")
                sys.exit(1)
                
        elif args.interactive:
            # Interactive mode
            client.interactive_mode()
            
        else:
            # Default: read from stdin or prompt for message
            if sys.stdin.isatty():
                message = input("Enter message to send: ").strip()
                if not message:
                    print("No message provided")
                    sys.exit(1)
            else:
                message = sys.stdin.read().strip()
                
            response = client.send_single_message(message)
            if response:
                print(response)
                sys.exit(0)
            else:
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Client error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()