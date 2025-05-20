import socket
import threading
import sys
import tkinter as tk
from tkinter import scrolledtext, ttk
from queue import Queue, Empty


# HOST = '37.187.122.178'  # Adresse IP du serveur (localhost)
# PORT = 1312        # Port d'écoute du serveur

HOST = 'localhost'  # Adresse IP du serveur (localhost)
PORT = 12345        # Port d'écoute du serveur


class Protocol:
    def __init__(self, Version, Alive, TalkRule):
        self.version = Version
        self.alive = Alive

        self.rules = {}

        self.talk_callback = TalkRule
        self.alive_callback = AliveRule

    def RegisterRule (self, name, rule):
        if name not in self.rules.keys():
            self.rules [name] = rule

    def GetTokens (message: str):
        return message.split (" ")
    
    def GetRule (self, name):
        return (self.rules.get (name, None))
    
    def GetTalkRule (self):
        return (self.talk_callback)
    
class App (tk.Tk):
    def __init__(self, protocol: Protocol, *args, **kwargs):
        super ().__init__ ()

        self.master = tk.Frame (self)
        self.master.pack (side='top', expand=True, fill=('both'))

        self.master.grid_rowconfigure(0, weight = 1)
        self.master.grid_columnconfigure(0, weight = 1)


        self.current_frame = None
        self.frames = {}

        for f in (StartPage, ChatPage):
            frame = f (self.master, self)

            self.frames [f] = frame
            frame.grid (row = 0, column = 0, sticky ="nsew")

        self.show_frame (StartPage)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.chat_protocol = protocol

        self.connected = False
        self.validated = False
        self.loggedin = False

        self.requests = Queue ()

        self.server_talk_mode = False

        self.async_tasks = []

        self.waiting_for = None

        self.username = None

    def __del__ (self):
        self.sock.close ()

    def show_frame(self, cont):
        if self.current_frame != None:
            self.current_frame.pack_forget ()
            self.current_frame.grid_forget ()

        frame = self.frames[cont]
        frame.tkraise()
        self.current_frame = frame

    def receive_messages (self):
        while True:
            if not self.connected: continue
            try:
                data = self.sock.recv(1024)
                if not data:
                    break

                message: str = data.decode ().strip ()

                self.requests.join ()
                self.requests.put (message)

                print (f"Received {message}")
            except ConnectionResetError:
                print ("Connection Terminated (reset)")
                break

    def try_to_connect(self, username: str):
        if not self.connected:
            print (f"Trying to connect to {HOST} at port {PORT}.")
            try:
                self.sock.connect((HOST, PORT))

            except ConnectionRefusedError:
                print (f"Connection refused.")
                return

            except:
                print (f"Connection failed for some reason.")
                return

            self.connected = True

            listen_thread = threading.Thread(target=self.receive_messages, daemon=True)
            listen_thread.start()
            print ("Connected to host successfuly")
            self.master.after (100, self.update_master ())

        self.username = username

        if (self.connected and self.validated):
            self.master.after (100, lambda : self.send_request (f"LOGIN {self.username}", "OKAY!"))


    def handle_requests (self, request: str):
        tokens = Protocol.GetTokens (request)

        print ("Trying to handle request...")

        if self.waiting_for == None or tokens [0] == self.waiting_for[0]:
            rule = self.chat_protocol.GetRule (tokens [0])
            if rule:
                print ("Request being handled...")
                rule (self, tokens)
            else:
                print ("Request was not in the register")
            self.waiting_for = None

        else:
            if (tokens [0] == self.chat_protocol.alive):
                print ("Alive received while waiting for another request")
                self.chat_protocol.GetRule (tokens [0]) (self)

            else:
                rule = self.chat_protocol.GetRule ("*")
                if rule: rule (self, tokens)
                self.waiting_for = None
    
    def send_request (self, request: str, waiting_for: str = None):
        print (f"Sent {request}")
        self.sock.sendall (request.encode ())
        
        self.waiting_for = (waiting_for, request)

        return True

    def update_master(self):
        try:
            while True:
                request = self.requests.get_nowait ()
                self.handle_requests (request)
                self.requests.task_done ()

        except:
            pass


        self.master.after (100, self.update_master)

