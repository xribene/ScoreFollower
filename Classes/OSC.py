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
    def emit(self, address, arg = None):
        # msg_raw = f"/cue/{self.i}"
        self.i += 1
        # bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
        msg = osc_message_builder.OscMessageBuilder(address=f"{address}")
        if arg:
            msg.add_arg(arg)
        # bundle.add_content(msg.build())
        msg = msg.build()
        self.client.send(msg)
        # logging.info(f"message {msg} sent")

    pyqtSlot(object)
    def changePort(self, port):
        self.port = port
        self.client = udp_client.UDPClient(self.ip, port)

class ServerOSC(QObject):
    serverSignalFromQlab = pyqtSignal(object)
    serverSignalFromTouchDesigner = pyqtSignal(object)
    serverSignalFromUknownSource = pyqtSignal(object)

    def __init__(self, ip = "127.0.0.1", port = 53000):
        QObject.__init__(self)
        disp = dispatcher.Dispatcher()
        disp.map("/reply/*", self.replyReceiver)
        disp.map("/response/*", self.responseReceiver)
        disp.set_default_handler(self.globalReceiver)
        # disp.map
        self.server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        logging.info(f"Serving on {self.server.server_address}")

        self.serverThread = threading.Thread(target=self.server.serve_forever)
        self.serverThread.name = "customServerThread"
        self.serverThread.start()

    def globalReceiver(self, address, *args):
        logging.debug(f"global receiver got {address} {args}")
        self.serverSignalFromUknownSource.emit([address, args])
    def replyReceiver(self, address, *args):
        logging.debug(f"qlab receiver got {address} {args}")
        self.serverSignalFromQlab.emit([address, args])
    def responseReceiver(self, address, *args):
        logging.debug(f"touch receiver got {address} {args}")
        self.serverSignalFromTouchDesigner.emit([address, args])

    @pyqtSlot()
    def shutdown(self):
        logging.debug(f"shutting down osc server")
        self.server.shutdown()
        logging.debug(f"osc server is down") 

if __name__ == "__main__":
    from PyQt5 import QtGui
    from PyQt5.QtWidgets import (QGridLayout, QWidget, QApplication, QLabel, QPushButton,
                                QGridLayout, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QRadioButton)
    from PyQt5.QtCore import (pyqtSlot, QThread, Qt, pyqtSignal)
    
    import sys
    class OscTester(QWidget):
        signalToAligner = pyqtSignal()
        def __init__(self):
            super(OscTester, self).__init__()   


            self.oscClientThread = QThread()
            self.oscClient = ClientOSC(port = 53000)
            self.oscClient.moveToThread(self.oscClientThread)

            self.oscServerThread = QThread()
            self.oscServer = ServerOSC(port = 53001)
            self.oscServer.moveToThread(self.oscServerThread)

            self.oscClientThread.start()

            self.oscServer.serverSignal.connect(self.oscReceiverCallback)

            mainLayout = QVBoxLayout(self) 

            vbox1 = QVBoxLayout()
            hbox1 = QHBoxLayout()
            hbox2 = QHBoxLayout()


            self.labelClientPort = QLabel("client port:")
            self.clientPortText = QLineEdit(self)
            self.clientMessageText = QLineEdit(self)
            self.sendBtn = QPushButton("Send", self)

            hbox1.addStretch()
            hbox1.addWidget(self.labelClientPort)
            hbox1.addWidget(self.clientPortText)
            hbox1.addWidget(self.clientMessageText)
            hbox1.addStretch()
            hbox1.addWidget(self.sendBtn)
            mainLayout.addLayout(hbox1)

            self.labelServerPort = QLabel("listener port:")
            self.serverPortText = QLineEdit(self)
            # self.serverMessageText = QLineEdit(self)
            self.serverMessageText = QTextEdit()
            self.cursor = QtGui.QTextCursor(self.serverMessageText.document())
            self.cursor.setPosition(0)
            self.serverMessageText.setTextCursor(self.cursor) 

            hbox2.addWidget(self.labelServerPort)
            hbox2.addWidget(self.serverPortText)
            # hbox1.addStretch()
            vbox1.addLayout(hbox2)
            vbox1.addWidget(self.serverMessageText)

            mainLayout.addLayout(vbox1)
            self.setLayout(mainLayout)
            self.sendBtn.clicked.connect(self.sendMessage)


            self.resize(1000,1000)
            self.show()

        def closeEvent(self, event):
            self.oscServer.shutdown()
            print(f"close Event")

        @pyqtSlot()
        def sendMessage(self):
            print(self.clientMessageText.text())
            self.oscClient.emit(self.clientMessageText.text(), cuenum = 0)

        @pyqtSlot(object)
        def oscReceiverCallback(self, args):
            logging.debug(f"main osc receiver got {args}")
            self.cursor.setPosition(0)
            self.serverMessageText.setTextCursor(self.cursor)
            # self.serverMessageText.insertHtml(f"<font color='green' size='6'><red>/cue <b>{args[0]}</b></font><br>")
            self.serverMessageText.insertHtml(f"{args}")
    

    QThread.currentThread().setObjectName('MainThread')
    logging.getLogger('matplotlib.font_manager').disabled = True
    logging.getLogger().setLevel(logging.DEBUG)
    # Uncomment below for terminal log messages
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

    app = QApplication(sys.argv)
    mainWindow = OscTester()
    exit_code = app.exec_()
    sys.exit(exit_code)