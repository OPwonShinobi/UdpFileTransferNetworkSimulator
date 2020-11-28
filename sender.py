import utils
import traceback

def main():
    utils.initConfigs()
    simulatorSocket = utils.createUdpSocket(utils.SEND_PORT)
    simulatorHost = utils.SocketHost(simulatorSocket, utils.SIMULATOR_IP, utils.SEND_PORT)
    print('Sender started, connecting to simulator ', utils.SIMULATOR_IP,' ctrl+c to exit')
    try:
        seqNum = 1
        flag = utils.DATA
        utils.sendPacket(simulatorHost,flag,seqNum,'Hello')
        (flag, seqNum, msg) = utils.readPacket(simulatorSocket, utils.timeout_sec)
        print('simulator returned ACK: {} {} {}'.format(flag, seqNum, msg))
    except KeyboardInterrupt:
        print('\nexit called.')
    except Exception as e: 
        traceback.print_exc()
    finally:
        simulatorSocket.close()


# run main
main()