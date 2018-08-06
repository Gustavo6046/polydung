# import renderer
import clientprotocol
import sys
import getpass


def client_handle(conn):
    pass
    # game = conn.get_game()

    # renderer.render_game(game)

def main():
    print("Host of server to connect to:     (format: <IP>[:<port>])")
    host = input(":")
    sys.stdout.write('\r')
    
    if ":" not in host or host.index(":") == len(host) - 1:
        ip = host.split(":")[0]
        port = 3048
        
    else:
        ip, port = host.split(':')    
        port = int(port)
        
    print("Username of your account:")
    username = input(":")
    
    password = None

    def conn_response(status):
        if status.status.upper() == "ERR":
            status.connection.disconnect()
        
            if status.code == clientprotocol.SCODE_NEEDAUTH:
                print("The server is asking for the password")
                print("for the account {}".format(username))
                print()
                print("Password:".format(username))
                
                password = getpass.getpass(":")
                sys.stdout.write('\r')
                
                clientprotocol.Connection.connect(ip, port, username, password, conn_response, broadcast=True)
                
            elif status.code == clientprotocol.SCODE_BANNED:
                print()
                print("You're banned from this server.")
                print()
                main()
                
            elif status.code == clientprotocol.SCODE_BADREG:
                while True:
                    print()
                    print("Please supply a password to register a new")
                    print("account named {}.".format(username))
                    password  = getpass.getpass(":")
                    print("Please confirm your password, to make sure you")
                    print("can log in later without a forgotten password")
                    print("situation.")
                    p2 = getpass.getpass(":")
                    
                    if p2 == password:
                        break
                        
                    else:
                        print("Passwords don't match!")
                        
                
                sys.stdout.write('\r')
                
                clientprotocol.Connection.connect(ip, port, username, password, conn_response, broadcast=True)
            
            elif status.code == clientprotocol.SCODE_BADAUTH:
                print()
                print("Invalid password.")
                print()
                main()
                
        elif status.status.upper() == "SUC":
            conn = status.connection
            print("Connected with success!")
            client_handle(conn)
            
    clientprotocol.Connection.connect(ip, port, username, password, conn_response, broadcast=True)
    
if __name__ == "__main__":
    print("   :: P O L Y D U N G :: ")
    print()
    print("'Ludere comitatus est ludere bene.'")
    print("(to play accompanied is to play well)")
    print()
    print()
    
    main()