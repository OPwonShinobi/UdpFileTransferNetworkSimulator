import socket
import os


SERVER_COMM_PORT=7005
SERVER_TX_PORT=7006
PORT_X=8888

GETALL='0'
GET='1'
SEND='2'
CMDS=('GETALL','GET','SEND')

NOT_FOUND='/404/'
FOUND='/200/'
BUFFER_SIZE=8192


def createTcpSocket(bindPort=None):
    newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    newSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if bindPort is not None:
        newSocket.bind(('', bindPort))
    return newSocket


def sendStr(sendSocket,str):
    total_sent = 0
    total = len(str)
    byte_str = str.encode()
    while total_sent < total:
        bytes_sent = sendSocket.send(byte_str[total_sent:])
        if bytes_sent == 0:
            raise RuntimeError("sendStr socket disconnected")
        total_sent += bytes_sent


def recvStr(recvSocket,msgLen):
    chunks = []
    bytes_read = 0
    while bytes_read < msgLen:
        chunk = recvSocket.recv(min(BUFFER_SIZE,msgLen))
        # python empty str is false, empty chunk == connection broke, stop reading
        if not chunk:
            raise RuntimeError('recvStr socket disconnected while reading!')
        chunks.append(chunk)
        bytes_read += len(chunk)
    return b''.join(chunks).decode()


def sendCmdPacket(sendSocket,flag,msg=''):
    msgStr=str(msg)
    paddedLength = '{:0>3}'.format(len(msgStr))
    packet=flag + paddedLength + msgStr
    sendStr(sendSocket, packet)


def readCmdPacket(readSocket):
    flag =recvStr(readSocket,1)
    msg = readDataPacket(readSocket)
    return (flag, msg)


def sendDataPacket(sendSocket, msg):
    msgStr=str(msg)
    paddedLength = '{:0>3}'.format(len(msgStr))
    packet=paddedLength + msgStr
    sendStr(sendSocket, packet)


def readDataPacket(readSocket):
    msgLen=int(recvStr(readSocket,3))
    return recvStr(readSocket, msgLen)


def sendFile(sendSocket,filename):
    # read binary mode
    with open('./files/'+filename,'rb') as file:
        filesize=os.path.getsize('./files/'+filename)
        
        sendDataPacket(sendSocket, filesize)
        if filesize != 0:
            bytes_sent=0
            while bytes_sent < filesize:
                chunk=file.read(BUFFER_SIZE)
                if not chunk:
                    raise RuntimeError("sendFile socket disconnected while sending")
                bytes_sent+=sendSocket.send(chunk)
        print('File sent, bytes',filesize)

def recvFile(recvSocket,filename):
    filesize=int(readDataPacket(recvSocket))

    # create or clear file
    with open('./files/'+filename,'w') as file:
        file.write('')
        
    print('Sender\'s file size: ',filesize)
    if filesize == 0:
        return

    with open('./files/'+filename,'ab') as file:
        bytes_read = 0
        while bytes_read < filesize:
            chunk = recvSocket.recv(BUFFER_SIZE)
            if not chunk:
                print('recvFile socket disconnected while reading!')
                break
            file.write(chunk)
            bytes_read += len(chunk)
    print('File saved: /files/'+filename)
