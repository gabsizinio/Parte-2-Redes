import socket
import threading

# Configurações do servidor
HOST = '127.0.0.2'  # Endereço IP do servidor (localhost)
PORT = 12345        # Porta onde o servidor ouvirá conexões
FORMAT = "utf-8"

# Listas para armazenar informações dos clientes conectados
clients = []    # Lista de sockets dos clientes conectados
usernames = []  # Lista de nomes de usuários correspondentes

fileno = 0
idx = 0

passwords = {
    "admin": "admin",
    "dely": "1234",
    "arthur": "4321",
    "gabriel": "senha",
    "victor": "123456",
}

def broadcast(message, exclude_client=None, private=False, private_client=None):
    """
    Envia mensagens para todos os clientes conectados, exceto o cliente que gerou a mensagem.
    
    Args:
    - message (bytes): Mensagem a ser enviada.
    - exclude_client (socket, optional): Cliente a ser excluído do envio.
    - private (bool, optional): Se a mensagem é privada.
    - private_client (socket, optional): Cliente que receberá a mensagem privada.
    """
    if private:
        private_client.send(message)
        return 

    for client in clients:   
        if client != exclude_client:  # Não envia a mensagem ao cliente que gerou o evento
            client.send(message)

def broadcast_tcp(message, exclude_client=None, username=None, password=None, private=False, private_client=None):
    """
    Envia mensagens para todos os clientes conectados, exceto o cliente que gerou a mensagem.
    
    Args:
    - message (bytes): Mensagem a ser enviada.
    - exclude_client (socket, optional): Cliente a ser excluído do envio.
    - username (str, optional): Nome de usuário para verificar login.
    - password (str, optional): Senha do usuário para autenticação.
    - private (bool, optional): Se a mensagem é privada.
    - private_client (socket, optional): Cliente a receber a mensagem privada.
    """
    # Verificação de login e senha
    if username and password:
        if passwords.get(username) != password:
            return  # Senha incorreta, não envia a mensagem
    
    # Chama a função genérica de broadcast
    broadcast(message, exclude_client=exclude_client, private=private, private_client=private_client)

# Broadcast UDP modificado para incluir login, senha e mensagens privadas
def broadcast_udp(server_socket, message, exclude_address=None, username=None, password=None, private=False, private_address=None):
    """
    Envia mensagens para todos os clientes conectados, exceto o remetente (se especificado).
    
    Args:
    - server_socket (socket): O socket do servidor UDP.
    - message (bytes): A mensagem a ser enviada.
    - exclude_address (tuple, optional): Endereço (host, port) do cliente a ser excluído do envio.
    - username (str, optional): Nome de usuário para verificar login.
    - password (str, optional): Senha do usuário para autenticação.
    - private (bool, optional): Se a mensagem é privada.
    - private_address (tuple, optional): Endereço do cliente a receber a mensagem privada.
    """
    # Verificação de login e senha
    if username and password:
        if passwords.get(username) != password:
            return  # Senha incorreta, não envia a mensagem
    
    if private:
        server_socket.sendto(message, private_address)
        return 

    # Envia para todos os clientes, exceto o remetente
    for client_address in clients:
        if client_address != exclude_address:
            server_socket.sendto(message, client_address)

# Função genérica de atualização da lista de usuários
def update_user_list(message, exclude_client=None, private=False, private_client=None):
    """
    Atualiza a lista de usuários online para todos os clientes conectados.
    Envia uma mensagem especial no formato "USERS:username1,username2,..." para todos.

    Args:
    - message (bytes): A mensagem a ser enviada.
    - exclude_client (socket, optional): Cliente a ser excluído do envio.
    - private (bool, optional): Se a mensagem é privada.
    - private_client (socket, optional): Cliente a receber a mensagem privada.
    """
    if private:
        private_client.send(message)
        return 

    for client in clients:   
        if client != exclude_client:  # Não envia a mensagem ao cliente que gerou o evento
            client.send(message)

# Função de atualização da lista de usuários online para TCP
def update_user_list_tcp(username=None, password=None, exclude_client=None, private=False, private_client=None):
    """
    Atualiza a lista de usuários online para todos os clientes conectados (TCP).
    Envia uma mensagem especial no formato "USERS:username1,username2,..." para todos os clientes.

    Args:
    - username (str, optional): Nome de usuário para verificação de login.
    - password (str, optional): Senha do usuário para autenticação.
    - exclude_client (socket, optional): Cliente a ser excluído do envio.
    - private (bool, optional): Se a mensagem é privada.
    - private_client (socket, optional): Cliente a receber a mensagem privada.
    """
    # Verificação de login e senha
    if username and password:
        if passwords.get(username) != password:
            return  # Senha incorreta, não envia a mensagem
    
    # Cria a mensagem da lista de usuários
    user_list_message = "USERS:" + ",".join(usernames)  # Formata a lista de usuários como string
    
    # Envia a mensagem utilizando a função genérica
    update_user_list(user_list_message.encode(FORMAT), exclude_client, private, private_client)

