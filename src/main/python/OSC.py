from PyQt5.QtCore import (QObject, pyqtSignal, QTimer, Qt, pyqtSlot, QThread,
                            QPointF, QRectF, QLineF, QRect)
from pythonosc import udp_client, osc_message_builder, dispatcher, osc_server
import logging
import threading

class ClientOSC(QObject):
    """Connects to OSC server to send OSC messages to server
    input: ip of qlab machine, input port number
    default localhost, 53000 (QLab settings)"""
    def __init__(self, ip="127.0.0.1", port=53000):
        QObject.__init__(self)
        self.ip = ip
        self.port = port
        self.client = udp_client.UDPClient(ip, port)
        self.i = 0
    pyqtSlot(object)
    def emit(self, cuenum):
        # msg_raw = f"/cue/{self.i}"
        self.i += 1
        # bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
        msg = osc_message_builder.OscMessageBuilder(address=f"/cue")
        msg.add_arg(cuenum)
        # bundle.add_content(msg.build())
        msg = msg.build()
        self.client.send(msg)
        # logging.info(f"message {msg} sent")

class ServerOSC(QObject):
    serverSignal = pyqtSignal(object)
    
    def __init__(self, ip = "127.0.0.1", port = 53000):
        QObject.__init__(self)
        disp = dispatcher.Dispatcher()

        disp.set_default_handler(self.globalReceiver)
        disp.map
        self.server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        logging.info(f"Serving on {self.server.server_address}")

        self.serverThread = threading.Thread(target=self.server.serve_forever)
        self.serverThread.name = "customServerThread"
        self.serverThread.start()

    def print_volume_handler(self, unused_addr, args, volume):
        logging.debug(f"volume handler {args}")
        print("[{0}] ~ {1}".format(args[0], volume))

    def print_compute_handler(self, unused_addr, args, volume):
        logging.debug(f"compute handler got {args}")
        try:
            print("[{0}] ~ {1}".format(args[0], args[1](volume)))
        except ValueError: pass

    def globalReceiver(self, address, *args):
        logging.debug(f"global receiver got {address} {args}")
        self.serverSignal.emit(args)

    @pyqtSlot()
    def shutdown(self):
        logging.debug(f"shutting down osc server")
        self.server.shutdown()
        logging.debug(f"osc server is down")

    
