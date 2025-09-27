import socket

# Create a TCP/IP socket
my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to localhost:8080
# Bind the socket to the port
server_address = ('localhost', 8080)
print("Starting up on localhost port 8080") # Print setted port number
my_socket.bind(server_address)

# Listen for connections
my_socket.listen(1) # Listen one coming call

# While True:
while True:
    # Wait for a connection, Accept client connection
    print("Waiting for a connection-----")
    connection, client_address = my_socket.accept()

    try:
        print(f"Socket connection from {client_address}")

        # Receive the data in small chunks and retransmit it, Receive data from client
        while True:
            data = connection.recv(16)
            # 
            print(f"Server received [ {data.decode()} ]")
            if data:
                print("Server sending data back to the client")
                connection.sendall(data)
            else:
                print(f"no more data from {client_address}")
                break
            
    finally:
        # Clean up the connection
        connection.close()