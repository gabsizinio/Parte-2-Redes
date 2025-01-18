import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# Configuração do host e porta do servidor
HOST = '127.0.0.2'  # Endereço do servidor (localhost)
PORT = 12345        # Porta para comunicação

# Criação do socket para comunicação com o servidor
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Tela de login
def login_screen():
    # Configuração da janela de login
    login_window = tk.Tk()
    login_window.title("Login")  # Título da janela
    login_window.geometry("300x200")  # Dimensões da janela
    login_window.config(bg="#1c1c1c")  # Cor de fundo da janela

    # Rótulo para entrada do nome de usuário
    tk.Label(login_window, text="Nome de Usuário:", font=("Arial", 12), bg="#1c1c1c", fg="#ffffff").pack(pady=10)

    # Caixa de entrada para o nome de usuário
    username_entry = tk.Entry(login_window, font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff")
    username_entry.pack(pady=5)

    # Função para realizar o login
    def login():
        username = username_entry.get()  # Obtém o nome de usuário digitado
        if username:  # Verifica se o nome não está vazio
            try:
                # Tenta conectar ao servidor
                client.connect((HOST, PORT))
                client.send(username.encode())  # Envia o nome de usuário ao servidor
                response = client.recv(1024).decode()  # Recebe a resposta do servidor
                if response.startswith("ERRO"):  # Verifica se houve erro
                    messagebox.showerror("Erro", response)  # Mostra mensagem de erro
                    client.close()  # Fecha a conexão
                else:
                    login_window.destroy()  # Fecha a janela de login
                    chat_screen(username)  # Abre a tela de chat
            except Exception as e:
                # Mostra mensagem de erro caso falhe a conexão
                messagebox.showerror("Erro", f"Falha na conexão: {e}")
        else:
            # Mostra aviso se o nome de usuário estiver vazio
            messagebox.showwarning("Aviso", "O nome de usuário não pode estar vazio.")

    # Botão para realizar o login
    tk.Button(login_window, text="Entrar", command=login, font=("Arial", 12), 
              bg="#007bff", fg="#ffffff", activebackground="#0056b3", activeforeground="#ffffff").pack(pady=20)

    login_window.mainloop()  # Inicia o loop da interface gráfica

# Tela principal do chat
def chat_screen(username):
    # Função para receber mensagens do servidor
    def receive_messages():
        while True:
            try:
                msg = client.recv(1024).decode()  # Recebe mensagens do servidor
                if msg.startswith("USERS:"):  # Atualização da lista de usuários online
                    update_user_list(msg[6:].split(","))  # Atualiza a lista de usuários
                else:
                    # Insere mensagens na área de texto
                    message_box.config(state=tk.NORMAL)
                    message_box.insert(tk.END, f"{msg}\n")
                    message_box.config(state=tk.DISABLED)
                    message_box.see(tk.END)  # Rola automaticamente para a última mensagem
            except Exception as e:
                # Exibe erro no console caso ocorra um problema ao receber mensagens
                print(f"Erro ao receber mensagem: {e}")
                break

    # Função para enviar mensagens ao servidor
    def send_message():
        msg = input_box.get()  # Obtém a mensagem da caixa de entrada
        if msg:  # Verifica se a mensagem não está vazia
            client.send(msg.encode())  # Envia a mensagem ao servidor
            input_box.delete(0, tk.END)  # Limpa a caixa de entrada

    def send_file():
        filename = file_name_box.get()

        try: 
           # Reading file and sending data to server 
            fi = open(filename, "r") 
            data = fi.read() 
            if data:
            
                while data: 
                    client.send(str(data).encode()) 
                    data = fi.read() 
                # File is closed after data is sent 
                fi.close() 
            
            file_name_box.delete(0, tk.END)  # Limpa a caixa de entrada
    
        except IOError: 
            print('Nome de arquivo invalido ou arquivo não existe') 

    # Função para atualizar a lista de usuários online
    def update_user_list(users):
        user_list.delete(0, tk.END)  # Limpa a lista de usuários
        for user in users:
            user_list.insert(tk.END, user)  # Adiciona os usuários atualizados

    # Configuração da janela de chat
    chat_window = tk.Tk()
    chat_window.title(f"Chat - {username}")  # Título da janela com o nome do usuário
    chat_window.geometry("600x400")  # Dimensões da janela
    chat_window.config(bg="#1c1c1c")  # Cor de fundo da janela

    # Layout principal
    main_frame = tk.Frame(chat_window, bg="#1c1c1c")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Lista de usuários online no lado esquerdo
    user_list = tk.Listbox(main_frame, font=("Arial", 12), bg="#333333", fg="#ffffff",
                           selectbackground="#007bff", selectforeground="#ffffff")
    user_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

    # Área de mensagens
    message_box = scrolledtext.ScrolledText(main_frame, state=tk.DISABLED, wrap=tk.WORD, 
                                            font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff")
    message_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Caixa de entrada para digitar mensagens
    input_box = tk.Entry(chat_window, font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff")
    input_box.pack(fill=tk.X, padx=10, pady=5)

    # Botão de enviar mensagem
    send_button = tk.Button(chat_window, text="Enviar", command=send_message, font=("Arial", 12), 
                             bg="#007bff", fg="#ffffff", activebackground="#0056b3", activeforeground="#ffffff")
    send_button.pack(pady=5)


    file_name_box = tk.Entry(chat_window, font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff")
    file_name_box.pack(fill=tk.X, padx=10, pady=5)


    send_file_button = tk.Button(chat_window, text="Enviar Arquivo", command=send_file, font=("Arial", 12), 
                             bg="#007bff", fg="#ffffff", activebackground="#0056b3", activeforeground="#ffffff")
    send_file_button.pack(pady=5)


    # Thread para receber mensagens do servidor sem bloquear a interface gráfica
    thread = threading.Thread(target=receive_messages, daemon=True)
    thread.start()

    chat_window.mainloop()  # Inicia o loop da interface gráfica

# Execução principal do programa
if __name__ == "__main__":
    login_screen()  # Inicia o programa com a tela de login
