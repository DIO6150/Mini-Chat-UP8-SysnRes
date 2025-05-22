import tkinter as tk
from client import Client, ClientStatus

class LoginPage (tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)

        self.controller = controller

        self.username_textbox = tk.Entry (self)
        self.connect_button = tk.Button (self, text="Se Conecter", command=lambda: self.controller.LoginButtonCallback ())

        self.username_textbox.pack ()
        self.connect_button.pack ()

