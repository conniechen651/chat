import selectors
import sys
import re
from socket import *

port = sys.argv[1]
print("Type 'help' for available commands.\n")

sel = selectors.DefaultSelector()

## create server socket
def start_server(port):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', int(port)))
    server_socket.listen(1)
    server_socket.setblocking(False)
    print("Listening on port " + str(port))
    sel.register(server_socket, selectors.EVENT_READ, handle_new_socket_connection)

## create client socket
def start_client(dest_ip, dest_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.settimeout(10) ## set timeout to 10 seconds
    client_socket.connect((dest_ip, int(dest_port)))
    client_socket.setblocking(False)
    print("Connected to " + dest_ip + " on port " + dest_port)
    return client_socket

## function to send a message, including the listening port number so it can be added to receiver's list of connections
def send_message(connection_socket, message):
    message = str(port) + ";" + message
    connection_socket.send(message.encode())

## function to handle new socket connection
def handle_new_socket_connection(server_socket):
    connection_socket, addr = server_socket.accept()
    print("Connection from: " + str(addr))
    sel.register(connection_socket, selectors.EVENT_READ, handle_socket_message)

## function to handle messages received from other sockets
def handle_socket_message(connection_socket):
    data = connection_socket.recv(1024).decode().split(";") ## split message into listening port and data
    print(data)
    if data:
        listening_port = data[0]
        data = data[1]
        list_of_connections.append([connection_socket.getpeername()[0], listening_port, connection_socket])
        print("Message received from: " + str(connection_socket.getpeername()[0]))
        print("Sender's Port: " + str(connection_socket.getpeername()[1]))
        print("Message: " + data) 
    else:
        print("Connection closed")
        sel.unregister(connection_socket)
        for i in range(len(list_of_connections)):
            if list_of_connections[i][2] == connection_socket:
                list_of_connections.pop(i)
        connection_socket.close()

## create list to store all connections
list_of_connections = []

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
    ############### EXIT ###############
    elif data == "exit":
        ##server_socket.close()
        sys.exit()
    
    ############### MYIP ###############
    elif data == "myip":
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        print("Your Computer IP Address is:" + s.getsockname()[0])
        s.close()
        print("---------------------------")
    
    ############### MYPORT ###############
    elif data == "myport":
        print("Your port is: " + port)
        print("---------------------------")
    
    ############### CONNECT ###############
    elif data.startswith("connect"):
        dest_ip = data.split()[1]
        dest_port = data.split()[2]
        for i in range(len(list_of_connections)):
            if list_of_connections[i][0] == dest_ip and list_of_connections[i][1] == dest_port:
                print("Already connected to " + dest_ip + " on port " + dest_port)
                return
        try:
            client = start_client(dest_ip, dest_port) ## call function to create client socket
            list_of_connections.append([dest_ip, dest_port, client]) ## add client to list of connections
        except error:
            print("Error: " + str(error))
        print("---------------------------")
    
    ############### LIST ###############
    elif data == "list":
        print("id:\tIP address:\t\tPort number:")
        for i in range(len(list_of_connections)):
            print(str(i+1) + "\t" + list_of_connections[i][0] + "\t\t" + str(list_of_connections[i][1]))
        print("---------------------------")
    
    ############### TERMINATE ###############
    elif data.startswith("terminate"):
        connection_id = int(data.split()[1])
        if connection_id <= len(list_of_connections):
            list_of_connections[connection_id-1][2].close()
            list_of_connections.pop(connection_id-1)
        else:
            print("Invalid connection ID. Try again.")
        print("---------------------------")

    ############### SEND ###############
    elif data.startswith("send"):
        if re.search('\d+\s', data) == None: ## error checking to make sure there is a connection ID
            print("Invalid command. Try again.")
            return
        connection_id = int(data.split()[1])
        message = re.split('(\d\s+)', data, 1)[2]
        if connection_id <= len(list_of_connections):
            send_message(list_of_connections[connection_id-1][2], message)
            print("Message sent to " + str(list_of_connections[connection_id-1][0]) + " on port " + str(list_of_connections[connection_id-1][1]))
        else:
            print("Invalid connection ID. Try again.")
        print("---------------------------")
    else:
        print("Invalid command. Type 'help' for available commands.")
        print("---------------------------")

def main():
    sel.register(sys.stdin, selectors.EVENT_READ, handle_stdin_input)
    
    start_server(port)

    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj)

main()

    