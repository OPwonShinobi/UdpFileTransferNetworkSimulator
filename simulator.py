import utils
import traceback
import threading
import time

def main():
    utils.initConfigs()
    print('Simulator started, ctrl+c or enter exit to exit');
    sendSocket = utils.createUdpSocket(utils.SEND_PORT)
    sendHost = utils.SocketHost(sendSocket, utils.SENDER_IP, utils.SEND_PORT)
    recvSocket = utils.createUdpSocket(utils.RECV_PORT)
    recvHost = utils.SocketHost(recvSocket, utils.RECEIVER_IP, utils.RECV_PORT)
    try:
        sendThread = threading.Thread(target=senderHandler, args=(sendHost,recvHost), daemon=True)
        sendThread.start()
        recvThread = threading.Thread(target=receiverHandler, args=(sendHost,recvHost), daemon=True)
        recvThread.start()
        while True:
            userInput = input('>>> ').strip().upper()
            if userInput == 'EXIT':
                break
            if userInput == 'RELOAD':
                # utils.initConfigs()
                pass
    except KeyboardInterrupt:
        print('\nexit called.')
    except Exception as e: 
        traceback.print_exc()
    finally:
        sendSocket.close()
        recvSocket.close()

def senderHandler(sendHost, recvHost):
    print('send thread started')
    try:
        while True:
            (flag, seqNum, msg) = utils.readPacket(sendHost.socket)
            print('sender packet: flag: {} seqNum: {} payload: {}'.format(utils.CMDS[flag], seqNum, msg))
            utils.sendPacket(recvHost,flag,seqNum,msg)
    except Exception as e:
        raise e

def receiverHandler(sendHost, recvHost):
    print('recv thread started')
    try:
        while True:
            (flag, ackNum, msg) = utils.readPacket(recvHost.socket)
            print('receiver packet: flag: {} ackNum: {} payload: {}'.format(utils.CMDS[flag], ackNum, msg))
            utils.sendPacket(sendHost,flag,ackNum,msg)
    except Exception as e:
        raise e

# run main
main()