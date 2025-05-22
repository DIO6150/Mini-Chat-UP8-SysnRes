from client import Client, ClientStatus, Protocol, Mode
from client_gui import ClientGUI
from login import LoginPage
from chat import ChatPage
import sys

def get_name (name: str, t_type: str):
    return (name + "_" + t_type)





protocol = Protocol ("1")
if len(sys.argv) == 3:
    print (sys.argv)
    client_side = Client (protocol, sys.argv [1], int (sys.argv [2]))
else:
    client_side = Client (protocol)
client_gui = ClientGUI (client=client_side)
client_gui.title ("Client")

# protocol responses definition
def AliveRequest (client: Client, response_token):
    client.send ("ALIVE", False)

def TchatRequest (client: Client, response_token):
    if (client.status == ClientStatus.CONNECTED):
        if (response_token [1] == client.protocol.version):
            client.status = ClientStatus.VALIDATED
            print ("Protocol version validated.")

            print ("Now trying to Log In")
            client.send (f"LOGIN {client.username}")

def SpeakRequest (client: Client, response_token: list):
    tab = get_name (response_token [2], "group")

    client.talk_mode = Mode.TALK
    client.talk_buffer = ""
    client.talk_author = response_token [1]
    client.talk_name = tab
    
def EnterRequest (client: Client, response_token):
    tab = get_name (response_token [1], "group")
    client_gui.write_in_chat (f"{response_token [2]} à rejoint le groupe.", tab=tab)    
    client_gui.add_member (response_token [2], tab)
    client_gui.update_members ()
    
def LeaveRequest (client: Client, response_token):
    tab = get_name (response_token [1], "group")
    client_gui.write_in_chat (f"{response_token [2]} à quitté le groupe.", tab=tab)
    client_gui.remove_member (response_token [2], tab)
    client_gui.update_members ()


def MsgRequest (client: Client, response_token):
    tab = get_name (response_token [1], "user")

    user_name = tab.split ("_")[0]
    if tab not in client_gui.messages:
        client_gui.add_tab (tab)

        client_gui.add_member (client_gui.client.username, tab)
        client_gui.add_member (user_name, tab)
        client_gui.update_members ()

    client.talk_mode = Mode.TALK
    client.talk_buffer = ""
    client.talk_author = user_name
    client.talk_name = tab

# protocol requests definition
def LoginResponse (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")

    if (is_error):
        print (f"Error when login : {response_token [1]}")
        client.username = None
        return
    
    client.status = ClientStatus.LOGGED
    client.username = original_request_token [1]
    print (f"Client logged in as {client.username}.")

    client_gui.show_frame (ChatPage)

def CreatResponse (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")

    if (is_error):
        client_gui.write_in_chat (f"Erreur en créant le groupe: {response_token [1]}", remember=False)
        return
    
    tab_name = get_name (original_request_token [1], "group")

    client_gui.add_member (client.username, tab_name)
    client_gui.add_tab (tab_name)
    client_gui.change_tab (get_name (original_request_token [1], "group"))

def EnterResponse (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")

    tab_name = get_name (original_request_token [1], "group")

    if (is_error):
            
        client_gui.write_in_chat (f"Erreur en rejoignant le groupe: {response_token [1]}", remember=False)
        return

    client_gui.add_tab (tab_name)
    client_gui.change_tab (tab_name)

    client.send (f"LSMEM {original_request_token [1]}")


def LeaveResponse (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")

    if (is_error):
        client_gui.write_in_chat (f"Erreur en essayant de quitter le groupe: {response_token [1]}", remember=False)
        return
    
    client_gui.remove_tab (get_name (original_request_token [1], "group"))
    client_gui.reset_tab ()
    client_gui.update_members ()

def ListMemberResponse (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")

    if (is_error):
        client_gui.write_in_chat (f"Erreur (réponse de LSMEM): {response_token [1]}", remember=False)
        return

    tab_name = get_name (original_request_token [1], "group")

    client.talk_mode = Mode.LIST
    client.talk_buffer = ""
    client.talk_index = int (response_token [2])
    client.talk_name = tab_name


def MsgResponse (client: Client, response_token, original_request_token):
    is_error: bool = (response_token [0] == "ERROR")

    if (is_error):
        err_no: int = response_token [1]
        if err_no == "21":
            print (original_request_token)
            tab_id = get_name (original_request_token [1], "user")
            client_gui.remove_member (original_request_token [1], tab_id)
        client_gui.purge_chat (3) # ne marche pas
        client_gui.write_in_chat (f"Erreur message privé n'a pas pu parvenir au destinataire : {err_no}", remember=False)

        return

def TalkRule (client: Client, token: str):
    match client.talk_mode:
        case Mode.TALK:
            if token == ".":
                message: str = client.talk_buffer

                client_gui.write_in_chat (message, client.talk_author, tab=client.talk_name)

                client.talk_mode = Mode.NONE
                return
            
            client.talk_buffer += token
            
        case Mode.LIST:
            client.talk_buffer += token + '\n'
            client.talk_index -= 1

            if client.talk_index <= 0:
                members: str = client.talk_buffer

                for member in members.split ():
                    client_gui.add_member (member, client.talk_name)

                client_gui.update_members ()
                client.talk_mode = Mode.NONE
            pass
    


    



protocol.RegisterRequest ("ALIVE", AliveRequest)
protocol.RegisterRequest ("TCHAT", TchatRequest)
protocol.RegisterRequest ("SPEAK", SpeakRequest)
protocol.RegisterRequest ("ENTER", EnterRequest)
protocol.RegisterRequest ("LEAVE", LeaveRequest)
protocol.RegisterRequest ("MSGPV",   MsgRequest)

protocol.RegisterResponse ("LOGIN", LoginResponse)
protocol.RegisterResponse ("CREAT", CreatResponse)
protocol.RegisterResponse ("ENTER", EnterResponse)
protocol.RegisterResponse ("LEAVE", LeaveResponse)
protocol.RegisterResponse ("LSMEM", ListMemberResponse)
protocol.RegisterResponse ("MSGPV",   MsgResponse)

protocol.talk_rule = TalkRule




client_gui.geometry ("1000x800")
client_gui.mainloop ()