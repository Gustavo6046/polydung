import socket
import base64
import time
import threading
import hashlib


SCODE_NEEDAUTH = 0
SCODE_BANNED = 1
SCODE_BADAUTH = 2
SCODE_BADREG = 3


class Connection(object):
    def __init__(self, ip, port, broadcast=False):
        if broadcast:
            print()
            print("Connecting: {}:{}".format(ip, port))
    
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        self.auth_handlers = []
        
        self.stopped = False
        threading.Thread(target=self._receive_loop).start()
        
    def disconnect(self):
        self.stopped = True
    
        self.socket.sendall("DISCONNECT\n".encode('utf-8'))
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()
        
    def send(self, cmd, *args):
        self.socket.sendall("{}{}\n".format(cmd, ''.join([' ' + a for a in args])).encode('utf-8'))
        
    @classmethod
    def connect(cls, ip, port, username, password=None, on_response=None, broadcast=False):
        self = cls(ip, port, broadcast=broadcast)
        
        if on_response is not None:
            self.auth_handlers.append(on_response)
        
        if password is not None:
            sha = hashlib.sha512()
            sha.update(password.encode('utf-8'))
            sha.update(b"PolyDung")
            hash = base64.b64encode(sha.digest()).decode('utf-8')
        
        self.socket.sendall("AUTH {}{}\n".format(username, (" " + hash if password is not None else "")).encode('utf-8'))
        
    def receive(self, cmd, *args):    
        if cmd.upper() == "AUTHCODE":
            status = ConnectionStatus(args[0], self, (int(args[1]) if len(args) > 1 else None))
        
            for ah in self.auth_handlers:
                ah(status)
                
            if args[0].upper() == "ERR":
                self.socket.close()
    
    def _receive_loop(self):
        buf = ""
        
        while True:
            if self.stopped:
                return
        
            buf += self.socket.recv(2048).decode('utf-8')    
            splits = buf.split('\n')
            buf = splits[-1]
            
            if len(splits) > 1:
                for s in splits[:-1]:
                    self.receive(*s.split(' '))
                    
            else:
                time.sleep(0.5)
        
class ConnectionStatus(object):
    def __init__(self, status, connection=None, code=None):
        self.status = status
        self.connection = connection
        self.code = code