import tkinter as tk
from tkinter import ttk

from client import Client, ClientStatus, is_str_valid



class ChatPage (tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        # root frame
        self.root = ttk.Frame (self)
        self.root.pack (fill="both", expand=True)


        self.root.rowconfigure(0, weight=2)
        self.root.rowconfigure(1, weight=40)
        self.root.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=5)
        self.root.columnconfigure(1, weight=15)
        self.root.columnconfigure(2, weight=2)

        self.titlebar = tk.Frame (self.root)
        self.titlebar.grid (column=0, row=0, sticky=tk.NSEW, padx=2.5, pady=2.5, columnspan=3)
        self.title_conv = tk.Label (self.titlebar, text="<titre>")
        self.title_conv.pack (expand=True, fill='both')


        self.leftbar = tk.Frame (self.root)
        self.leftbar.grid(column=0, row=1, sticky=tk.NSEW, padx=2.5, pady=2.5, rowspan=2)
        self.leftbar.columnconfigure (0, weight=1)
        self.leftbar.rowconfigure (0, weight=1)
        self.leftbar.rowconfigure (1, weight=10)
        self.buttons_frame = tk.Frame (self.leftbar)
        self.create_button = tk.Button (self.buttons_frame, text="Créer une conversation", command=lambda: CreatePopup (self, self.controller), width=1)
        self.join_button = tk.Button (self.buttons_frame, text="Rejoindre une conversation", command=lambda: JoinPopup (self, self.controller), width=1)
        self.create_button.pack (side="top", fill="x")
        self.join_button.pack (side="bottom", fill="x")
        self.buttons_frame.grid (row=0, column=0, sticky="new")
        self.talkable_frame = tk.Frame (self.leftbar)
        self.talkable_frame.grid (row=1, column=0, sticky="nsew")
        self.tabs = {}


        self.rightbar = tk.Frame (self.root)
        self.rightbar.grid(column=2, row=1, sticky=tk.NSEW, padx=2.5, pady=2.5, rowspan=2)
        self.rightbar.rowconfigure (0, weight=1)
        self.rightbar.rowconfigure (1, weight=0)
        self.rightbar.rowconfigure (2, weight=10)
        self.rightbar.rowconfigure (3, weight=1)
        self.rightbar.columnconfigure (0, weight=1)
        self.rightbar_title = tk.Label (self.rightbar, text="Participants:")
        self.rightbar_title.grid (row=1, column=0, sticky='ew')
        self.members_frame = tk.Frame (self.rightbar)
        self.members_frame.grid (row=2, column=0, sticky='nsew')
        self.members_frame.columnconfigure (0, weight=1, pad=2.5)
        self.members_frame.rowconfigure (0, weight=1)
        self.members_frame.rowconfigure (21, weight=1)
        self.members = {}
        self.quit_button = tk.Button (self.rightbar, text="Quitter le groupe", command=lambda: self.QuitButtonCallback (), width=1)
        self.quit_button.grid (row=3, column=0, sticky="sew")

        self.body = tk.Frame (self.root)
        self.body.grid(column=1, row=1, sticky=tk.NSEW, padx=2.5, pady=2.5, rowspan=1)
        self.chat_scrollbar = tk.Scrollbar (self.body)
        self.chat = tk.Listbox (self.body, yscrollcommand=self.chat_scrollbar.set)
        self.chat_scrollbar.pack (side='right', fill='y')
        self.chat.pack (expand=True, fill="both")


        self.footer = tk.Frame (self.root)
        self.footer.grid(column=1, row=2, sticky=tk.NSEW, padx=2.5, pady=2.5, rowspan=1)
        self.footer.columnconfigure (0, weight=20)
        self.footer.columnconfigure (1, weight=1)
        self.footer.rowconfigure (0, weight=1)
        self.message_field = tk.Text (self.footer, width=10, height=2)
        self.message_send = tk.Button (self.footer, text='Envoyer', command=lambda: self.controller.SendButtonCallback ())
        self.message_field.grid (row=0, column=0, padx=2.5, pady=2.5, sticky=tk.NSEW)
        self.message_send.grid (row=0, column=1, padx=2.5, pady=2.5, sticky=tk.NSEW)

    def QuitButtonCallback (self):
        if self.controller.current_tab.split ("_")[1] == 'group':
            QuitPopup (self, self.controller)

class CreatePopup (tk.Toplevel):
    def __init__(self, master, controller):
        super().__init__(master)

        self.controller = controller

        tk.Label (self, text="Quel sera le nom du groupe ?").pack ()
        entry = tk.Entry (self)
        entry.pack ()

        def validate_button ():
            group_name = entry.get ()
            if is_str_valid (group_name):
                self.controller.client.send (f"CREAT {group_name}")
                self.destroy ()

        tk.Button (self, text="Valider", command=lambda: validate_button ()).pack ()
        tk.Button (self, text="Annuler", command=lambda: self.destroy ()).pack ()

class JoinPopup (tk.Toplevel):
    def __init__(self, master, controller):
        super().__init__(master)

        self.controller = controller

        tk.Label (self, text="Quel est le nom du groupe ?").pack ()
        entry = tk.Entry (self)
        entry.pack ()

        def validate_button ():
            group_name = entry.get ()
            if is_str_valid (group_name):
                self.controller.client.send (f"ENTER {group_name}")
                self.destroy ()

        tk.Button (self, text="Valider", command=lambda: validate_button ()).pack ()
        tk.Button (self, text="Annuler", command=lambda: self.destroy ()).pack ()

class QuitPopup (tk.Toplevel):
    def __init__(self, master, controller):
        super().__init__(master)

        self.controller = controller

        tk.Label (self, text="Voulez vous vraiment quitter ce groupe ?").pack ()

        def validate_button ():
            group_name: str = self.controller.current_tab.split("_")[0]
            self.controller.client.send (f"LEAVE {group_name}")
            self.destroy ()

        tk.Button (self, text="Valider", command=lambda: validate_button ()).pack ()
        tk.Button (self, text="Annuler", command=lambda: self.destroy ()).pack ()