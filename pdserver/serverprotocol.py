import socket
import threading
import hashlib
import json


class Client(object):
    def __init__(self, game, host, socket):
        self.game = game # game.Game
        self.host = host # (ip, port)
        self.socket = socket # socket.socket [socket.AF_INET, socket.SOCK_STREAM]
        self.username = None
        self.password = None
        self.snapshot()
                
        threading.Thread(target=self.listen_loop).start()
                
    def authenticate(self):
        return self.game.authenticate(self)
                
    def receive(self, cmd, *args):
        if cmd.upper() == "AUTH":
            self.username = args[0]
            
            if len(args) > 1:
                self.password = args[1]
                
            code = self.authenticate()
            
            if code is None:
                self.socket.sendall(b"AUTHCODE SUC\n")
            
            else:
                self.socket.sendall("AUTHCODE ERR {}\n".format(code).encode('utf-8'))
            
        elif cmd.upper() == "DISCONNECT":
            self.game.logger.info("Client {}:{} disconnected".format(*self.host))
            self.game.disconnect(self)
            return True
                
    def listen_loop(self):
        buf = ""
        
        while True:
            try:
                buf += self.socket.recv(2048).decode('utf-8')
                
            except socket.error:
                self.game.disconnect(self)
                return
                
            splits = buf.split('\n')
            buf = splits[-1]
            
            for s in splits[:-1]:
                if self.receive(*s.split(' ')):
                    return
        
    def update_object(self, obj):
        self.socket.sendall('DELETE {}\n'.format(obj.id).encode('utf-8'))
        self.socket.sendall('SPAWN {}\n'.format(obj.serialize()).encode('utf-8'))
        
    def snapshot(self):
        self.socket.sendall('ALLRESET\n'.encode('utf-8'))
        
        for obj in self.game.objects:
            self.socket.sendall('SPAWN {}\n'.format(obj.serialize()).encode('utf-8'))
        
    def send(self, command, *args):
        self.socket.sendall("{}{}\n".format(command, ''.join([' ' + a for a in args])).encode('utf-8'))
        
    def send_map(self):
        self.socket.sendall("MAP {}\n".format(self.game.serialize_map()).encode('utf-8'))