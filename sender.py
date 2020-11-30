import utils
import traceback
import random
import string
import time

def getRngString():
    return "".join( [random.choice(string.ascii_letters) for i in range(20)] )

def main():
    utils.initConfigs()
    utils.clear()
    print('Using configs from config.xml: Sender (this) {}\n Simulator: {} Receiver: {}'.format(utils.SENDER_IP, utils.SIMULATOR_IP, utils.RECEIVER_IP))
    print('ACK timeout seconds: ',utils.timeout_sec)
    print('Window size: ',utils.window_size)
    simulatorSocket = utils.createUdpSocket(utils.SEND_PORT)
    simulatorHost = utils.SocketHost(simulatorSocket, utils.SIMULATOR_IP, utils.SEND_PORT)
    print('Sender started, connecting to simulator ', utils.SIMULATOR_IP,' ctrl+c to exit')
    try:
        # make packets
        window = []
        seqNum = 1
        while True:
            for x in range(1,utils.window_size):
                packet = utils.Packet(utils.DATA, seqNum, getRngString())
                seqNum = seqNum + 1 if seqNum <= 998 else 1
                window.append(packet)
            packet = utils.Packet(utils.EOT, seqNum, getRngString())
            seqNum += 1
            window.append(packet)

            retransmit = True
            while retransmit:
                retransmit = False
                timed_out = False           
                for packet in window:
                    utils.sendPacket(simulatorHost,packet)
                    print('packet to simulator: {} {} {}'.format(utils.CMDS[packet.flag], packet.num, packet.payload))
                    time.sleep(utils.send_delay_sec)
                print('window sent included packets {}-{}'.format(window[0].num, window[utils.window_size-1].num))
                for x in window:
                    ack_packet = utils.readPacket(simulatorSocket, utils.timeout_sec)
                    if ack_packet.flag == utils.TIMEOUT:
                        timeout_msg = 'timeout while waiting for ACKs, resending packets {}-{}'.format(window[0].num, window[utils.window_size-1].num)
                        print(timeout_msg)
                        info_packet = utils.Packet(utils.TIMEOUT, 0, timeout_msg)
                        utils.sendPacket(simulatorHost,info_packet)
                        timed_out = True
                        break
                    else:
                        print('ACK recv\'d: {} {} {}'.format(utils.CMDS[ack_packet.flag], ack_packet.num, ack_packet.payload))
                if timed_out:
                    retransmit = True
            # end retransmit
            window = []
    except KeyboardInterrupt:
        print('\nexit called.')
    except Exception as e: 
        traceback.print_exc()
    finally:
        simulatorSocket.close()


# run main
main()