# Função de atualização da lista de usuários online para UDP
def update_user_list_udp(server_socket, username=None, password=None, exclude_address=None, private=False, private_address=None):
    """
    Atualiza a lista de usuários online para todos os clientes conectados (UDP).
    Envia uma mensagem especial no formato "USERS:username1,username2,..." para todos os clientes.

    Args:
    - server_socket (socket): O socket do servidor UDP.
    - username (str, optional): Nome de usuário para verificação de login.
    - password (str, optional): Senha do usuário para autenticação.
    - exclude_address (tuple, optional): Endereço (host, port) do cliente a ser excluído do envio.
    - private (bool, optional): Se a mensagem é privada.
    - private_address (tuple, optional): Endereço do cliente a receber a mensagem privada.
    """
    # Verificação de login e senha
    if username and password:
        if passwords.get(username) != password:
            return  # Senha incorreta, não envia a mensagem
    
    # Cria a mensagem da lista de usuários
    user_list = "USERS:" + ",".join(usernames)  # Formata a lista de usuários
    
    # Envia a mensagem para todos os clientes, exceto o remetente, ou para um cliente privado
    if private:
        server_socket.sendto(user_list.encode(FORMAT), private_address)
    else:
        for client_address in clients:
            if client_address != exclude_address:
                server_socket.sendto(user_list.encode(FORMAT), client_address)

def handle_client(client):
    """
    Gerencia a comunicação com um cliente (TCP ou UDP).
    """
    global fileno
    while True:
        try:
            message = client.recv(1024)  # Limite do tamanho da mensagem 1024
            if not message:
                break  # Se não receber mensagem, encerra o loop

            # Verifica se a mensagem é um arquivo
            if message.startswith(b"FILE:"):
                print("Envio de arquivo iniciado")

                filename = message[5:].decode(FORMAT)
                fileno += 1
                full_filename = f'output{fileno}.txt'

                with open(full_filename, "wb") as fo:
                    while True:
                        message = client.recv(1024)
                        if not message:
                            break
                        fo.write(message)

                print(f'Arquivo recebido com sucesso! Nome do novo arquivo: {full_filename}')
                # Notifica os usuários do arquivo recebido
                broadcast(f"A new file has been uploaded: {full_filename}".encode(FORMAT), exclude_client=client)
            else:
                # Verificação de login e senha
                decoded_message = message.decode(FORMAT)
                username = decoded_message.split(" ")[0]  # Primeiro elemento é o nome de usuário

                # Verifica se a senha está correta
                if passwords.get(username) != decoded_message.split(" ")[1]:  # Verifica senha
                    continue  # Se a senha for incorreta, não faz nada

                private = False
                private_client = None
                if decoded_message.startswith("@"):
                    private = True
                    private_client = clients[usernames.index(decoded_message.split(" ")[0][1:])]
                    decoded_message = decoded_message.split(" ", 1)[1]  # Retira o "@nome" e deixa a mensagem

                # Formatação da mensagem para incluir o nome de usuário
                index = clients.index(client)
                username = usernames[index]
                formatted_message = f"{username}: {decoded_message}"

                # Envia a mensagem para todos ou um cliente privado
                broadcast(formatted_message.encode(FORMAT), exclude_client=client, private=private, private_client=private_client)

        except Exception as e:
            print(f"Erro: {e}")
            # Em caso de erro, remove o cliente da lista
            index = clients.index(client)
            clients.remove(client)
            username = usernames.pop(index)
            client.close()
            print(f"{username} saiu do chat.")
            update_user_list()
            break

