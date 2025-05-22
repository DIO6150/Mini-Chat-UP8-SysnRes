from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from enum import Enum
from queue import Queue, Empty
import socket
from threading import Thread, Lock
from collections.abc import Callable


def is_str_valid (s: str):
    if len (s) <= 0 or len (s) > 16: return False

    valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

    for c in s:
        if c not in valid_chars: return False

    return True

class Protocol:
    def __init__(self, version: str, talk_rule = None):
        self.version = version

        self.requests = {}
        self.responses = {}

        self.talk_rule = talk_rule

    def RegisterRequest (self, name: str, task: Callable):
        self.requests [name] = task

    def RegisterResponse (self, name: str, task: Callable):
        self.responses [name] = task

    def GetRequest (self, name: str):
        return (self.requests.get (name, None))
    
    def GetResponse (self, name: str):
        return (self.responses.get (name, None))
    
    def GetAllRequestCommand (self):
        return ([x for x in self.requests])
    
    def GetTalkRule (self):
        return (self.talk_rule or (lambda client, message: print ("No talk rule")))

class ClientStatus (Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    VALIDATED = 2
    LOGGED = 3

class Mode (Enum):
    NONE = 0
    TALK = 1
    LIST = 2

    def __gt__ (self, other: Mode):
        return self.value > other.value

class Client:
    def __init__(self, protocol: Protocol, host: str = 'localhost', port: int = 12345):
        self.sock = None

        self.status = ClientStatus.DISCONNECTED

        self.protocol = protocol

        self.mutex = Lock ()
        self.responses_pool = Queue ()

        self.last_requests = Queue ()

        self.listen_thread = None

        self.username = None

        self.talk_mode: Mode = Mode.NONE
        self.talk_buffer = ""
        self.talk_author = ""
        self.talk_name = ""
        self.talk_index = 0

        self.talkable_name = None

        self.HOST = host
        self.PORT = port

    def connect (self):
        if (self.status.value >= ClientStatus.CONNECTED.value): return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((self.HOST, self.PORT))

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

        self.sock.sendall ((request + '\n').encode ())

        readable_request = request.replace ('\n', '\\n')
        print (f"[CLIENT] [{readable_request}]")

        if (should_wait): self.last_requests.put (request)
        

    def listen (self):
        while (True):
            if (self.status.value < ClientStatus.CONNECTED.value): continue
            try:
                data = self.sock.recv (1024)
                if (not data): print ("Connection Terminated (forced)"); self.status = ClientStatus.DISCONNECTED; break

                message: str = data.decode ()

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

        response: str = ""

        try:
            while (True):
                with self.mutex:
                    response = self.responses_pool.get_nowait ()

                for t in response.split ("\n"):
                    if (t == ''): continue
                    if self.talk_mode > Mode.NONE:
                        rule = self.protocol.GetTalkRule ()
                        print (f"[SERVER] {t}")
                        if (rule):
                            rule (self, t)
                        continue
                    
                    args = [x.strip (" \n\t\r") for x in t.split (" ")]

                    presentable_tokens = [a.replace ('\n', '\\n') for a in args]
                    print (f"[SERVER] {presentable_tokens}")

                    if (args [0] in self.protocol.GetAllRequestCommand ()):

                        task = self.protocol.GetRequest (args [0])
                        if (task):
                            task (self, args)

                        else:
                            print ("REQUEST WAS NOT REGISTERED IN CURRENT PROTOCOL")                        

                    else:
                        last_request = self.last_requests.get (block=False)

                        if (not last_request):
                            continue

                        last_tokens = last_request.split ()

                        # print (f"Trying to answer to {last_tokens [0]}")
                        task = self.protocol.GetResponse (last_tokens [0])
                        if (task):
                            task (self, args, last_tokens)
                            # print ("Response handled")

                        else:
                            print ("RESPONSE WAS NOT REGISTERED IN CURRENT PROTOCOL")

        except Empty:
            return