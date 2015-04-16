from __future__ import with_statement
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log = logging.getLogger('socketUdpReal')
log.setLevel(logging.ERROR)
log.addHandler(NullHandler())

#sockets
import socketUdp
import threading
import socket
import time

#dtls imports
import dtls
import ssl



class socketUdpSecure(socketUdp.socketUdp):

    BUFSIZE = 1024

    def __init__(self, ipAddress, udpPort, callback):

        #log
        log.debug('creating secure instance')

        # initialize the parent class
        socketUdp.socketUdp.__init__(self, ipAddress, udpPort, callback)

        # change name
        self.name = 'socketUdpSecureRead@%s:%s' % (self.ipAddress, self.udpPort)
        self.callback = callback

        # local variables
        self.socketLock = threading.Lock()

        # open UDP port
        try:
            #patch DTLS
            dtls.do_patch()

            #socket wrapper
            self.socket_handler = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
            self.socket_handler.bind((self.ipAddress, self.udpPort))

        except socket.error, err:
            log.critical(err)
            raise

        #start myself
        self.start()

    #======================== public ==========================================

    def sendUdp(self, destIp, destPort, msg):
        # message to string
        msg = ''.join([chr(b) for b in msg])

        # send over dtls over UDP
        with self.socketLock:
            self.socket_handler.sendto(msg, (destIp, destPort))

        self._incrementTx()

    def close(self):
        # declare that this thread has to stop
        self.goOn = False

        #send some dummy value into dthe socket to trigger a read
        self.socket_handler.sendto( 'stop', ('127.0.0.1', self.udpPort) )

        #wait for this thread to exit
        self.join()

    #======================== private =========================================

    def run(self):
        while self.goOn:
            try:
                # blocking wait for something from UDP socket
                raw, conn = self.socket_handler.recvfrom(self.BUFSIZE)
            except socket.error, err:
                log.critical("socket error: %s" % (err))
                self.goOn = False
                continue
            else:
                if not raw:
                    log.error("no data read from socket, stopping")
                    self.goOn = False
                    continue
                if not self.goOn:
                    log.warning("goOn is false")
                    continue

                timestamp = time.time()
                source = (conn[0], conn[1])
                data = [ord(b) for b in raw]

                log.debug("got %s from %s at %s" % (data, source, timestamp))

                self.callback(timestamp, source, data)

        #close the socket
        self.socket_handler.close()

        log.info("tearDown")