def handle_client_tcp(client):
    """
    Gerencia a comunicação com um cliente TCP específico.
    Lida com mensagens enviadas pelo cliente e desconexões.
    
    Args:
    - client (socket): O socket do cliente conectado.
    """
    global fileno
    while True:
        try:
            message = client.recv(1024)  # Limite do tamanho da mensagem 1024
            if not message:
                break  # Se não receber mensagem, encerra o loop

            # Verifica se a mensagem é um arquivo (prefixo FILE:)
            if message.startswith(b"FILE:"):
                print("Envio de arquivo iniciado")

                filename = message[5:].decode(FORMAT)
                fileno += 1
                full_filename = f'output{fileno}.txt'

                with open(full_filename, "wb") as fo:
                    while True:
                        message = client.recv(1024)
                        if not message:
                            break
                        fo.write(message)

                print(f'Arquivo recebido com sucesso! Nome do novo arquivo: {full_filename}')
                # Notifica os usuários do arquivo recebido
                broadcast_tcp(f"A new file has been uploaded: {full_filename}".encode(FORMAT), exclude_client=client)
            else:
                # Verificação de login e senha
                decoded_message = message.decode(FORMAT)
                username = decoded_message.split(" ")[0]  # Primeiro elemento é o nome de usuário

                # Verifica se a senha está correta
                if passwords.get(username) != decoded_message.split(" ")[1]:  # Verifica senha
                    continue  # Se a senha for incorreta, não faz nada

                private = False
                private_client = None
                if decoded_message.startswith("@"):
                    private = True
                    private_client = clients[usernames.index(decoded_message.split(" ")[0][1:])]
                    decoded_message = decoded_message.split(" ", 1)[1]  # Retira o "@nome" e deixa a mensagem

                # Formatação da mensagem para incluir o nome de usuário
                index = clients.index(client)
                username = usernames[index]
                formatted_message = f"{username}: {decoded_message}"

                # Envia a mensagem para todos ou um cliente privado
                broadcast_tcp(formatted_message.encode(FORMAT), exclude_client=client, private=private, private_client=private_client)

        except Exception as e:
            print(f"Erro: {e}")
            # Em caso de erro, remove o cliente da lista
            index = clients.index(client)
            clients.remove(client)
            username = usernames.pop(index)
            client.close()
            print(f"{username} saiu do chat.")
            update_user_list_tcp()
            break


def handle_client_udp(server_socket):
    """
    Gerencia a comunicação com clientes via UDP.
    Lida com mensagens enviadas pelos clientes e mensagens de arquivo.

    Args:
    - server_socket (socket): O socket do servidor configurado para UDP.
    """
    print("Servidor UDP está pronto para receber mensagens.")
    
    while True:
        try:
            # Recebe mensagens do cliente (mensagem + endereço do cliente)
            message, client_address = server_socket.recvfrom(1024)  # Limita a mensagem a 1024 bytes
            if not message:
                continue  # Ignora mensagens vazias

            # Verifica se a mensagem é um arquivo (usando um prefixo)
            if message.startswith(b"FILE:"):
                print(f"Recebendo arquivo do cliente {client_address}")

                # Extrai nome do arquivo e incrementa contagem
                filename = f"output_{client_address[0]}_{client_address[1]}.txt"
                with open(filename, "wb") as file:
                    while message:
                        # Escreve o conteúdo do arquivo
                        file.write(message)
                        # Recebe o próximo pedaço do arquivo
                        message, client_address = server_socket.recvfrom(1024)
                        if not message:
                            break

                print(f"Arquivo recebido com sucesso! Novo arquivo salvo como: {filename}")

            else:
                # Verificação de login e senha
                decoded_message = message.decode('utf-8')
                username = decoded_message.split(" ")[0]  # Primeiro elemento é o nome de usuário

                # Verifica se a senha está correta
                if passwords.get(username) != decoded_message.split(" ")[1]:  # Verifica senha
                    continue  # Se a senha for incorreta, não faz nada

                private = False
                private_address = None
                if decoded_message.startswith("@"):
                    private = True
                    private_address = clients[usernames.index(decoded_message.split(" ")[0][1:])]
                    decoded_message = decoded_message.split(" ", 1)[1]  # Retira o "@nome" e deixa a mensagem

                # Formatação da mensagem para difusão
                formatted_message = f"{client_address}: {decoded_message}"

                # Envia a mensagem para todos ou um cliente privado
                broadcast_udp(server_socket, formatted_message.encode('utf-8'), client_address, private, private_address)

        except Exception as e:
            print(f"Erro: {e}")
            continue

