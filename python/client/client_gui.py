import tkinter as tk
from tkinter import ttk
from client import Client, ClientStatus, is_str_valid
from chat import ChatPage
from login import LoginPage

def get_tab_display_name (tab_id: str):
    tab = tab_id.split ("_")
    return ("G" if tab [1] == "group" else "U") + ": " + tab [0]

def is_tab_group (tab_id: str):
    tab = tab_id.split ("_")
    return tab [1] == "group"

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

        self.messages = {}

        self.current_tab = ""

        for page in (LoginPage, ChatPage):
            frame = page (master=self.container_frame, controller=self)
            frame.grid (row=0, column=0, sticky="nsew")
            self.frames [page] = frame

        self.show_frame (LoginPage)

    def add_member (self, name: str, tab_id: str):
        page: ChatPage = self.frames [ChatPage]

        if tab_id not in page.members: page.members [tab_id] = {}
        if name in page.members [tab_id]: return

        page.members [tab_id][name] = tk.Button (page.members_frame, text=f"{name}", command=lambda: self.SelectUserRightbarCallback (name + "_user"))
        if name == self.client.username: page.members [tab_id][name].config(state=tk.DISABLED)

    def remove_member (self, name: str, tab_id: str):
        page: ChatPage = self.frames [ChatPage]

        if tab_id not in page.members: return
        button = page.members [tab_id].pop (name, None)
        button.destroy ()

    def add_tab (self, tab_id: str):
        page: ChatPage = self.frames [ChatPage]

        display_name: str = get_tab_display_name (tab_id)

        if tab_id not in self.messages:
            page.tabs [tab_id] = tk.Button (page.talkable_frame, text=f"{display_name}", command=lambda: self.change_tab (tab_id), width=1)
            page.tabs [tab_id].pack (side="top", fill='x')
            self.messages [tab_id] = []

    def remove_tab (self, tab_id: str):
        page: ChatPage = self.frames [ChatPage]
        found = page.tabs.pop (tab_id, None)

        if (found):
            found.pack_forget ()
            self.messages.pop (tab_id)
            if self.current_tab == tab_id and tab_id in page.members:

                for _, button in page.members [tab_id].items ():
                    button.destroy ()
                page.members [tab_id].clear ()

    def update_members (self):
        page: ChatPage = self.frames [ChatPage]

        for tab_name in page.members:
            for name, button in page.members [tab_name].items ():
                button.grid_forget ()
                button.pack_forget ()
            
        if self.current_tab in page.members:
            for name, button in page.members [self.current_tab].items ():
                button.pack (side="top", fill='x')

        """
        if self.current_tab in page.members:
            for name, button in page.members [self.current_tab].items ():
                print (f"hide {name}")
                button.grid_forget ()
                button.pack_forget ()
            
        if tab_id in page.members:
            for name, button in page.members [tab_id].items ():
                print (f"show {name}")
                button.pack (side="top", fill='x')
        """

    def change_tab (self, tab_id: str = None):
        if not tab_id:
            self.reset_tab ()
            return

        self.current_tab = tab_id

        self.update_members ()

        page: ChatPage = self.frames [ChatPage]
        tab_display_name = get_tab_display_name (tab_id)

        page.title_conv.config (text=tab_display_name)
        page.chat.delete (0, tk.END)
        for message in self.messages [tab_id]:
            page.chat.insert (tk.END, message)

        if not is_tab_group (tab_id):
            page.quit_button.config (state=tk.DISABLED)
        else:
            page.quit_button.config (state=tk.NORMAL)


    def reset_tab (self):
        page: ChatPage = self.frames [ChatPage]
        page.chat.delete (0, tk.END)
        
        if self.current_tab in page.members:
            for _, button in page.members[self.current_tab].items ():
                button.pack_forget ()

        page.title_conv.config (text="<titre>")

        self.current_tab = ""

    def show_frame(self, page):
        if self.current_frame != None:
            self.current_frame.pack_forget ()
            self.current_frame.grid_forget ()

        self.current_frame = self.frames [page]
        self.current_frame.tkraise()

    def update_chat (self):
        page: ChatPage = self.frames [ChatPage]
        page.chat.delete (0, tk.END)

        if self.current_tab in self.messages:
            for message in self.messages [self.current_tab]:
                page.chat.insert (tk.END, message)

    def write_in_chat (self, message: str, author: str = None, tab: str = None, remember=True):
        final_tab = tab or self.current_tab

        if message != "" and final_tab in self.messages:
            if author != None: message = author + ': ' + message
            if remember:
                self.messages [final_tab].append (message)
                self.update_chat ()
            else:
                page: ChatPage = self.frames [ChatPage]
                page.chat.insert (tk.END, message)
                
    def purge_chat (self, n_line: int):
        page: ChatPage = self.frames [ChatPage]
        page.chat.delete (tk.END - n_line, tk.END)

    def async_client_update (self):
        self.client.handle_response ()

        self.after (100, lambda: self.async_client_update ())

    def LoginButtonCallback (self):
        page: LoginPage = self.frames [LoginPage]
        username = page.username_textbox.get ()

        if not is_str_valid (username):
            return
        
        self.client.username = username
        self.client.connect ()

        if (self.client.status == ClientStatus.CONNECTED):
            self.after (100, lambda: self.async_client_update ())
        
        if (self.client.status == ClientStatus.VALIDATED):
            self.client.send (f"LOGIN {self.client.username}")

    def SendButtonCallback (self):
        page: ChatPage = self.frames [ChatPage]

        message: str = page.message_field.get ('1.0', 'end-1c')
        tab_id: str = self.current_tab

        if message != "" and tab_id in self.messages:
            tab = tab_id.split ("_")
            tab_name = tab [0]
            tab_type = tab [1]

            if (tab_type == "group"):
                self.client.send (f"SPEAK {tab_name}\n{message}\n.", False)

            else:
                self.write_in_chat (message, self.client.username, tab_id)
                self.client.send (f"MSGPV {tab_name}\n{message}\n.", False)

        page.message_field.delete (1.0, tk.END)
            

    def SelectUserRightbarCallback (self, tab_id: str):
        user_name = tab_id.split ("_")[0]
        if user_name == self.client.username: return

        if not tab_id in self.messages:
            self.add_tab (tab_id)

            self.add_member (user_name, tab_id)
            self.add_member (self.client.username, tab_id)
            self.update_members ()

        self.change_tab (tab_id)
