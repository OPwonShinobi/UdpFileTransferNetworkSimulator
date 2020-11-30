import utils
import traceback
import threading
import time
import os
import curses
import random

def printFormatted(line,msg):
    screen_w = os.get_terminal_size().columns
    format_str = '{: <' + str(screen_w) + '}'
    win.addstr(line, 0, format_str.format(msg))

win = None
mainLoop = True
sendLoop = True
recvLoop = True
timerLoop = False
timerInit = False

class HostStats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.packetsRecv = 0
        self.packetsFwd = 0
        self.retransmitions = 0
        self.packetsDropped = 0
        self.lastRecvNum = 0
        self.start = time.time()

def updateDurationDisplay(startTime):
    if timerInit:
        timestamp = time.time() - startTime
        mins = timestamp // 60
        sec = timestamp % 60
        hours = mins // 60
        mins = mins % 60
        printFormatted(26, "Transmission duration: {:0>2}:{:0>2}:{:0>2}".format(int(hours),int(mins),int(sec)))

def main():
    utils.initConfigs()
    utils.clear()
    global win
    win = curses.initscr()
    curses.noecho()
    # utils.clear()
    printFormatted(1, 'Using configs from config.xml Simulator(this): {}\nSender: {} Receiver: {}'.format(utils.SIMULATOR_IP, utils.SENDER_IP, utils.RECEIVER_IP))
    printFormatted(2, 'Bit error rate set to {}'.format(utils.ber_rate))
    printFormatted(3, 'Enter \'reload\' to apply config changes, \'reset\' to clear stats, or \'exit\' to exit')
    sendSocket = utils.createUdpSocket(utils.SEND_PORT)
    sendHost = utils.SocketHost(sendSocket, utils.SENDER_IP, utils.SEND_PORT)
    recvSocket = utils.createUdpSocket(utils.RECV_PORT)
    recvHost = utils.SocketHost(recvSocket, utils.RECEIVER_IP, utils.RECV_PORT)
    try:
        sendThread = threading.Thread(target=senderHandler, args=(sendHost,recvHost), daemon=True)
        sendThread.start()
        recvThread = threading.Thread(target=receiverHandler, args=(sendHost,recvHost), daemon=True)
        recvThread.start()
        inputThread = threading.Thread(target=inputHandler, args=(), daemon=True)
        inputThread.start()
        start = time.time()
        global timerLoop, sendLoop
        while mainLoop:
            win.refresh()
            time.sleep(0.05)
            updateDurationDisplay(start)
            if not timerLoop and sendLoop:
                start = time.time()
                timerLoop = True
    finally:
        sendSocket.close()
        recvSocket.close()
        curses.echo()
        curses.endwin()

def inputHandler():
    userInput = ''
    global sendLoop, recvLoop, timerLoop
    while True:
        printFormatted(0,'Command >>>{}'.format(userInput))
        ch = win.getch()
        if ch in range(32, 127): 
            userInput += chr(ch)
        elif ch == 127 or ch == 8: #backspace
            userInput = userInput[:-1]
        elif ch == 10: #enter
            # reset input after enter
            if userInput.lower() == 'exit':
                break
            elif userInput.lower() == 'reload':
                utils.initConfigs()
                printFormatted(2, '*Config updated* Bit error rate set to {}'.format(utils.ber_rate))
            elif userInput.lower() == 'reset':
                sendLoop, recvLoop, timerLoop = False, False, False
            userInput = ''
    print('exit called')
    global mainLoop
    mainLoop = False

# 1 in utils.ber_rate chance of dropping a packet
# rolls number between 1 and utils.ber_rate, if 1 is rolled, packet is dropped, else it's sent
def checkDropPacket():
    if utils.ber_rate == 0:
        return False
    return random.randint(1, utils.ber_rate) == 1

def senderHandler(sendHost, recvHost):
    senderStats = HostStats()
    avgPacketSize = 1 + 4 + 4 + 20
    global sendLoop, timerInit
    try:
        while True:
            if not sendLoop:
                senderStats.reset()
                sendLoop = True
            printFormatted(5, 'Sender stats:')
            printFormatted(6, '  total packets sent: ' + str(senderStats.packetsRecv))
            printFormatted(7, '  packets forwarded: ' + str(senderStats.packetsFwd))
            printFormatted(8, '  bytes forwarded: ' + str(senderStats.packetsFwd * avgPacketSize))
            printFormatted(9, '  max seq num: ' + str(senderStats.lastRecvNum))
            printFormatted(10, '  retransmitions: ' + str(senderStats.retransmitions))
            printFormatted(11, '  dropped packets: ' + str(senderStats.packetsDropped))
            printFormatted(12, '  packet loss: {:.0f}%'.format((senderStats.packetsDropped / (senderStats.packetsRecv+1)) * 100))
            rate = senderStats.packetsFwd / (time.time()-senderStats.start+1)
            printFormatted(13, '  throughput: {:.2f} packets/second'.format(rate))
            printFormatted(14, '  throughput: {:.2f} bytes/second'.format(rate * avgPacketSize))
            packet = utils.readPacket(sendHost.socket)
            timerInit = True
            if packet.flag == utils.TIMEOUT:
                senderStats.retransmitions +=1 
            else:
                senderStats.packetsRecv += 1
                senderStats.lastRecvNum = packet.num
                if checkDropPacket() == True:
                    senderStats.packetsDropped +=1
                else:    
                    utils.sendPacket(recvHost,packet)
                    senderStats.packetsFwd += 1
            # line 4 is for input
    except Exception as e:
        traceback.print_exc()
        global mainLoop
        mainLoop = False

def receiverHandler(sendHost, recvHost):
    recvStats = HostStats()
    avgPacketSize = 1 + 4 + 4
    global recvLoop
    try:
        while True:
            if not recvLoop:
                recvStats.reset()
                recvLoop = True
            printFormatted(16, 'Receiver stats:')
            printFormatted(17, '  total packets sent: ' + str(recvStats.packetsRecv))
            printFormatted(18, '  packets forwarded: ' + str(recvStats.packetsFwd))
            printFormatted(19, '  bytes forwarded: ' + str(recvStats.packetsFwd * avgPacketSize))
            printFormatted(20, '  max ack num: ' + str(recvStats.lastRecvNum))
            printFormatted(21, '  dropped packets: ' + str(recvStats.packetsDropped))
            printFormatted(22, '  packet loss: {:.0f}%'.format((recvStats.packetsDropped / (recvStats.packetsRecv+1)) * 100))
            rate = recvStats.packetsFwd / (time.time()-recvStats.start+1)
            printFormatted(23, '  throughput: {:.2f} packets/second'.format(rate))
            printFormatted(24, '  throughput: {:.2f} bytes/second'.format(rate * avgPacketSize))
            packet = utils.readPacket(recvHost.socket)
            recvStats.packetsRecv += 1
            recvStats.lastRecvNum = packet.num
            if checkDropPacket() == True:
                recvStats.packetsDropped +=1
            else:    
                utils.sendPacket(sendHost,packet)
                recvStats.packetsFwd += 1
    except Exception as e:
        traceback.print_exc()
        global mainLoop
        mainLoop = False

# run main
main()