def receive_connections():
    """
    Aceita conexões de clientes e inicia uma thread para gerenciar cada conexão.
    """
    print("Servidor ativo e aguardando conexões...")
    while True:
        # Aceita uma nova conexão
        client, address = server.accept()
        print(f"Conexão estabelecida com {address}")

        # Solicita o nome de usuário do cliente
        ans = client.recv(1024).decode(FORMAT)  # Recebe o nome de usuário do cliente

        # O nome de usuário vem junto com a senha, separados por um ":"
        username = ans.split(":")[0]  # Pega o nome de usuário, que é a primeira parte da mensagem
        password = ans.split(":")[1]  # Pega a senha, que é a segunda parte da mensagem

        # Verifica se o nome de usuário já está em uso
        if username in usernames:
            client.send("ERRO: Nome de usuário já está em uso.".encode(FORMAT))
            print(f"Usuário {username} tentou entrar com nome já em uso.")
            client.close()  # Fecha a conexão caso o nome já esteja em uso
            continue

        # Verifica se a senha está correta
        elif passwords[username] != password:
            client.send("ERRO: Senha incorreta.".encode(FORMAT))
            print(f"Usuário {username} tentou entrar com senha incorreta.")
            
        else:
            client.send("OK".encode(FORMAT))

            # Adiciona o cliente à lista de conexões
            usernames.append(username)  # Adiciona o nome de usuário à lista
            clients.append(client)  # Adiciona o socket à lista de clientes

            print(f"Usuário {username} entrou no chat.")  # Loga a entrada do usuário
            update_user_list()  # Atualiza a lista de usuários online para todos os clientes

            # Cria uma thread para gerenciar a comunicação com o cliente
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()

def receive_connections_tcp():
    """
    Aceita conexões de clientes e inicia uma thread para gerenciar cada conexão.
    """
    print("Servidor ativo e aguardando conexões...")
    while True:
        # Aceita uma nova conexão
        client, address = server.accept()
        print(f"Conexão estabelecida com {address}")

        # Solicita o nome de usuário do cliente
        client.send("USERNAME".encode(FORMAT))  # Envia uma solicitação para o cliente
        username = client.recv(1024).decode(FORMAT)  # Recebe o nome de usuário do cliente

        # Verifica se o nome de usuário já está em uso
        if username in usernames:
            client.send("ERRO: Nome de usuário já está em uso.".encode(FORMAT))
            client.close()  # Fecha a conexão caso o nome já esteja em uso
            continue

        # Adiciona o cliente à lista de conexões
        usernames.append(username)  # Adiciona o nome de usuário à lista
        clients.append(client)  # Adiciona o socket à lista de clientes

        print(f"Usuário {username} entrou no chat.")  # Loga a entrada do usuário
        update_user_list_tcp()  # Atualiza a lista de usuários online para todos os clientes

        # Cria uma thread para gerenciar a comunicação com o cliente
        thread = threading.Thread(target=handle_client_tcp, args=(client,))
        thread.start()

def receive_messages_udp(server_socket):
    """
    Gerencia a recepção de mensagens de clientes via UDP.
    Como o UDP não tem conexões persistentes, ele apenas recebe datagramas e responde conforme necessário.
    """
    print("Servidor UDP ativo e aguardando mensagens...")

    while True:
        try:
            # Recebe uma mensagem do cliente (dados e endereço do cliente)
            message, client_address = server_socket.recvfrom(1024)  # Limita a mensagem a 1024 bytes

            # Verifica se o cliente já está na lista de clientes conhecidos
            if client_address not in clients:
                # Solicita o nome de usuário para novos clientes
                server_socket.sendto("USERNAME".encode(FORMAT), client_address)
                username_message, _ = server_socket.recvfrom(1024)
                username = username_message.decode(FORMAT)

                # Verifica se o nome de usuário já está em uso
                if username in usernames:
                    server_socket.sendto("ERRO: Nome de usuário já está em uso.".encode(FORMAT), client_address)
                    continue  # Ignora este cliente

                # Adiciona o cliente à lista de usuários e clientes conhecidos
                usernames.append(username)
                clients.append(client_address)
                print(f"Usuário {username} conectado a partir de {client_address}.")

                # Atualiza a lista de usuários para todos os clientes
                update_user_list_udp(server_socket)

            # Processa mensagens recebidas
            decoded_message = message.decode(FORMAT)
            print(f"Mensagem recebida de {client_address}: {decoded_message}")

            # Difunde a mensagem para todos os clientes, exceto o remetente
            formatted_message = f"{usernames[clients.index(client_address)]}: {decoded_message}"
            broadcast_udp(server_socket, formatted_message.encode(FORMAT), exclude_address=client_address)

        except Exception as e:
            print(f"Erro: {e}")
            continue

"""Inicializa o servidor, permitindo escolher entre TCP e UDP."""
choice = input("Escolha o tipo de conexão do servidor (TCP/UDP): ").strip().upper()
if choice == "TCP":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Servidor TCP iniciado em {HOST}:{PORT}")
    receive_connections_tcp()
elif choice == "UDP":
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    print(f"Servidor UDP iniciado em {HOST}:{PORT}")
    receive_messages_udp(server)
else:
    print("Escolha inválida. Por favor, escolha entre 'TCP' ou 'UDP'.")