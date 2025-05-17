import socket

# Paramètres de connexion
HOST = '37.187.122.178'  # Adresse IP du serveur (localhost)
PORT = 1312        # Port d'écoute du serveur




# Création du socket client
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))  # Connexion au serveur


    s.sendall(b'Hello, server!')  # Envoi d'un message
    data = s.recv(1024)  # Réception de la réponse

print('Réponse du serveur:', data.decode())
