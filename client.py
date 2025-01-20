import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# Configuração do host e porta do servidor
HOST = '127.0.0.2'  # Endereço do servidor (localhost)
PORT = 12345        # Porta para comunicação
FORMAT = "utf-8"

def connect_to_server(host, port):
    # Tentativa de conexão TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria o socket TCP
    try:
        client.connect((host, port))  # Tenta conectar via TCP
        return client
    except socket.error:
        client.close()  # Fecha o socket TCP em caso de falha

        # Tentativa de conexão UDP
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Cria o socket UDP
        try:
            client.sendto(b"Hello", (host, port))  # Envia mensagem via UDP
            client.recvfrom(1024)  # Espera uma resposta
        except socket.error:
            client.close()  # Fecha o socket UDP em caso de falha
            return None
        else:
            return client


# Tela de login
def login_screen(connection_type="udp"):
    # Configuração da janela de login
    login_window = tk.Tk()
    login_window.title("Login")  # Título da janela
    login_window.geometry("600x400")  # Dimensões da janela
    login_window.config(bg="#1c1c1c")  # Cor de fundo da janela

    # Rótulo para entrada do nome de usuário
    tk.Label(login_window, text="Nome de Usuário:", font=("Arial", 12), bg="#1c1c1c", fg="#ffffff").pack(pady=10)

    # Caixa de entrada para o nome de usuário
    username_entry = tk.Entry(login_window, font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff")
    username_entry.pack(pady=5)

    # Rótulo para entrada da senha
    tk.Label(login_window, text="Senha:", font=("Arial", 12), bg="#1c1c1c", fg="#ffffff").pack(pady=10)

    # Caixa de entrada para a senha com "***" para ocultar a senha
    password_entry = tk.Entry(login_window, font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff", show="*")
    password_entry.pack(pady=5)

    def login(connection_type):
        username = username_entry.get()  # Obtém o nome de usuário digitado
        username += ":" + password_entry.get()  # Adiciona a senha ao nome de usuário
        if username:  # Verifica se o nome não está vazio
            try:
                client.connect((HOST, PORT)) if connection_type == "TCP" else None
                if connection_type == "TCP":
                    client.send(username.encode(FORMAT))
                    response = client.recv(1024).decode(FORMAT)
                else:
                    client.sendto(username.encode(FORMAT), (HOST, PORT))
                    response = "OK"  # Para UDP, você pode definir a resposta de acordo com sua lógica.
                if response.startswith("ERRO"):
                    messagebox.showerror("Erro", response)
                    client.close()
                else:
                    login_window.destroy()
                    chat_screen(username, connection_type)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha na conexão: {e}")
        else:
            messagebox.showwarning("Aviso", "O nome de usuário não pode estar vazio.")

    # Botão para realizar o login
    tk.Button(login_window, text="Entrar", command=lambda: login(connection_type), font=("Arial", 12), 
          bg="#007bff", fg="#ffffff", activebackground="#0056b3", activeforeground="#ffffff").pack(pady=20)

    login_window.mainloop()  # Inicia o loop da interface gráfica

# Tela principal do chat
def chat_screen(username, protocol="tcp"):
    def receive_messages():
        while True:
            try:
                if protocol == "tcp":
                    msg = client.recv(1024).decode(FORMAT)
                else:  # UDP
                    msg, server_address = client.recvfrom(1024)
                    msg = msg.decode(FORMAT)

                if msg.startswith("USERS:"):  # Atualização da lista de usuários online
                    update_user_list(msg[6:].split(","))
                else:
                    # Exibe a mensagem decodificada na interface do cliente
                    message_box.config(state=tk.NORMAL)
                    message_box.insert(tk.END, f"{msg}\n")
                    message_box.config(state=tk.DISABLED)
                    message_box.see(tk.END)  # Rola automaticamente para a última mensagem
            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")
                break

    def send_message():
        msg = input_box.get()
        if msg:
            try:
                if protocol == "tcp":
                    client.send(msg.encode(FORMAT))
                else:  # UDP
                    client.sendto(msg.encode(FORMAT), (HOST, PORT))

                input_box.delete(0, tk.END)
                message_box.config(state=tk.NORMAL)
                message_box.insert(tk.END, f"Você: {msg}\n")
                message_box.config(state=tk.DISABLED)
                message_box.see(tk.END)
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

    def send_file():
        filename = file_name_box.get()

        try:
            with open(filename, "r") as fi:
                data = fi.read()
                if data:
                    while data:
                        if protocol == "tcp":
                            client.send(data.encode(FORMAT))
                        else:  # UDP
                            client.sendto(data.encode(FORMAT), (HOST, PORT))
                        data = fi.read()
                file_name_box.delete(0, tk.END)
        except IOError:
            print('Nome de arquivo inválido ou arquivo não existe')

    def update_user_list(users):
        user_list.delete(0, tk.END)
        for user in users:
            user_list.insert(tk.END, user)

    # Configuração da janela de chat
    chat_window = tk.Tk()
    chat_window.title(f"Chat - {username}")
    chat_window.geometry("600x400")
    chat_window.config(bg="#1c1c1c")

    main_frame = tk.Frame(chat_window, bg="#1c1c1c")
    main_frame.pack(fill=tk.BOTH, expand=True)

    user_list = tk.Listbox(main_frame, font=("Arial", 12), bg="#333333", fg="#ffffff",
                           selectbackground="#007bff", selectforeground="#ffffff")
    user_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

    message_box = scrolledtext.ScrolledText(main_frame, state=tk.DISABLED, wrap=tk.WORD,
                                            font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff")
    message_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    input_box = tk.Entry(chat_window, font=("Arial", 12), bg="#333333", fg="#ffffff", insertbackground="#ffffff")
    input_box.pack(fill=tk.X, padx=10, pady=5)

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

    chat_window.mainloop()

# Execução principal do programa
if __name__ == "__main__":
    client = connect_to_server(HOST, PORT)
    login_screen()  # Inicia o programa com a tela de login