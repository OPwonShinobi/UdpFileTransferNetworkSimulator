import utils
import traceback

def main():
    utils.initConfigs()
    utils.clear()
    print('Using configs from config.xml Receiver(this): {}\nSender: {} Simulator: {}'.format(utils.RECEIVER_IP, utils.SIMULATOR_IP, utils.SENDER_IP))
    print('Missing packet timeout seconds:',utils.timeout_sec)
    print('Sender window size:',utils.window_size)
    simulatorSocket = utils.createUdpSocket(utils.RECV_PORT)
    simulatorHost = utils.SocketHost(simulatorSocket, utils.SIMULATOR_IP, utils.RECV_PORT)
    print('Receiver started, listening on port', utils.RECV_PORT,'ctrl+c to exit');
    try:
        sendSocketHost = utils.SocketHost(simulatorSocket, utils.SIMULATOR_IP, utils.SEND_PORT)
        ack_window = []
        while True:
            # block here until client connects
            data_packet = utils.readPacket(simulatorSocket)
            print('Packet recv\'d: {} {} {}'.format(utils.CMDS[data_packet.flag], data_packet.num, data_packet.payload))
            
            ack_packet = utils.Packet(utils.ACK, data_packet.num)
            if len(ack_window) < utils.window_size and ack_packet not in ack_window:
                ack_window.append(ack_packet)
                if len(ack_window) == utils.window_size:
                    print('window size {} filled, sending ACKs {}-{}'.format(utils.window_size, ack_window[0].num, ack_window[utils.window_size-1].num))
                    for packet in ack_window:
                        utils.sendPacket(simulatorHost,packet)
                    ack_window = []
            else:
                print('Ignored dup packet, seq num {}. Curr window size {}'.format(ack_packet.num,len(ack_window)))
    except KeyboardInterrupt:
        print('\nexit called.')
    except Exception as e: 
        traceback.print_exc()
    finally:
        simulatorSocket.close()


# run main
main()