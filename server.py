import socket
import threading
import logging
import os
from datetime import datetime

# Configurações do servidor
HOST = '127.0.0.2'  # Endereço IP do servidor (localhost)
PORT = 12345        # Porta onde o servidor ouvirá conexões
FORMAT = "utf-8"

# Configuração do log
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename=f"logs/server_{datetime.now().strftime('%Y-%m-%d')}.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Criação do socket do servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Socket TCP
server.bind((HOST, PORT))  # Associa o socket ao endereço e porta configurados
server.listen()  # Habilita o servidor para aceitar conexões

# Listas para armazenar informações dos clientes conectados
clients = []    # Lista de sockets dos clientes conectados
usernames = []  # Lista de nomes de usuários correspondentes

fileno = 0

# Mapa de senhas dos usuários
passwords = {
    "admin": "admin",
    "dely": "1234",
    "arthur": "4321",
    "gabriel": "senha",
    "victor": "123456",
    "juan": "123",
}


def broadcast(message, exclude_client=None, private=False, private_client=None):
    """
    Envia mensagens para todos os clientes conectados, exceto o cliente que gerou a mensagem.
    """
    if private:
        private_client.send(message)
        return

    for client in clients:
        if client != exclude_client:  # Não envia a mensagem ao cliente que gerou o evento
            client.send(message)


def update_user_list():
    """
    Atualiza a lista de usuários online para todos os clientes conectados.
    Envia uma mensagem especial no formato "USERS:username1,username2,..." para todos.
    """
    user_list_message = "USERS:" + ",".join(usernames)  # Formata a lista de usuários como string
    broadcast(user_list_message.encode(FORMAT))  # Envia a mensagem para todos os clientes


def handle_client(client):
    global fileno
    while True:
        try:
            message = client.recv(1024)  # Limite do tamanho da mensagem
            if not message:
                break

            if message.startswith(b"FILE:"):  # Verifica se mensagem é arquivo
                filename = message[5:].decode(FORMAT)
                fileno += 1
                full_filename = f'output{fileno}.txt'

                with open(full_filename, "wb") as fo:
                    while True:
                        message = client.recv(1024)
                        if not message:
                            break
                        fo.write(message)

                logging.info(f"Arquivo '{full_filename}' recebido e salvo com sucesso.")
                broadcast(f"A new file has been uploaded: {full_filename}".encode(FORMAT), exclude_client=client)

            else:
                # Difunde a mensagem para outros clientes
                decoded_message = message.decode(FORMAT)
                private = False
                private_client = None
                if decoded_message.startswith("@"):
                    private = True
                    private_client = clients[usernames.index(decoded_message.split(" ")[0][1:])]
                    decoded_message = decoded_message.split(" ", 1)[1]
                    decoded_message = f"(private) {decoded_message}"

                index = clients.index(client)
                username = usernames[index]
                formatted_message = f"{username}: {decoded_message}"

                logging.info(f"Mensagem de {username}: {decoded_message}")
                broadcast(formatted_message.encode(FORMAT), exclude_client=client, private=private, private_client=private_client)

        except Exception as e:
            logging.error(f"Erro no cliente: {e}")
            index = clients.index(client)
            clients.remove(client)
            username = usernames.pop(index)
            client.close()
            logging.info(f"{username} saiu do chat.")
            update_user_list()
            break


def receive_connections():
    """
    Aceita conexões de clientes e inicia uma thread para gerenciar cada conexão.
    """
    logging.info("Servidor ativo e aguardando conexões...")
    while True:
        client, address = server.accept()
        logging.info(f"Conexão estabelecida com {address}")

        ans = client.recv(1024).decode(FORMAT)
        username = ans.split(":")[0]
        password = ans.split(":")[1]

        if username in usernames:
            client.send("ERRO: Nome de usuário já está em uso.".encode(FORMAT))
            logging.warning(f"Usuário {username} tentou entrar com nome já em uso.")
            client.close()
            continue

        elif passwords.get(username) != password:
            client.send("ERRO: Senha incorreta.".encode(FORMAT))
            logging.warning(f"Usuário {username} tentou entrar com senha incorreta.")
            client.close()
            continue

        client.send("OK".encode(FORMAT))
        usernames.append(username)
        clients.append(client)
        logging.info(f"Usuário {username} entrou no chat.")
        update_user_list()

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


receive_connections()

