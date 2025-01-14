import socket
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server_log.txt"),
        logging.StreamHandler()
    ]
)

# Store active clients
clients = {}
lock = threading.Lock()

def handle_client(client, address):
    global clients

    # Register the user
    client.send(b'Enter your username: ')
    username = client.recv(1024).decode()
    
    with lock:
        if username in clients:
            client.send(b'Username already taken. Disconnecting.')
            client.close()
            logging.warning(f'Username conflict: "{username}" from {address}')
            return
        clients[username] = client
        logging.info(f'User "{username}" connected from {address}')

    client.send(b'Welcome to the chat server! You can send messages in the format "@username message". Type "exit" to disconnect.')

    try:
        while True:
            message = client.recv(1024).decode()
            if message.lower() == 'exit':
                break

            if message.startswith('@'):
                # Private message
                target_username, _, msg = message[1:].partition(' ')
                with lock:
                    if target_username in clients:
                        clients[target_username].send(f'From {username}: {msg}'.encode())
                        logging.info(f'Message from "{username}" to "{target_username}": {msg}')
                    else:
                        client.send(b'User not found.')
                        logging.warning(f'Failed message from "{username}" to non-existent user "{target_username}"')
            else:
                client.send(b'Invalid message format. Use "@username message".')
                logging.warning(f'Invalid message format from "{username}": {message}')
    except ConnectionResetError:
        logging.error(f'Connection reset by user "{username}"')
    finally:
        with lock:
            del clients[username]
        logging.info(f'User "{username}" disconnected.')
        client.close()

# Server setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 12345))
server.listen(5)

logging.info('Server is running...')

# Accept clients
try:
    while True:
        client, address = server.accept()
        threading.Thread(target=handle_client, args=(client, address)).start()
        logging.info(f'Accepted connection from {address}')
except KeyboardInterrupt:
    logging.info('Server shutting down...')
finally:
    server.close()
