import selectors
import sys
import re
from socket import *

port = sys.argv[1]

## get IP address
s = socket(AF_INET, SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip_addr = s.getsockname()[0]
s.close()

print("Type 'help' for available commands.\n")

sel = selectors.DefaultSelector()

## create server socket
def start_server(port):
    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((ip_addr, int(port))) 
        server_socket.listen(1)
        server_socket.setblocking(False)
        print("Listening on port " + str(port))
        sel.register(server_socket, selectors.EVENT_READ, handle_new_socket_connection)
        return server_socket
    except OSError as e:
        print(f"There was an error starting server: {e}")
        sys.exit(1) #If server fails to start, exit program
    

## create client socket
def start_client(dest_ip, dest_port):
    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.settimeout(10) ## set timeout to 10 seconds
        client_socket.connect((dest_ip, int(dest_port)))
        client_socket.send(str(port).encode())
        client_socket.setblocking(False)
        print("Connected to " + dest_ip + " on port " + dest_port)
        return client_socket
    except (TimeoutError, ConnectRefusedError) as e:
        print(f"Connection failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

## function to send a message
def send_message(connection_socket, message):
    connection_socket.send(message.encode())

## function to handle new socket connection
def handle_new_socket_connection(server_socket):
    connection_socket, addr = server_socket.accept()
    port = connection_socket.recv(1024).decode()
    print("Connection from: " + str(addr))
    sel.register(connection_socket, selectors.EVENT_READ, handle_socket_message)
    ## check if existing connection already exists
    for i in range(len(list_of_connections)):
        if list_of_connections[i][0] == addr[0] and list_of_connections[i][1] == port:
            list_of_connections[i][2] = connection_socket
            return
    list_of_connections.append([addr[0], port, connection_socket, -1])

## function to handle messages received from other sockets
def handle_socket_message(connection_socket):
    try:
        data = connection_socket.recv(1024).decode()
        if data:
            print("Message received from: " + str(connection_socket.getpeername()[0]))
            print("Sender's Port: " + str(connection_socket.getpeername()[1]))
            print("Message: " + data)
            print("---------------------------")
        else:
            raise ConnectionResetError
    except (ConnectionResetError, OSError):
        for i, connection in enumerate(list_of_connections):
            if connection[2] == connection_socket:
                print(f"Connection closed by user {i + 1}: IP Address was {connection[0]}: Port Number was {connection[1]}")
                list_of_connections.pop(i)
                break
    sel.unregister(connection_socket)
    connection_socket.close()

## create list to store all connections
list_of_connections = []

def main_menu():
    print("\nMain Menu:")
    print("1. help")
    print("2. myip")
    print("3. myport")
    print("4. connect <destination> <port no>")
    print("5. list")
    print("6. terminate")
    print("7. send")
    print("8. exit")
    print("Please type the name of the command you wish to use:")


def handle_stdin_input(server_socket):
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
        server_socket.close()
        sys.exit()
    
    ############### MYIP ###############
    elif data == "myip":
        print("Your IP Address is: " + ip_addr)   
        print("---------------------------")
    
    ############### MYPORT ###############
    elif data == "myport":
        print("Your port is: " + port)
        print("---------------------------")
    
    ############### CONNECT ###############
    elif data.startswith("connect"):
        if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\s\d{4,5}\b", data) == None: ## error checking for valid IP and port
            print("Invalid command. Try again.")
            main_menu()
            return
        dest_ip = data.split()[1]
        dest_port = data.split()[2]
        if dest_ip == ip_addr and dest_port == port:
            print("Cannot connect to yourself.")
            main_menu()
            return
        #Validating port range
        if not (0 <= int(dest_port) <= 65535):
            print("Invalid port number. Port must be between 0 and 65535; try again.")
            main_menu()
            return
        for i in range(len(list_of_connections)):
            if list_of_connections[i][0] == dest_ip and list_of_connections[i][1] == dest_port and list_of_connections[i][3] != -1:
                print("Already connected to " + dest_ip + " on port " + dest_port)
                main_menu()
                return
        try:
            client = start_client(dest_ip, dest_port) ## call function to create client socket
            for i in range(len(list_of_connections)):
                if list_of_connections[i][0] == dest_ip and list_of_connections[i][1] == dest_port: ## one way connection exists
                    list_of_connections[i][3] = client
                    main_menu()
                    return 
            ## no connection exists
            list_of_connections.append([dest_ip, dest_port, -1, client]) ## add client to list of connections
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
        if re.search('\d+', data) == None: ## error checking to make sure there is a connection ID
            print("Invalid command. Try again.")
            main_menu()
            return
        connection_id = int(data.split()[1])
        if connection_id <= len(list_of_connections):
            if list_of_connections[connection_id-1][3] != -1:
                list_of_connections[connection_id-1][3].close()
                list_of_connections.pop(connection_id-1)
                print("Connection with connection ID #" + str(connection_id) + " terminated")
            else:
                print("Connection not established yet. Try again.")
        else:
            print("Invalid connection ID. Try again.")
        print("---------------------------")

    ############### SEND ###############
    elif data.startswith("send"):
        if re.search('\d+\s', data) == None: ## error checking to make sure there is a connection ID
            print("Invalid command. Try again.")
            main_menu()
            return
        connection_id = int(data.split()[1])
        message = re.split('(\d\s+)', data, 1)[2]
        if connection_id <= len(list_of_connections):
            if list_of_connections[connection_id-1][3] == -1:
                print("Connection not established yet. Try again.")
                main_menu()
                return
            try:
                send_message(list_of_connections[connection_id-1][3], message)
                print("Message sent to " + str(list_of_connections[connection_id-1][0]) + " on port " + str(list_of_connections[connection_id-1][1]))
            except error:
                print("Error: " + str(error))
        else:
            print("Invalid connection ID. Try again.")
        print("---------------------------")
    else:
        print("Invalid command. Type 'help' for available commands.")
        print("---------------------------")

    main_menu()

def main():
    
    server = start_server(port)
    main_menu()
    sel.register(sys.stdin, selectors.EVENT_READ, lambda _: handle_stdin_input(server))
    
    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj)

main()

    
