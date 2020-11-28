import utils
import traceback

def main():
    utils.initConfigs()
    simulatorSocket = utils.createUdpSocket(utils.RECV_PORT)
    simulatorHost = utils.SocketHost(simulatorSocket, utils.SIMULATOR_IP, utils.RECV_PORT)
    print('Receiver started, listening on port', utils.RECV_PORT,'ctrl+c to exit');
    try:
        sendSocketHost = utils.SocketHost(simulatorSocket, utils.SIMULATOR_IP, utils.SEND_PORT)
        while True:
            # block here until client connects
            (flag, seqNum, msg) = utils.readPacket(simulatorSocket)
            print('Packet recv\'d: {} {} {}'.format(utils.CMDS[flag], seqNum, msg))
            utils.sendPacket(simulatorHost,flag,seqNum,msg)
    except KeyboardInterrupt:
        print('\nexit called.')
    except Exception as e: 
        traceback.print_exc()
    finally:
        simulatorSocket.close()


# run main
main()