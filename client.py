import sys
import getopt
import os
import traceback
import utils

"""
------------------------------------------------------------------------------------------------------
SOURCE FILE: client.py - client application

PROGRAM: Tcp File Transfer Client Server

DATE: Oct 1, 2020

DESIGNER: Junyin Xia

PROGRAMMER: Junyin Xia

FUNCTIONS:
    void main (void)
    void userInputLoop(string : ip)
    void handleGet(socket : controlSocket, string : filename)
    void handleSend(socket : controlSocket, string : filename)

NOTES:
    This is a terminal client for a fileshare application to transfer files of all sizes bothways across a local 
    network using TCP. On start, the client program will try to connect to a listening server, then
    continuously read and execute commands.
    
    Two channels are used:
        control channel - created on client starts after it connects to server, client sends commands thru this channel.
            Runs between clientIp:OS port <-> serverIp:7005
        
        data channel - created after client issues command through the control channel, and server establishes a new connection
            to transfer file data. Runs between clientIp:8888 <-> serverIp:7006

    At any time, the user can leave by entering 'exit' or hitting 'ctrl+c' in the terminal.
    This will disconnect any existing connections, and exit the program. 
-------------------------------------------------------------------------------------------------------
"""

"""
----------------------------------------------------------------------------------------------
FUNCTION main

DATE: Oct 1 2020

DESIGNER: Junyin Xia

PROGRAMMER: Junyin Xia

INTERFACE: def main():

ARGUMENTS: void
    
RETURNS: void

NOTES:
Entry point of the client application. Main function verifies the commandline arguments passed 
into python is right. If commandline args are invalid or an exception is thrown at this stage, a help
msg is printed and the program exits. 

After a server ip is extracted from commandline args, a loop is started that reads and executes commands. 
----------------------------------------------------------------------------------------------
"""
def main():
    help_msg=sys.argv[0] + ' -i <server ip>'
    try:
        opts, args = getopt.getopt(sys.argv[1:],'i:',['ip='])
    except getopt.GetoptError:
        print(help_msg)
        sys.exit(2)
    if len(opts) == 0:
        print(help_msg)
        sys.exit()
    
    ip=''
    for opt, arg in opts:
        if opt in ('-i', '--ip'):
            ip = arg

    if ip != '':
        userInputLoop(ip)

"""
----------------------------------------------------------------------------------------------
FUNCTION userInputLoop

DATE: Oct 1 2020

DESIGNER: Junyin Xia

PROGRAMMER: Junyin Xia

INTERFACE: def userInputLoop(ip):

ARGUMENTS: string ip : ipv4 address of server
    
RETURNS: void

NOTES:

Makes a connection to server ip port 7005, then starts a forever loop that reads user input and executes commands.

The accepted commands a user can enter are (cmds aren't case-sensitive but filenames are)
    GET - request list of files stored on server
    GET filename - request a specific file from server to be saved locally
    SEND - lists the files stored locally that can send to server
    SEND filename -  send a local file to server to be saved
    EXIT - disconnect and exit the program 

    GET and SEND commands are handled by their own functions.
This function opens a socket on the control channel with the server.
----------------------------------------------------------------------------------------------
"""
def userInputLoop(ip):
    controlSocket = utils.createTcpSocket()
    try:
        controlSocket.connect((ip, utils.SERVER_COMM_PORT))
        print('Enter a command: get / get <file> / send / send <file> / exit')
        while True:
            userInput = input('>>> ')
            validInput=True
            cmd = userInput.upper()
            if cmd[0:3] == 'GET':
                filename=userInput[3:].strip()
                handleGet(controlSocket, filename)
            elif cmd[0:4] == 'SEND':
                filename=userInput[4:].strip()
                handleSend(controlSocket, filename)
            elif cmd == 'EXIT':
                print('exit called.')
                break
            else:
                validInput=False

            if not validInput:
                print('>>> Invalid input, please enter valid cmd')
    except KeyboardInterrupt:
        print('\nexit called.')
    except Exception as e: 
        traceback.print_exc()
    finally:
        controlSocket.close()

"""
----------------------------------------------------------------------------------------------
FUNCTION handleGet

DATE: Oct 1 2020

DESIGNER: Junyin Xia

PROGRAMMER: Junyin Xia

INTERFACE: def handleGet(controlSocket, filename):

ARGUMENTS: 
    socket controlSocket :  tcp socket opened on control channel
    string filename : file that client wants from server. Leave empty to receive server filenames list
    
RETURNS: void

NOTES:
    Handles the get file scenario on the client.
    Open port 8888 and listen for server connection (to establish data channel)
    If a file was specified, send GET packet with filename. Otherwise, send a request to GETALL filenames.
    
    Once the server connects, depending what cmd packet was sent, it will immediately send back either the filenames
    (which the client will print out), or a status indicating if the file was found on the server. If the file was
    found, the server will send the filesize then file bytes right after. So we pass off the socket + filename to a helper
    function to recv and save the file bytes locally.
----------------------------------------------------------------------------------------------
"""
def handleGet(controlSocket, filename):
    listenSocket = utils.createTcpSocket(utils.PORT_X)
    listenSocket.listen(1)
    packet=''
    if not filename:
        utils.sendCmdPacket(controlSocket, utils.GETALL)
    else:
        utils.sendCmdPacket(controlSocket, utils.GET, filename)

    dataSocket, serverIpPort = listenSocket.accept()
    data = utils.readDataPacket(dataSocket)

    if not filename:
        # data is list of filenames
        print(data)
    else:
        # data is filename or status
        if data == utils.NOT_FOUND:
            print('File not found on server:', filename)
        if data == utils.FOUND:
            print('Fetching', filename)
            utils.recvFile(dataSocket, filename)
    dataSocket.close()
    listenSocket.close()

"""
----------------------------------------------------------------------------------------------
FUNCTION handleSend

DATE: Oct 1 2020

DESIGNER: Junyin Xia

PROGRAMMER: Junyin Xia

INTERFACE: handleSend(controlSocket, filename):

ARGUMENTS: 
    socket controlSocket : tcp socket opened on control channel
    string filename : file that client wants to send to server. Leave empty to list out local filenames available for transfer
    
RETURNS: void

NOTES:
    Handles the send file scenario on the client.
    If a file isn't specified, function just prints list of files in ./files dir and ends.

    Otherwise, function will open port 8888 and listen for server connection (to establish data channel)
    
    Once the server connects, the client will immediately use a helper function to send the filesize + filebytes
    across the data channel for the server to read.
----------------------------------------------------------------------------------------------
"""
def handleSend(controlSocket, filename):
    if not filename:
        print('  '.join(os.listdir('./files')))
    elif not os.path.isfile('./files/' + filename):
        print('File not found, cannot send: ', filename)
    else:
        listenSocket = utils.createTcpSocket(utils.PORT_X)
        listenSocket.listen(1)
        
        utils.sendCmdPacket(controlSocket, utils.SEND, filename)
        
        dataSocket, serverIpPort = listenSocket.accept()
        utils.sendFile(dataSocket, filename)
        
        print('File sent to server')

# start program
main()