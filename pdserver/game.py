import objects
import logging
import sqlite3
import threading
import json
import serverprotocol
import sqlite3
import base64
import socket


tileset = []

SCODE_NEEDAUTH = 0
SCODE_BANNED = 1
SCODE_BADAUTH = 2
SCODE_BADREG = 3


class TileType(object):
    def __init__(self, sprite="nulltile", functions=()):
        self.index = len(tileset)
        self.sprite = sprite
        self.functions = dict(functions)
        
        tileset.append(self)
        
    def serializable(self):
        return {
            "index": self.index,
            "sprite": self.sprite,
        }

class Game(object):
    def __init__(self, save='polydung.db', listen_port=3048, map_width=120, map_height=67, logger=None): # kinda 16:9
        self.save = save
        self.clients = []
        self.logger = logger or logging.getLogger("PolydungServer")
        self.block_db = False
    
        db = self.database()
        c = db.cursor()
        c.execute('SELECT * FROM sqlite_master WHERE TYPE = "table";')
    
        if len(c.fetchall()) > 0:
            self.map = []
            c.execute("SELECT * FROM TileMap;")
            self.block_db = True
            
            for ind, js in c.fetchall():
                self.map.insert(ind, json.loads(js))
                
            self.objects = []
            c.execute('SELECT * FROM Objects;')
            
            for o, in c.fetchall():
                objects.PDObject.deserialize(o)
                
            self.block_db = False
    
        else:
            self.objects = []
            self.map = [[0 for _ in range(map_width)] for _ in range(map_height)]
            
            c.execute("CREATE TABLE TileMap (row int, json text);")
            c.execute("CREATE TABLE Objects (json text);")
            c.execute("CREATE TABLE IpBans (ip text);")
            c.execute("CREATE TABLE AccountBans (username text);")
            c.execute("CREATE TABLE Accounts (fails int, logins int, username text, password text);")
            
            for i, row in enumerate(self.map):
                c.execute("INSERT INTO TileMap VALUES (?, ?);", (i, json.dumps(row)))
            
            db.commit()
        
        c.close()
        db.close()
        
        self.logger.info("Hosting at port: {}".format(listen_port))
        threading.Thread(target=self._listen_loop, args=(listen_port,)).start()
        
    def is_authentic(self, username, password=None):
        db = self.database()
        c = db.cursor()
        c.execute("SELECT password FROM Accounts WHERE username = ?", (username,))
        
        p = c.fetchone()[0]
        
        if p is None:
            if password is None:
                return False
            
            else:
                c.execute("INSERT INTO Accounts VALUES (?, ?, ?, ?);", (0, 1, username, password))
                db.commit()
                c.close()
                db.close()
                
                return True
            
        elif password is None:
            return False
            
        res = (password == p)
        
        if res:
            c.execute("UPDATE Accounts SET logins = logins + 1 WHERE username = ?", (username,))
            
        else:
            c.execute("UPDATE Accounts SET fails = fails + 1 WHERE username = ?", (username,))
            
        db.commit()
        c.close()
        db.close()
        
        return res
        
    def _listen_loop(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
            
        s.listen(5)
        
        while True:
            (clsock, addr) = s.accept()
            self.logger.info("Client attempting connection from {}:{}".format(*addr))
            serverprotocol.Client(self, addr, clsock)
        
    def is_host_banned(self, ip):
        db = self.database()
        c = db.cursor()
        c.execute("SELECT * FROM IpBans WHERE ip = ?", (ip,))
        
        return len(c.fetchall()) > 0
        
    def is_account_banned(self, username):
        db = self.database()
        c = db.cursor()
        c.execute("SELECT * FROM AccountBans WHERE username = ?", (username,))
        
        return len(c.fetchall()) > 0
        
    def authenticate(self, client):
        if self.is_authentic(client.username, client.password):
            if self.is_host_banned(client.host[0]):
                self.logger.info("Client {}:{} ({}) is IP banned!".format(*client.host, client.username))
                return SCODE_BANNED
                
            elif self.is_account_banned(client.username):
                self.logger.info("Client {}:{} ({}) is user banned!".format(*client.host, client.username))
                return SCODE_BANNED
            
            else:
                self.logger.info("Client {}:{} authenticated as {}".format(*client.host, client.username))
                self.add_client(client)
                
        elif client.password is None:
            db = self.database()
            c = db.cursor()
            c.execute("SELECT * FROM Accounts WHERE username = ?;", (client.username,))
            
            if len(c.fetchall()) == 0:                
                self.logger.info("Client {}:{} tried to make a new account {} but hasn't set a new password for it!".format(*client.host, client.username))
                return SCODE_BADREG
        
            else:
                self.logger.info("Client {}:{} doesn't have the password to account {}".format(*client.host, client.username))
                return SCODE_NEEDAUTH
            
        else:        
            self.logger.info("Client {}:{} has the wrong password to account {}".format(*client.host, client.username))
            return SCODE_BADAUTH
        
    def disconnect(self, client):
        if client in self.clients:
            self.clients.remove(client)
        
    def handle_object_creation(self, obj):
        self.objects.append(obj)
        
        for cl in self.clients:
            cl.send("SPAWN", obj.serialize())
        
        if not self.block_db:
            db = self.database()
            c = db.cursor()
            c.execute('INSERT INTO Objects VALUES (?);', (obj.serialize(),))
            db.commit()
            c.close()
            db.close()
        
    def database(self):
        return sqlite3.connect(self.save)
        
    def serialize_map(self):
        return json.dumps(self.map)
        
    def add_client(self, cl):
        for cl in self.clients:
            cl.send("JOINED", cl.username)
            
        self.clients.append(cl)
        
    def update_object(self, obj):
        for cl in self.clients:
            cl.update_object(obj)
            
    def global_snapshot(self):
        for cl in self.clients:
            cl.send("TILESET", json.dumps([tp.serializable() for tp in tileset]))
            cl.snapshot()
            cl.send_map()
            
            for kind in objects.kinds.values():
                cl.send("CLASS", json.dumps(kind.serializable()))
        
    def update_map(self, coords):
        for cl in self.clients:
            cl.send("TILECHANGE", coords[0], coords[1], str(self.map[coords[0]][coords[1]]))
        
    def tick(self, tdelta):
        for o in self.objects:
            o.tick(tdelta)
        
    def __getitem__(self, key):
        return self.map[key[0]][key[1]]
        
    def __setitem__(self, key, value):
        self.map[key[0]][key[1]] = value
        self.update_map(key)
        
        if not self.block_db:
            db = self.database()
            c = db.cursor()
            c.execute('UPDATE TileMap SET json=? WHERE row=?;', (json.dumps(self.map[key[0]]), key[0]))
            db.commit()
            c.close()
            db.close()
        
    def call_tile(self, coords, name, **kwargs):
        t = self.map[coords[0]][coords[1]]
        f = tileset[t[0]].functions[name]
        
        nbe = netbyte.Netbyte()
        nbe['coords'] = coords
        nbe['state'] = t[1]
        
        for k, v in kwargs.items():
            nbe[k] = v
        
        nbe.execute_instructions(*f)