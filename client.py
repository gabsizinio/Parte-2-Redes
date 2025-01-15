import socket
import threading
from cryptography.fernet import Fernet

# Função para receber mensagens do servidor
def receive_messages(client_socket, cipher):
    while True:
        try:
            encrypted_message = client_socket.recv(1024)
            if encrypted_message:
                print(cipher.decrypt(encrypted_message).decode())
        except Exception as e:
            print(f"Erro: {e}")
            break

def main():
    host = '127.0.0.1'  # Endereço do servidor
    port = 12345        # Porta do servidor
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    # Escolher entre login e cadastro
    print(client_socket.recv(1024).decode())
    while True:
        option = input("Digite 'login' para acessar ou 'register' para se cadastrar: ").strip().lower()
        client_socket.send(option.encode())
        response = client_socket.recv(1024).decode()
        print(response)
        
        if option == 'register':
            if "Escolha um login:" in response:
                login = input("Login: ")
                client_socket.send(login.encode())
                response = client_socket.recv(1024).decode()
                print(response)
                if "Escolha uma senha:" in response:
                    password = input("Senha: ")
                    client_socket.send(password.encode())
                    response = client_socket.recv(1024).decode()
                    print(response)
        
        elif option == 'login':
            if "Login:" in response:
                login = input("Login: ")
                client_socket.send(login.encode())
                response = client_socket.recv(1024).decode()
                print(response)
                if "Senha:" in response:
                    password = input("Senha: ")
                    client_socket.send(password.encode())
                    response = client_socket.recv(1024).decode()
                    print(response)
                    if "Login bem-sucedido!" in response:
                        break
        else:
            print("Opção inválida. Tente novamente.")
    
    # Recebe a chave de criptografia do servidor
    key = client_socket.recv(1024)
    cipher = Fernet(key)

    # Inicia thread para receber mensagens
    threading.Thread(target=receive_messages, args=(client_socket, cipher), daemon=True).start()

    print("Conexão estabelecida. Digite suas mensagens:")
    try:
        while True:
            message = input()
            encrypted_message = cipher.encrypt(message.encode())
            client_socket.send(encrypted_message)
            if message.lower() == 'exit':
                break
    except KeyboardInterrupt:
        print("Desconectado.")
    finally:
        client_socket.close()

if __name__ == '__main__':
    main()
