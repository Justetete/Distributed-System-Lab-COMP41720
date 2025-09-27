import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('localhost', 8080)
print("Connecting to localhost port 8080")
sock.connect(server_address)

try:
    # Send data
    message = 'This is the message. It will be repeated.'
    print(f"Client is sending {message}")
    sock.sendall(message.encode()) # sendall function to send message
    # Noticed: the message need to be encoded!

    # Look for the response
    amount_received = 0
    amount_expected = len(message)
    
    while amount_received < amount_expected:
        data = sock.recv(16)
        amount_received += len(data)
        print(f"Server received [ {data} ]")

finally:
    print(f"Client is closing socket!!!")
    sock.close()