import socket
import os
import xml.dom.minidom
import select

SEND_PORT=7005
RECV_PORT=7006
PORT_X=8888

# flags
DATA='0' #equivalent to SEND
EOT='1'
ACK='2'
TIMEOUT='3'
CONN='4'
CMDS=('DATA','EOT','ACK','TIMEOUT','CONN')

BUFFER_SIZE=8192 #8KB

SENDER_IP = None
RECEIVER_IP = None
SIMULATOR_IP = None
ber_rate = None
timeout_sec = None
window_size = None

class SocketHost:
    socket = None
    ip = None
    port = 0
    def __init__(self, socket, ip, port):
        super(SocketHost, self).__init__()
        self.socket = socket
        self.ip = ip
        self.port = port

def initConfigs():
    DOMTree = xml.dom.minidom.parse("config.xml")
    root = DOMTree.documentElement
    hosts = root.getElementsByTagName("host")
    global SENDER_IP
    global RECEIVER_IP
    global SIMULATOR_IP
    global ber_rate
    global timeout_sec
    for host in hosts:
        if host.getAttribute('id') == 'simulator':
            ber_rate = float(host.getElementsByTagName('ber_rate')[0].childNodes[0].data)
            SIMULATOR_IP = host.getElementsByTagName('ip')[0].childNodes[0].data
        if host.getAttribute('id') == 'sender':
            SENDER_IP = host.getElementsByTagName('ip')[0].childNodes[0].data
            timeout_sec = float(host.getElementsByTagName('timeout_sec')[0].childNodes[0].data)
        if host.getAttribute('id') == 'receiver':
            RECEIVER_IP = host.getElementsByTagName('ip')[0].childNodes[0].data
    print('Using configs from config.xml\n Sender: {} Simulator: {} Receiver: {}'.format(SENDER_IP, SIMULATOR_IP, RECEIVER_IP))

def createUdpSocket(bindPort=None):
    newSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    newSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if bindPort is not None:
        newSocket.bind(('', bindPort))
        newSocket.setblocking(False)
    return newSocket

def sendStr(destnSocketHost,str):
    total_sent = 0
    total = len(str)
    byte_str = str.encode()
    while total_sent < total:
        bytes_sent = destnSocketHost.socket.sendto(byte_str[total_sent:], (destnSocketHost.ip, destnSocketHost.port))
        if bytes_sent == 0:
            raise RuntimeError("sendStr socket disconnected")
        total_sent += bytes_sent


def recvStr(recvSocket):
    chunk, addr = recvSocket.recvfrom(BUFFER_SIZE)
    # unlike tcp recv(), if sendto(10) but we call recvfrom(1), 9bytes are discarded 
    if not chunk:
        raise RuntimeError('recvStr socket disconnected while reading!')
    return chunk.decode()

def sendPacket(destnSocketHost,flag,seqNum,payload=''):
    seqNumStr = str(seqNum)
    seqNumLen = '{:0>3}'.format(len(seqNumStr))
    payloadLen = '{:0>3}'.format(len(payload))
    packet = str(flag) + str(seqNumLen) + seqNumStr + str(payloadLen) + payload
    sendStr(destnSocketHost,packet)

def readPacket(readFromSocket,timeout_sec=None):
    flag, seqNum, msg, readyList = TIMEOUT, 0, '', []
    # settimeout is more work cause have to reset timeout every time afterwards
    if timeout_sec is None:
        # blocking select
        readyList = select.select([readFromSocket], [], [])
    else:
        # nonblocking select
        readyList = select.select([readFromSocket], [], [], timeout_sec)
    
    if readyList[0]:
        packet=recvStr(readFromSocket)
        cursor = 0;
        flag =int(packet[cursor])
        cursor += 1
        seqNumLen =int(packet[cursor:cursor+3])
        cursor += 3
        seqNum = int(packet[cursor:cursor+seqNumLen])
        cursor += seqNumLen
        msgLen=int(packet[cursor:cursor+3])
        cursor += 3
        msg=packet[cursor:cursor+msgLen]
    return (flag, seqNum, msg)


