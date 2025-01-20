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

def broadcast_tcp(message, exclude_client=None):
    """
    Envia mensagens para todos os clientes conectados, exceto o cliente que gerou a mensagem.
    
    Args:
    - message (bytes): Mensagem a ser enviada.
    - exclude_client (socket, optional): Cliente a ser excluído do envio.
    """
    for client in clients:   
        if client != exclude_client:  # Não envia a mensagem ao cliente que gerou o evento
            client.send(message)

def broadcast_udp(server_socket, message, exclude_address=None):
    """
    Envia mensagens para todos os clientes conectados, exceto o remetente (se especificado).

    Args:
    - server_socket (socket): O socket do servidor UDP.
    - message (bytes): A mensagem a ser enviada.
    - exclude_address (tuple): Endereço (host, port) do cliente a ser excluído do envio.
    """
    for client_address in clients:
        if client_address != exclude_address:
            server_socket.sendto(message, client_address)

def update_user_list_tcp():
    """
    Atualiza a lista de usuários online para todos os clientes conectados.
    Envia uma mensagem especial no formato "USERS:username1,username2,..." para todos.
    """
    user_list_message = "USERS:" + ",".join(usernames)  # Formata a lista de usuários como string
    broadcast_tcp(user_list_message.encode(FORMAT))  # Envia a mensagem para todos os clientes

def update_user_list_udp(server_socket):
    """
    Atualiza a lista de usuários online e envia para todos os clientes.

    Args:
    - server_socket (socket): O socket do servidor UDP.
    """
    user_list = "USERS:" + ",".join(usernames)  # Formata a lista de usuários
    for client_address in clients:
        server_socket.sendto(user_list.encode(FORMAT), client_address)

def handle_client_tcp(client):
    """
    Gerencia a comunicação com um cliente específico.
    Lida com mensagens enviadas pelo cliente e desconexões.
    
    Args:
    - client (socket): O socket do cliente conectado.
    """
    while True:
        try:
            # Recebe mensagens do cliente
            message = client.recv(1024)  # Limita a mensagem a 1024 bytes  # adicionei o decode
            
            if not message:
                break        
            
            if message.startswith(b"FILE:"): #check if is file

                print("entrou")
                # Creating a new file at server end and writing the data 
                filename = 'output'+str(fileno)+'.txt'
                fileno = fileno+1
                fo = open(filename, "w") 
                
                while message: 
                    if not message: 
                        break
                    else: 
                        fo.write(message) 
                        message = client.recv(1024).decode(FORMAT)
                print()
                print('Received successfully! New filename is:', filename) 
                fo.close() 
            
            else:    
                 # Decode the message before formatting

                decoded_message = message.decode(FORMAT)  

                # Difunde a mensagem para outros clientes

                index = clients.index(client)
                username = usernames[index]

                # Inclui o autor na mensagem
                formatted_message = f"{username}: {decoded_message}"

                broadcast_tcp(formatted_message.encode(FORMAT), exclude_client=client)
        except:
            print(message)
            # Em caso de erro, remove o cliente da lista
            index = clients.index(client)  # Localiza o índice do cliente na lista
            clients.remove(client)  # Remove o cliente da lista de sockets
            username = usernames.pop(index)  # Remove o nome de usuário correspondente
            client.close()  # Fecha o socket do cliente
            print(f"{username} saiu do chat.")  # Loga no servidor
            update_user_list_tcp()  # Atualiza a lista de usuários online para todos
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
            # Recebe mensagens dos clientes (mensagem + endereço do cliente)
            message, client_address = server_socket.recvfrom(1024)  # Limita a mensagem a 1024 bytes

            if not message:
                continue  # Ignora mensagens vazias

            # Verifica se a mensagem é um arquivo (usando um prefixo)
            if message.startswith(b"FILE:"):
                print("Recebendo arquivo do cliente:", client_address)
                
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
                # Mensagens normais (não arquivos)
                decoded_message = message.decode('utf-8')
                print(f"Mensagem recebida de {client_address}: {decoded_message}")
                
                # Formata a mensagem para difusão
                formatted_message = f"{client_address}: {decoded_message}"
                broadcast_udp(server_socket, formatted_message.encode('utf-8'), client_address)

        except Exception as e:
            print(f"Erro: {e}")
            continue


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
            if(decoded_message != ""):
                print(f"Mensagem recebida de {username}: {decoded_message}")

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