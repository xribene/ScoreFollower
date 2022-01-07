from PyQt5.QtCore import (QObject, pyqtSignal, QTimer, Qt, pyqtSlot, QThread,
                            QPointF, QRectF, QLineF, QRect)
from pythonosc import udp_client, osc_message_builder, dispatcher, osc_server
import math 
import argparse

class ClientOSC(QObject):
    """Connects to OSC server to send OSC messages to server
    input: ip of qlab machine, input port number
    default localhost, 53000 (QLab settings)"""
    def __init__(self, ip="127.0.0.1", port=53000):
        QObject.__init__(self)
        self.ip = ip
        self.port = port
        self.client = udp_client.UDPClient(ip, port)
    pyqtSlot(object)
    def emit(self, cuenum):
        msg_raw = f"/cue/{cuenum}/start"
        print(f'{msg_raw} sent')
        msg = osc_message_builder.OscMessageBuilder(msg_raw)
        msg = msg.build()
        self.client.send(msg)

class ServerOSC(QObject):
    def __init__(self, ip = "127.0.0.1", port = 53000):
        QObject.__init__(self)
        self.dispatcher = dispatcher.Dispatcher()

        self.dispatcher.map("/filter", print)
        self.dispatcher.map("/volume", self.print_volume_handler, "Volume")
        self.dispatcher.map("/logvolume", self.print_compute_handler, "Log volume", math.log)

        server = osc_server.ThreadingOSCUDPServer(
            (ip, port), dispatcher)
        print("Serving on {}".format(server.server_address))
        server.serve_forever()

    def print_volume_handler(self, unused_addr, args, volume):
        print("[{0}] ~ {1}".format(args[0], volume))

    def print_compute_handler(self, unused_addr, args, volume):
        try:
            print("[{0}] ~ {1}".format(args[0], args[1](volume)))
        except ValueError: pass
