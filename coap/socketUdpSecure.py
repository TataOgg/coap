from __future__ import with_statement
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log = logging.getLogger('socketUdpReal')
log.setLevel(logging.ERROR)
log.addHandler(NullHandler())

#sockets
import socketUdpReal
import threading
import socket
import time
from os import path
#dtls imports
import dtls
import ssl



class socketUdpSecure(socketUdpReal.socketUdpReal):

    BUFSIZE = 1024

    def __init__(self, ipAddress, udpPort, callback):

        #log
        log.debug('creating secure instance')

        # initialize the parent class
        socketUdpReal.socketUdpReal.__init__(self, ipAddress, udpPort, callback)

        # change name
        self.name = 'socketUdpSecureRead@%s:%s' % (self.ipAddress, self.udpPort)


    #======================== public ==========================================

    #======================== private =========================================

    def initializeSocket(self):
        #patch DTLS
        dtls.do_patch()

        cert_path = path.join(path.abspath(path.dirname(__file__)), "certs")
        #socket wrapper
        ## if we are going to add certificates it is done by:
        ## ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM),ca_certs="server.crt",cert_reqs=ssl.CERT_REQUIRED)
        self.socket_handler = ssl.wrap_socket(
                                                socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                                                server_side=True,
                                                certfile=path.join(cert_path, "server-key.pem"), 
                                                keyfile=path.join(cert_path, "server.cert.pem"),
                                                ca_certs=path.join(cert_path, "ca-cert.pem"))
        self.socket_handler.bind((self.ipAddress, self.udpPort))
