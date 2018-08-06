import base64
import random
import string
import netbyte
import numpy as np

try:
    import simplejson as json
    
except ImportError:
    import json
    

kinds = {}

class PDObject(object):
    def __init__(self, game, kind, id, pos, properties):
        self.game = game
        self.kind = kind
        self.id = id or ''.join([random.choice(string.ascii_letters + string.digits + "#$%*") for _ in range(100)])
        self.pos = np.array(pos)
        self.properties = properties
        
        self.game.handle_object_creation(self)
        
    def __getitem__(self, key): # a shortcut for Netbyte
        return self.properties[key]
        
    def __setitem__(self, key, value): # not only a shortcut for Netbyte
        self.properties[key] = value
        self.game.update_object(self)
        
    def __call__(self, key, **kwargs):
        nbe = netbyte.Netbyte()
        nbe['self'] = self
        nbe['game'] = self.game
        
        for k, v in kwargs.items():
            nbe[k] = v
        
        nbe.execute_instructions(*self.kind.functions[key])
        
    def tick(self, timedelta):
        self('tick', timedelta=timedelta)
    
    def serialize(self):
        return json.dumps({
            "kind": self.kind.name,
            'id': self.id,
            'pos': self.pos.tolist(),
            "properties": self.properties
        })

    @classmethod
    def deserialize(cls, game, js):
        data = json.loads(js)
        return cls(game, kinds[data['kind']], data['id'], data['pos'], data['properties'])

class PDClass(object):
    def __init__(self, game, name, functions=()):
        self.functions = dict(functions)
        self.name = name
    
        kinds[name] = self
        
        nbe = netbyte.Netbyte()
            
    def serializable(self):
        return {
            'name': self.name,
            'functions': {k: nbe.dump(v, name="{}.{}".format(self.name, k)) for k, v in self.functions.items()}
        }