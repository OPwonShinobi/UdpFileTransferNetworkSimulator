import os
import utils
import traceback

def main():
    listenSocket = utils.createTcpSocket(utils.SERVER_COMM_PORT)
    listenSocket.listen(5)                           
    print('Server started listening on port', utils.SERVER_COMM_PORT,'ctrl+c to exit');
    try:
        while True:
            controlSocket, clientIpPort = listenSocket.accept()
            isConnected=True
            clientIp = clientIpPort[0]
            print('New client:', clientIpPort)
            while isConnected:
                data = controlSocket.recv(1)
                if not data:
                    print ('client disconnected:', clientIpPort)
                    isConnected=False
                    continue
                cmd = data.decode()
                print('Client', clientIp, 'request', utils.CMDS[int(cmd)])

                dataSocket = utils.createTcpSocket(utils.SERVER_TX_PORT)
                dataSocket.connect((clientIp, utils.PORT_X))

                # cant use utils.readCmdPacket(controlSocket), already got 1 byte to test client connection
                msgLen=int(utils.recvStr(controlSocket,3))
                filename=utils.recvStr(controlSocket, msgLen)

                if cmd == utils.GETALL:
                    handleGetAll(dataSocket)
                elif cmd == utils.GET:
                    handleGet(dataSocket, filename)                
                elif cmd == utils.SEND:
                    handleSend(dataSocket, filename)
                dataSocket.close()
    except KeyboardInterrupt:
        print('\nexit called.')
    except Exception as e: 
        traceback.print_exc()
    finally:
        listenSocket.close()


def handleGetAll(dataSocket):
    filenames = '  '.join(os.listdir('./files'))
    utils.sendDataPacket(dataSocket,filenames)


def handleGet(dataSocket, filename):
    if not os.path.isfile('./files/' + filename):
        utils.sendDataPacket(dataSocket, utils.NOT_FOUND)
    else:
        utils.sendDataPacket(dataSocket, utils.FOUND)
        utils.sendFile(dataSocket, filename)


def handleSend(dataSocket, filename):
    utils.recvFile(dataSocket, filename)

# run main
main()