class StartPage (tk.Frame):
    def __init__(self, parent, controller: App):
        tk.Frame.__init__(self, parent)

        self.username_textbox = tk.Entry (self)
        self.connect_button = tk.Button (self, text="connect", command= lambda : controller.try_to_connect (self.username_textbox.get ()))

        self.username_textbox.pack ()
        self.connect_button.pack ()


class ChatPage (tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # root frame
        self.root_frame = ttk.Frame (self)

        # sidebar frame
        self.sidebar_frame = ttk.Frame (self.root_frame)
        self.create_group_button = ttk.Button (self.sidebar_frame, text="+", command=lambda: self.ask_name_popup (controller))

        self.talkable = {}

        for t_name, t_type in {}:
            self.talkable [f'{t_name}_{t_type}', tk.Button (self.sidebar_frame, text=f'{t_name}', background='orange')]
        

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
        for talkable_name, talkable_button in self.talkable:
            talkable_button.pack (pady=5)

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


    def add_talkable_tab (self, t_name, t_type):
        fullname = f'{t_name}_{t_type}'
        self.talkable [fullname, tk.Button (self.sidebar_frame, text=f'{t_name}', background='orange')]
        self.talkable [fullname].pack (pady=5)

    def ask_name_popup (self, controller: App):
        print ("Trying to create a popup")
        tp = tk.Toplevel (controller.master)
        tp.transient (controller.master)
        tp.geometry ("200x100")
        tp.title ("Groupe")
        
        tk.Label (tp, text="Quel sera le nom du groupe ?").pack ()
        entry = tk.Entry (tp)

        entry.pack ()


        def validate_button ():
            tp.destroy ()
            controller.master.after (100, lambda: controller.send_request (f"CREAT {entry.get ()}", "OKAY!"))

        tk.Button (tp, text="Valider", command=lambda: validate_button ()).pack ()
        tk.Button (tp, text="Annuler", command=lambda: tp.destroy ()).pack ()



# rules

def TalkRule (app: App, args):
    pass

def AliveRule (app, args):
    app.send_request ("ALIVE")

def VersionRule (app: App, args):
    print ("Validating version...")

    if not app.validated:
        print ("Trying to log in ...")
        app.master.after (100, lambda: app.send_request (f'LOGIN {app.username}', "OKAY!"))

    if args [1] == app.chat_protocol.version:
        print ("Version was valided")
        app.validated = True

def OkayRule (app: App, args):
    last_request = Protocol.GetTokens(app.waiting_for[1])[0]
    if last_request == "LOGIN" and not app.loggedin:
        print ("Logged in !")
        app.loggedin = True
        app.show_frame (ChatPage)

    if last_request == "CREAT":
        print (f"Groupe {args [1]} créé de manière succès-pleinement")

def DefaultRule (app: App, args):
    last_request = Protocol.GetTokens(app.waiting_for[1])[0]

    if args [0] == "ERROR":
        error_n = args [1]
        print (f"Error when trying to login : {error_n}") # TODO : make a function that translate error_no to str
        if last_request == "LOGIN":
            app.username = None

# protocol
chat = Protocol ("1", "ALIVE", TalkRule)

chat.RegisterRule ("*", DefaultRule)
chat.RegisterRule ("ALIVE", AliveRule)
chat.RegisterRule ("TCHAT", VersionRule)
chat.RegisterRule ("OKAY!", OkayRule)

# window
window = App (chat)
window.title("Client")
window.geometry ("800x800")

# window = tk.Tk ()
# 
# def ask_name_popup ():
#     print ("Trying to create a popup")
#     win = tk.Toplevel(window)
#     win.geometry("200x100")
#     tk.Label(win, text="Ceci est une popup").pack()
#     tk.Button(win, text="Fermer", command=win.destroy).pack()
# 
# ask_name_popup ()
# root frame

# run
window.mainloop ()