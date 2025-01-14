import socket
import threading

def receive_messages(client):
    while True:
        try:
            response = client.recv(1024).decode()
            print(response)
        except ConnectionResetError:
            print('Disconnected from server.')
            break

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 12345))

# Start a thread to receive messages
threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

# Send username
print(client.recv(1024).decode())
username = input()
client.send(username.encode())

# Chat loop
try:
    while True:
        message = input()
        client.send(message.encode())
        if message.lower() == 'exit':
            break
except KeyboardInterrupt:
    print('Disconnected.')
finally:
    client.close()
