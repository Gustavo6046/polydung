import game
import sys
import logging


l = logging.getLogger("PolydungServer")
l.setLevel(logging.DEBUG)

FORMAT = '[%(levelname)s | %(asctime)s] %(message)s'
logging.basicConfig(format=FORMAT)

game.Game(*[eval(x) for x in sys.argv[1:]], logger=l)