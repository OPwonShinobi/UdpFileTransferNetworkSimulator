import socket
import os
import xml.dom.minidom
import select

# flags
DATA=0 #equivalent to SEND
EOT=1
ACK=2
TIMEOUT=3
CONN=4
CMDS=('DATA','EOT','ACK','TIMEOUT','CONN')

BUFFER_SIZE=8192 #8KB

SEND_PORT= 7005
RECV_PORT= 7006
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
        self.socket = socket
        self.ip = ip
        self.port = port

class Packet:
    num = 0 #seqNum or ackNum
    flag = None 
    payload = None
    def __init__(self, flag, num, payload=''):
        self.flag = flag
        self.num = num
        self.payload = payload

    def __eq__(self, other):
        return other.num == self.num and other.flag == self.flag

def clear(): 
    if os.name == 'nt': 
        _ = os.system('cls') 
    else: 
        _ = os.system('clear') 

def initConfigs():
    DOMTree = xml.dom.minidom.parse("config.xml")
    root = DOMTree.documentElement
    hosts = root.getElementsByTagName("host")
    global SENDER_IP, RECEIVER_IP, SIMULATOR_IP
    global ber_rate
    global timeout_sec, send_delay_sec
    global window_size
    for host in hosts:
        if host.getAttribute('id') == 'simulator':
            ber_rate = float(host.getElementsByTagName('ber_rate')[0].childNodes[0].data)
            SIMULATOR_IP = host.getElementsByTagName('ip')[0].childNodes[0].data
        if host.getAttribute('id') == 'sender':
            SENDER_IP = host.getElementsByTagName('ip')[0].childNodes[0].data
            SEND_PORT = int(host.getElementsByTagName('port')[0].childNodes[0].data)
            timeout_sec = float(host.getElementsByTagName('timeout_sec')[0].childNodes[0].data)
            send_delay_sec = float(host.getElementsByTagName('send_delay_sec')[0].childNodes[0].data)
            window_size = int(host.getElementsByTagName('window_size')[0].childNodes[0].data)
        if host.getAttribute('id') == 'receiver':
            RECEIVER_IP = host.getElementsByTagName('ip')[0].childNodes[0].data
            RECV_PORT = int(host.getElementsByTagName('port')[0].childNodes[0].data)

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

def sendPacket(destnSocketHost,packet):
    paddedSeqNum = '{:0>4}'.format(str(packet.num))
    paddedPayloadLen = '{:0>4}'.format(len(packet.payload))
    packetStr = str(packet.flag) + paddedSeqNum + paddedPayloadLen + packet.payload
    sendStr(destnSocketHost,packetStr)

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
        packetStr=recvStr(readFromSocket)
        cursor = 0;
        flag =int(packetStr[cursor])
        cursor += 1
        seqNum = int(packetStr[cursor:cursor+4])
        cursor += 4
        msgLen=int(packetStr[cursor:cursor+4])
        cursor += 4
        msg=packetStr[cursor:cursor+msgLen]
    return Packet(flag, seqNum, msg)


