import socket
import threading
import os
from cryptography.fernet import Fernet

# Geração e armazenamento da chave de criptografia
key = Fernet.generate_key()
cipher = Fernet(key)

# Lista de clientes conectados
clients = []

# Função para carregar os usuários registrados
def load_users():
    users = {}
    if os.path.exists('users.txt'):
        with open('users.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    login, password = line.split(':')
                    users[login] = password
    return users

# Função para salvar novos usuários
def save_user(login, password):
    with open('users.txt', 'a') as f:
        f.write(f'{login}:{password}\n')

# Função para lidar com mensagens de um cliente específico
def handle_client(client_socket, address):
    print(f"Nova conexão: {address}")
    client_socket.send(b"Digite 'login' para acessar ou 'register' para se cadastrar:")

    users = load_users()  # Carrega usuários registrados inicialmente

    while True:
        option = client_socket.recv(1024).decode().strip().lower()
        if option == 'register':
            client_socket.send(b"Escolha um login:")
            login = client_socket.recv(1024).decode().strip()
            if login in users:
                client_socket.send(b"Usuario ja existe. Tente novamente.\nDigite 'login' ou 'register':")
                continue
            client_socket.send(b"Escolha uma senha:")
            password = client_socket.recv(1024).decode().strip()
            save_user(login, password)
            users = load_users()  # Recarrega os usuários após cadastro
            client_socket.send(b"Cadastro concluido! Agora voce pode fazer login.\nDigite 'login' para continuar:")
        elif option == 'login':
            client_socket.send(b"Login:")
            login = client_socket.recv(1024).decode().strip()
            client_socket.send(b"Senha:")
            password = client_socket.recv(1024).decode().strip()
            if login in users and users[login] == password:
                client_socket.send(b"Login bem-sucedido! Bem-vindo ao chat.")
                break
            else:
                client_socket.send(b"Credenciais invalidas. Tente novamente.\nDigite 'login' ou 'register':")
        else:
            client_socket.send(b"Opcao invalida. Digite 'login' ou 'register':")
    
    print(f"Usuário {login} conectado.")
    clients.append(client_socket)
    client_socket.send(key)  # Envia a chave de criptografia ao cliente

    while True:
        try:
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break
            message = cipher.decrypt(encrypted_message).decode()
            message = message.encode('ascii', 'ignore').decode()  # Remove não ASCII
            print(f"[{login}] {message}")
            
            # Transmite a mensagem para todos os outros clientes
            for c in clients:
                if c != client_socket:
                    c.send(cipher.encrypt(f"[{login}] {message}".encode()))
        except Exception as e:
            print(f"Erro: {e}")
            break
    
    print(f"Usuário {login} desconectado.")
    clients.remove(client_socket)
    client_socket.close()

# Configuração do servidor
def main():
    host = '0.0.0.0'
    port = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor escutando em {host}:{port}")
    
    while True:
        client_socket, address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, address)).start()

if __name__ == '__main__':
    main()
