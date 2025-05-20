import tkinter as tk
from tkinter import ttk
from enum import Enum
from queue import Queue, Empty
import socket
from threading import Thread, Lock
from collections.abc import Callable

HOST = 'localhost'  # Adresse IP du serveur (localhost)
PORT = 12345        # Port d'écoute du serveur

class Protocol:
    def __init__(self, version: str):
        self.version = version

        self.requests = {}
        self.responses = {}

    def RegisterRequest (self, name: str, task: Callable):
        self.requests [name] = task

    def RegisterResponse (self, name: str, task: Callable):
        self.responses [name] = task

    def GetRequest (self, name: str):
        return (self.requests [name])
    
    def GetResponse (self, name: str):
        return (self.responses [name])
    
    def GetAllRequestCommand (self):
        return ([x for x in self.requests])

class ClientStatus (Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    VALIDATED = 2
    LOGGED = 3

class Client:
    def __init__(self, protocol: Protocol):
        self.sock = None

        self.status = ClientStatus.DISCONNECTED

        self.protocol = protocol

        self.mutex = Lock ()
        self.responses_pool = Queue ()

        self.last_requests = Queue ()

        self.listen_thread = None

        self.username = None

        self.gui_handle = None

    def GetGUIHandle (self) -> 'ClientGUI':
        return (self.gui_handle)

    def connect (self):
        if (self.status.value >= ClientStatus.CONNECTED.value): return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((HOST, PORT))

        except ConnectionRefusedError:
            print (f"Connection refused.")
            return

        except:
            print (f"Connection failed for some reason.")
            return

        self.status = ClientStatus.CONNECTED

        self.listen_thread = Thread(target=self.listen, daemon=True)
        self.listen_thread.start()
        print ("Connected to host successfuly")

    def send (self, request: str, should_wait: bool = True):
        if (self.status.value < ClientStatus.CONNECTED.value): return
        print (f"Sent {request}")
        self.sock.sendall (request.encode ())
        
        if (should_wait): self.last_requests.put (request)

    def listen (self):
        while (True):
            if (self.status.value < ClientStatus.CONNECTED.value): continue
            try:
                data = self.sock.recv (1024)
                if (not data): print ("Connection Terminated (forced)"); self.status = ClientStatus.DISCONNECTED; break

                message: str = data.decode ().strip ()

                with self.mutex:
                    self.responses_pool.put (message)

                # print (f"[LISTEN][SERVER] {message}")

            except ConnectionResetError:
                self.status = ClientStatus.DISCONNECTED
                print ("Connection Terminated (reset)")
                break

            except:
                print ("Something went wrong")
                self.mutex.release ()
                break
    
    def handle_response (self):        
        if (self.status.value < ClientStatus.CONNECTED.value): return

        try:
            while (True):
                with self.mutex:
                    response = self.responses_pool.get_nowait ()

                print (f"[HANDLE][SERVER] {response}")
                response_tokens = response.split (" ")
                # TODO: i'm not entierly sure, but its quite possible that when we do the speak thingy, we should look for . and not SPEAK command (maybe queue is LIFO idk)
                # after careful research (one google link) I have concluded that Queue is in fact Fifo

                if (response_tokens [0] in self.protocol.GetAllRequestCommand ()):
                    # print ("Initiating Server Request handling")

                    
                    if (task := self.protocol.GetRequest (response_tokens [0])):
                        task (self, response_tokens)
                        # print ("Request handled")

                    else:
                        print ("REQUEST WAS NOT REGISTERED IN CURRENT PROTOCOL")
                        pass

                else:
                    # print ("Initiating Server Response handling")
                    last_request = self.last_requests.get ()
                    last_tokens = last_request.split (" ")

                    # print (f"Trying to answer to {last_tokens [0]}")

                    if (task := self.protocol.GetResponse (last_tokens [0])):
                        print (task)
                        task (self, response_tokens, last_tokens)
                        # print ("Response handled")

                    else:
                        print ("RESPONSE WAS NOT REGISTERED IN CURRENT PROTOCOL")

        except:
            return

class ConnectPage (tk.Frame):
    def __init__(self, master, controller: 'ClientGUI'):
        super().__init__(master)

        self.controller: 'ClientGUI' = controller

        self.username_textbox = tk.Entry (self)
        self.connect_button = tk.Button (self, text="connect", command=lambda: self.connect_button_callback ())

        self.username_textbox.pack ()
        self.connect_button.pack ()

    def connect_button_callback (self):
        self.username_textbox.config (state="readonly")
        self.controller.client.username = self.username_textbox.get ()
        self.controller.client.connect ()

        self.controller.should_change_page = True

        if (self.controller.client.status == ClientStatus.CONNECTED):
            self.controller.after (100, lambda: self.controller.async_client_update ())

        self.username_textbox.config (state="normal")

class ChatPage (tk.Frame):
    def __init__(self, master, controller: 'ClientGUI'):
        super().__init__(master)
        self.controller: 'ClientGUI' = controller

        # root frame
        self.root_frame = ttk.Frame (self)

        # sidebar frame
        self.sidebar_frame = ttk.Frame (self.root_frame)
        self.create_group_button = ttk.Button (self.sidebar_frame, text="+", command= lambda: CreateGroupPopup (self, self.controller))

        # chat frame
        self.chat_frame = ttk.Frame (self.root_frame)
        self.labelTitle = ttk.Label (self.chat_frame, text='CONV NAME', background='gray')
        self.scrollbar = tk.Scrollbar (self.chat_frame)
        self.chatList = tk.Listbox (self.chat_frame, yscrollcommand=self.scrollbar.set)

        # entry frame
        self.entry_frame = ttk.Frame (self.chat_frame)
        self.textBox = tk.Entry (self.entry_frame)
        self.sendButton = tk.Button (self.entry_frame, text='Envoyer')

        # sidebar layout
        self.create_group_button.pack (pady=5)
        self.talkables = {}

        # chat layout
        self.labelTitle.pack (fill='x')
        self.scrollbar.pack (side='right', fill='y')
        self.chatList.pack (fill='both', expand=True)

        # entry layout
        self.entry_frame.pack (fill='x', side='bottom')
        self.textBox.pack (fill='x', side='left', expand=True)
        self.sendButton.pack (fill='none', side='right')

        # root layout
        self.sidebar_frame.pack (side='left', fill='y', padx=10, pady=5)
        self.chat_frame.pack (side='left', expand=True, fill='both')
        self.root_frame.pack (expand=True, fill='both')

    def add_talkable (self, name=str, t_type=str):
        fullname = name + "_" + t_type
        self.talkables [fullname] = tk.Button (self.sidebar_frame, text=f"{name}")
        self.talkables [fullname].pack ()

class CreateGroupPopup (tk.Toplevel):
    def __init__(self, master, controller):
        super().__init__(master)

        self.controller: 'ClientGUI' = controller

        tk.Label (self, text="Quel sera le nom du groupe ?").pack ()
        entry = tk.Entry (self)
        entry.pack ()


        def validate_button ():
            self.controller.client.send (f"CREAT {entry.get ()}")
            self.destroy ()
            # controller.master.after (100, lambda: controller.send_request (f"CREAT {entry.get ()}", "OKAY!"))

        tk.Button (self, text="Valider", command=lambda: validate_button ()).pack ()
        tk.Button (self, text="Annuler", command=lambda: self.destroy ()).pack ()


class ClientGUI (tk.Tk):
    def __init__(self, screenName = None, baseName = None, className = "Tk", useTk = True, sync = False, use = None, client = None):
        super().__init__(screenName, baseName, className, useTk, sync, use)

        self.client: Client = client
        self.client.gui_handle = self
        self.should_change_page = False

        self.container_frame = tk.Frame (self)
        self.container_frame.pack(side = "top", fill = "both", expand = True)

        self.container_frame.grid_rowconfigure(0, weight=1)
        self.container_frame.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.current_frame = None

        for page in (ConnectPage, ChatPage):
            frame = page (master=self.container_frame, controller=self)
            frame.grid (row=0, column=0, sticky="nsew")
            self.frames [page.__name__] = frame

        self.show_frame (ConnectPage)


    def show_frame(self, page):
        if self.current_frame != None:
            self.current_frame.pack_forget ()
            self.current_frame.grid_forget ()

        self.current_frame = self.frames [page.__name__]
        self.current_frame.tkraise()

    def async_client_update (self):
        self.client.handle_response ()

        self.after (100, lambda: self.async_client_update ())


# protocol responses definition
def AliveResponse (client: Client, response_token):
    client.send ("ALIVE", False)

def TchatResponse (client: Client, response_token):
    if (client.status == ClientStatus.CONNECTED):
        if (response_token [1] == client.protocol.version):
            client.status = ClientStatus.VALIDATED
            print ("Protocol version validated.")

            print ("Now trying to Log In")
            client.send (f"LOGIN {client.username}")

# protocol requests definition
def LoginRequest (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")

    if (is_error):
        print (f"Error when login : {response_token [1]}")
        client.username = None
        return
    
    client.status = ClientStatus.LOGGED
    client.username = original_request_token [1]
    print (f"Client logged in as {client.username}.")

    client.GetGUIHandle ().show_frame (ChatPage)

def CreatRequest (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")
    page: ChatPage = client.GetGUIHandle ().frames [ChatPage.__name__]

    print ("hello ?")

    if (is_error):
        page.chatList.insert (tk.END, f"Erreur en créant le groupe: {response_token [1]}")
        print (f"Error when creating group : {response_token [1]}")
        return
    
    print (f"Group {original_request_token [1]} was successfully created.")
    # TODO : create the widget for the group in the talkable part
    page.add_talkable (original_request_token [1], "group")

protocol = Protocol ("1")

# protocol requests regitration
protocol.RegisterRequest ("ALIVE", AliveResponse)
protocol.RegisterRequest ("TCHAT", TchatResponse)

# protocol response registration (ex: Client asks: LOGIN USR -> servers respond: OKAY! -> client does something in return)
protocol.RegisterResponse ("LOGIN", LoginRequest)
protocol.RegisterResponse ("CREAT", CreatRequest)

client = Client (protocol)

window = ClientGUI (client=client)
window.geometry ("800x800")

window.mainloop ()