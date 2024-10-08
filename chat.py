import selectors
import sys
from socket import *
from requests import get

port = sys.argv[1]
print("Type 'help' for available commands.\n")

sel = selectors.DefaultSelector()

def start_server(port):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', int(port)))
    server_socket.listen(1)
    server_socket.setblocking(False)
    print("Listening on port " + str(port))
    sel.register(server_socket, selectors.EVENT_READ, handle_new_socket_connection)

def start_client(dest_ip, dest_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((dest_ip, int(dest_port)))
    client_socket.setblocking(False)
    print("Connected to " + dest_ip + " on port " + dest_port)

def handle_stdin_input(data):
    data = input()
    if data == "help":
        print("----------------------------------------------------")
        print("Type 'myip' to display your IP")
        print("Type 'myport' to display the port on which you are listening")
        print("Type 'connect <destination IP> <port number>' to connect to a destination")
        print("Type 'list' to display all connected nodes")
        print("Type 'terminate <connection ID>' to terminate the connection under the connection ID")
        print("Type 'send <connection ID> <message>' to send a message to the host designated by the connection ID")
        print("Type 'exit' to close all connections and exit the program")
        print("----------------------------------------------------")
        print()
    elif data == "exit":
        ##server_socket.close()
        sys.exit()
    elif data == "myip":
        ## not working??
        hostname = gethostname()
        IPAddr = gethostbyname(hostname)
        DnsIPAddr = gethostbyaddr(hostname)

        print("Your Computer Name is:" + str(hostname))
        print("Your Computer IP Address is:" + str(IPAddr))
        print("According to DNS, your Computer IP Address is:" + str(DnsIPAddr))

        ##print("Your IP is: " + gethostbyname(gethostname()))
        print()
    elif data == "myport":
        print("Your port is: " + port)
        print()
    elif data.startswith("connect"):
        dest_ip = data.split()[1]
        dest_port = data.split()[2]
        start_client(dest_ip, dest_port)
    else:
        print("Invalid command. Type 'help' for available commands.")

def handle_new_socket_connection(server_socket):
    connection_socket, addr = server_socket.accept()
    print("Connection from: " + str(addr))
    sel.register(connection_socket, selectors.EVENT_READ, handle_socket_message)

def handle_socket_message(connection_socket):
    data = connection_socket.recv(1024)
    if data:
        print("Received: " + data) 
    else:
        print("Connection closed")
        sel.unregister(connection_socket)
        connection_socket.close()

def main():
    sel.register(sys.stdin, selectors.EVENT_READ, handle_stdin_input)
    
    start_server(port)

    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj)

main()

    