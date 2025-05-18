import socket
import threading
import sys
print (sys.path)
import tkinter as tk
from tkinter import scrolledtext



# HOST = '37.187.122.178'  # Adresse IP du serveur (localhost)
# PORT = 1312        # Port d'écoute du serveur
HOST = 'localhost'  # Adresse IP du serveur (localhost)
PORT = 12345        # Port d'écoute du serveur

class ClientApp:
    def __init__(self, master):
        self.master = master
        master.title("Client Réseau")

        self.chat_area = scrolledtext.ScrolledText(master, state='disabled', width=40, height=10)
        self.chat_area.pack(padx=10, pady=10)

        self.entry = tk.Entry(master, width=30)
        self.entry.pack(padx=10, pady=5)
        self.entry.bind("<Return>", self.send_message)

        self.connect_to_server()

    def connect_to_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))

        self.listen_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.listen_thread.start()

    def send_message(self, event=None):
        msg = self.entry.get()
        self.sock.sendall(msg.encode())
        self.entry.delete(0, tk.END)

    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                self.chat_area.config(state='normal')
                self.chat_area.insert(tk.END, "Serveur: " + data.decode() + '\n')
                self.chat_area.config(state='disabled')
            except ConnectionResetError:
                break

root = tk.Tk()
app = ClientApp(root)
root.mainloop()
