import socket
import threading

# Configurações do servidor
HOST = '127.0.0.2'  # Endereço IP do servidor (localhost)
PORT = 12345        # Porta onde o servidor ouvirá conexões
FORMAT = "utf-8"

# Criação do socket do servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Socket TCP
server.bind((HOST, PORT))  # Associa o socket ao endereço e porta configurados
server.listen()  # Habilita o servidor para aceitar conexões

# Listas para armazenar informações dos clientes conectados
clients = []    # Lista de sockets dos clientes conectados
usernames = []  # Lista de nomes de usuários correspondentes

fileno = 0

def broadcast(message, exclude_client=None):
    """
    Envia mensagens para todos os clientes conectados, exceto o cliente que gerou a mensagem.
    
    Args:
    - message (bytes): Mensagem a ser enviada.
    - exclude_client (socket, optional): Cliente a ser excluído do envio.
    """
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
            
            message = client.recv(1024)  # Limite do tamanho da mensagem 1024
            
            if not message:
                break        
            
            if message.startswith(b"FILE:"):  # Verifica se mensagem é arquivo
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

                print('Arquivo recebido com sucesso! Nome do novo arquivo:', full_filename) 
                # Notifica usuarios do arquivo recebido
                broadcast(f"A new file has been uploaded: {full_filename}".encode(FORMAT), exclude_client=client)
            
            else:    
                # Difunde a mensagem para outros clientes
                decoded_message = message.decode(FORMAT)  
                index = clients.index(client)
                username = usernames[index]
                
                formatted_message = f"{username}: {decoded_message}"
                
                broadcast(formatted_message.encode(FORMAT), exclude_client=client)
        
        except Exception as e:
            print(f"Erro: {e}")
            # Em caso de erro, remove o cliente da lista
            index = clients.index(client) # Localiza o índice do cliente na lista
            clients.remove(client) # Remove o cliente da lista de sockets
            username = usernames.pop(index) # Remove o nome de usuário correspondente
            client.close()  # Fecha o socket do cliente
            print(f"{username} saiu do chat.") # Loga no servidor
            update_user_list() # Atualiza a lista de usuários online para todos
            break


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
        update_user_list()  # Atualiza a lista de usuários online para todos os clientes

        # Cria uma thread para gerenciar a comunicação com o cliente
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

# Inicia o servidor
receive_connections()
