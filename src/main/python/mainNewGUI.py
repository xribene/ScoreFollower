###########import statements#################
##standard PyQt imports (thanks christos!)###
from PyQt5 import QtGui, QtCore, QtSvg
from PyQt5.QtWidgets import (QMainWindow, QApplication, QCheckBox, QComboBox, QDateTimeEdit,QMessageBox,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy, QStatusBar,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit, QSplashScreen,
        QVBoxLayout, QWidget,QLCDNumber, QDoubleSpinBox,QGraphicsItem, QGraphicsItemGroup, QGraphicsEllipseItem, QGraphicsObject, QGraphicsLineItem,
                         QGraphicsScene, QGraphicsView, QSpacerItem, QStyle, QWidget, QLabel, QPlainTextEdit, QHBoxLayout, QMenuBar, QTextEdit, QGridLayout, QAction, QActionGroup, QToolBar, QToolBox, QToolButton)

from PyQt5.QtCore import (QObject, pyqtSlot, QThread, Qt, pyqtSignal)
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import qdarkstyle

# import pyqtgraph as pg
##############################################
###############################################
import queue #threadsafe queue
import sys
from pathlib import Path
import logging
from tslearn.metrics import dtw, dtw_path
from scipy.spatial.distance import cdist
import numpy as np
from matplotlib import pyplot as plt
###############################################
from AudioRecorder import AudioRecorder
from Chromatizer import Chromatizer
from Aligner import Aligner
# from OSCClient import OSCclient
from MenuBar import MenuBar
from ToolBar import ToolBar
from OSC import ClientOSC, ServerOSC
import music21.alpha
import encodings
from librosa import * 
from offline.utils_offline import Params, getChromas, getCuesDict
from fbs_runtime.application_context.PyQt5 import ApplicationContext

#####################################################
## Qt app instantiation -> thread setup
#####################################################
# class ApplicationContext(object):
#     """
#     Manages the resources. There is not
#     actual need for this Class. The only reason
#     to use it is for compatibility with the fbs
#     library, in order to create an exe file for the app
#     Methods
#     -------
#     get_resource(name) : str
#         returns the path of a resource by name
#     """
#     def __init__(self):
#         self.path = Path.cwd() / 'resources'
#     def get_resource(self, name):
#         return str(self.path / name)

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class QLabBox(QGroupBox):
    def __init__(self, appctxt, parent):
        super(QLabBox, self).__init__()
        # Set the logger
        # logTextBox = QTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s -%(threadName)s -%(lineno)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)
        # policy = QSizePolicy(QSizePolicy.Expanding,
        #                            QSizePolicy.Expanding)
        # self.setSizePolicy(policy)
        self.setParent(parent)
        # initializations
        self.config = Params(appctxt.get_resource("config.json"))
        self.setObjectName("QLabBox")
        self.setTitle("&QLab - Disconnected")
        self.setStyleSheet('#QLabBox:title {color: rgb(0,0,0);background-color: rgb(200, 0, 0);}')
        self.setMinimumSize(1000,300)
        self.appctxt = appctxt
        self.layout = QHBoxLayout(self)

        # self.status = QStatusBar(self)
        # self.status.showMessage("Disconnected")
        # self.status.setStyleSheet("background-color: rgb(0, 255, 0);")

        self.clientManualMessageText = QLineEdit(self)
        self.clientAutoMessageText = QTextEdit()
        self.cursor1 = QtGui.QTextCursor(self.clientAutoMessageText.document())
        self.cursor1.setPosition(0)
        self.clientAutoMessageText.setTextCursor(self.cursor1) 
        self.serverMessageText = QTextEdit()
        self.cursor2 = QtGui.QTextCursor(self.serverMessageText.document())
        self.cursor2.setPosition(0)
        self.serverMessageText.setTextCursor(self.cursor2) 

        self.sendGroup = QGroupBox("&Sent")
        self.sendGroup.setParent = self
        self.receiveGroup = QGroupBox("&Receive")
        self.receiveGroup.setParent = self
        self.sendLayout = QVBoxLayout(self.sendGroup)
        self.receiveLayout = QVBoxLayout(self.receiveGroup)
        
        self.receiveLayout.addWidget(self.serverMessageText)
        self.receiveGroup.setLayout(self.receiveLayout)

        # self.sendLayout.addWidget(self.status)
        self.sendLayout.addWidget(self.clientManualMessageText)
        self.sendLayout.addWidget(self.clientAutoMessageText)
        self.sendGroup.setLayout(self.sendLayout)

        self.layout.addWidget(self.sendGroup)
        self.layout.addWidget(self.receiveGroup)

        
        # self.sendGroup.setSizePolicy(policy)
        # self.receiveGroup.setSizePolicy(policy)
        # self.clientAutoMessageText.setSizePolicy(policy)
        # self.clientManualMessageText.setSizePolicy(policy)
        # self.serverMessageText.setSizePolicy(policy)

        # layout.setColumnMinimumWidth(0, 50) 
        # self.layout.setColumnMinimumWidth(1, 30)
        # layout.setRowMinimumHeight(0, 20) 
        # layout.setRowMinimumHeight(1, 20) 
        
        #layout.setRowStretch(5, 1)
        self.setLayout(self.layout)
    def changeTitle(self, status):
        if status is True:
            self.setTitle("&QLab - Connected")
            self.setStyleSheet('#QLabBox:title {color: rgb(0,0,0);background-color: rgb(0, 200, 0);}')
        else:
            self.setTitle("&QLab - Disconnected")
            self.setStyleSheet('#QLabBox:title {color: rgb(0,0,0);background-color: rgb(200, 0, 0);}')
    def setGreenTitle(self, workspaceID):
        self.setTitle(f"&QLab - Connected - {workspaceID}")
        self.setStyleSheet('#QLabBox:title {color: rgb(0,0,0);background-color: rgb(0, 200, 0);}')
    def setRedTitle(self):
        self.setTitle("&QLab - Disconnected")
        self.setStyleSheet('#QLabBox:title {color: rgb(0,0,0);background-color: rgb(200, 0, 0);}')

class ScoreBox(QGroupBox):
    def __init__(self, appctxt, parent):
        super(ScoreBox, self).__init__()
        # Set the logger
        # logTextBox = QTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s -%(threadName)s -%(lineno)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)

        # initializations
        self.config = Params(appctxt.get_resource("config.json"))
        self.setTitle("&ScoreBox")
        self.setFixedSize(300,300)
        self.appctxt = appctxt
        self.layout = QGridLayout(self)
        self.barLabel = QLabel("Bar")
        self.cueLabel = QLabel("Cue")
        self.barLcd = QLCDNumber()
        self.barLcd = QLCDNumber(self)
        self.barLcd.display(0)
        self.barLcd.setDigitCount(3)
        # self.barLcd.setFixedHeight(35)
        # self.barLcd.setFixedWidth(35)
        self.cueLcd = QLCDNumber()
        self.cueLcd = QLCDNumber(self)
        self.cueLcd.display(0)
        self.cueLcd.setDigitCount(3)
        self.barLabel.setBuddy(self.barLcd)
        self.cueLabel.setBuddy(self.cueLcd)

        self.dropdown = QComboBox(self)
        self.dropdown.addItem("Jetee")

        self.layout.addWidget(self.dropdown, 0, 0, 1, 1,Qt.AlignCenter)
        # self.layout.addWidget(self.bar)

        self.layout.addWidget(self.barLabel, 1, 0, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.barLcd, 1, 1, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.cueLabel, 2, 0, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.cueLcd, 2, 1, 1, 1, Qt.AlignCenter)
        # layout.setColumnMinimumWidth(0, 50) 
        # self.layout.setColumnMinimumWidth(1, 30)
        # layout.setRowMinimumHeight(0, 20) 
        # layout.setRowMinimumHeight(1, 20) 
        
        #layout.setRowStretch(5, 1)
        self.setLayout(self.layout)

class AlignBox(QGroupBox):
    def __init__(self, appctxt, parent):
        super(AlignBox, self).__init__()
        # Set the logger
        # logTextBox = QTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s -%(threadName)s -%(lineno)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)

        # initializations
        self.config = Params(appctxt.get_resource("config.json"))
        self.setTitle("&Alignment")
        self.appctxt = appctxt
        self.layout = QGridLayout(self)

        self.win = pg.GraphicsWindow(size=(500,500))
        self.setMinimumSize(300,300)
        self.plot = self.win.addPlot(title = "Minimum Cost Path",
                                  labels = {
                                  'bottom':"Audio Frames",
                                  'left':"Score Frames"},
                                   backround = "white")
        # self.curve = self.p.plot(pen="r", background="w")
        # self.plot = pg.plot()
        self.scatter = pg.ScatterPlotItem(
            size=3, brush=pg.mkBrush(255, 255, 255, 120))
        self.plot.addItem(self.scatter)
        # layout
        
        
        self.layout.addWidget(self.win, 0, 0, 1, 1, Qt.AlignCenter)
        # layout.setColumnMinimumWidth(0, 50) 
        # self.layout.setColumnMinimumWidth(1, 30)
        # layout.setRowMinimumHeight(0, 20) 
        # layout.setRowMinimumHeight(1, 20) 
        
        #layout.setRowStretch(5, 1)
        self.setLayout(self.layout)

    def updatePlot(self, t,j):
        spot = [{'pos': np.array([t,j]), 'data': 1}]
        self.scatter.addPoints(spot)

class QLabInterface(QObject):
    # signalToAligner = pyqtSignal()
    def __init__(self, appctxt, oscClient, oscListener, qLabGroup):
        super(QLabInterface, self).__init__()

        # initializations
        self.config = Params(appctxt.get_resource("config.json"))
        self.setObjectName("QLabInterface")
        self.appctxt = appctxt
        self.oscClient = oscClient
        self.oscListener = oscListener
        self.qLabGroup = qLabGroup
        self.connectionStatus = False
        self.greetingsCnt = 0
        self.greetingsRsp = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.checkConnection)
        self.timer.start(1000)

        self.thumpsCnt = 0
        # self.thumpsRsp = 0
        self.workspaceID = None

    def getCurrentCue(self):
        pass

    def sendThump(self):
        self.oscClient.emit("/thump")
        self.thumpsCnt += 1

    def sendGreeting(self):
        self.oscClient.emit("/version")
        self.greetingsCnt += 1
        # self.rspTimer = QtCore.QTimer()
        # self.rspTimer.setSingleShot(True)
        # self.rspTimer.singleShot(3000, self.connectionLost)
    def sendCueTrigger(self, cue):
        address = f"/workspace/{self.workspaceID}/playhead/{cue['ind']}"
        self.oscClient.emit(address, arg = None)
        self.updateClientText(address, args = None)

    def checkConnection(self):
        print(f"{self.connectionStatus} {self.greetingsCnt} - {self.greetingsRsp}")
        if self.greetingsCnt > self.greetingsRsp + 1:
            if self.connectionStatus:
                self.connectionStatus = False
                self.workspaceID = None
                self.qLabGroup.setRedTitle()
        self.sendGreeting()
        if self.workspaceID is None:
            self.sendThump()

    # def newCues(self, cues):
    #     for cue in cues:
    #         if cue["type"] == "cue":
    #             self.sendCueTrigger()

                
    @pyqtSlot()
    def sentManualOscMessage(self):
        print(self.qLabGroup.clientManualMessageText.text())
        #TODO call the qlabInterface not the oscClient directly
        address = self.qLabGroup.clientManualMessageText.text()
        
        self.oscClient.emit(address, arg = None)
        self.updateClientText(address, args = None)
        # self.qLabGroup.cursor1.setPosition(0)
        # self.qLabGroup.clientAutoMessageText.setTextCursor(self.qLabGroup.cursor1)
        # self.qLabGroup.clientAutoMessageText.insertHtml(self.qLabGroup.clientManualMessageText.text()+"<br>")

    def thumpCallback(self, addressParts, args):
        logging.debug(f"Thump Response {addressParts} and {args}")
        if self.workspaceID is None:
            self.workspaceID = addressParts[2]
            self.qLabGroup.setGreenTitle(self.workspaceID)
        elif self.workspaceID:
            self.updateListenerText(addressParts, args)

    def versionCallback(self, address, args):
        if "ok" in args[0]:
            self.greetingsRsp += 1
            if not self.connectionStatus:
                self.greetingsRsp = 0
                self.greetingsCnt = 0
                self.connectionStatus = True
                self.qLabGroup.setGreenTitle(self.workspaceID)
        # logging.debug(f"Thump Response {address} and {args}")

    def updateListenerText(self, address, args):
        if isinstance(address, str):
            address = address.split("/")[1:]
        self.qLabGroup.cursor2.setPosition(0)
        self.qLabGroup.serverMessageText.setTextCursor(self.qLabGroup.cursor2)
        self.qLabGroup.serverMessageText.insertHtml(f"/{'/'.join(address)}<br>{args}<br><br>")

    def updateClientText(self, address, args):
        if isinstance(address, str):
            address = address.split("/")[1:]
        self.qLabGroup.cursor1.setPosition(0)
        self.qLabGroup.clientAutoMessageText.setTextCursor(self.qLabGroup.cursor1)
        self.qLabGroup.clientAutoMessageText.insertHtml(f"/{'/'.join(address)}<br>{args}<br><br>")

    @pyqtSlot(object)
    def qLabResponseCallbackRouter(self, load):
        address = load[0]
        args = load[1]
        addressParts = address.split("/")[1:]

        # first part should be always "reply"
        print(addressParts)
        if addressParts[0] != "reply":
            raise
        
        # check if this is a response to Version
        if addressParts[1] == "version":
            self.versionCallback(addressParts, args)
        else:
            # check if this is a response to THUMP
            if addressParts[3] == "thump":
                self.thumpCallback(addressParts, args)
            else:
                self.updateListenerText(addressParts, args)
                logging.debug(f"QLabInterface osc receiver got {address} and {args}")
            

class ScoreFollower(QWidget):
    signalToAligner = pyqtSignal()
    def __init__(self, appctxt):
        super(ScoreFollower, self).__init__()
        # Set the logger
        # logTextBox = QTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s -%(threadName)s -%(lineno)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)

        # initializations
        self.config = Params(appctxt.get_resource("config.json"))
        self.setObjectName("ScoreFollower")
        self.appctxt = appctxt

        # gui elements
        self.menuBar = MenuBar(self)
        self.toolbar = ToolBar(appctxt = appctxt, parent = self, config = self.config)
        self.scoreGroup = ScoreBox(self.appctxt, self)
        self.alignGroup = AlignBox(self.appctxt, self)
        self.qLabGroup = QLabBox(self.appctxt, self)        
        mainLayout = QGridLayout(self) 
        # mainLayout.addWidget(logTextBox.widget)
        mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.toolbar, 0, 0, 10, 100, Qt.AlignCenter|Qt.AlignTop)#, 0,0,3,1, Qt.AlignLeft|Qt.AlignTop)
        mainLayout.addWidget(self.scoreGroup, 10, 0, 50, 50, Qt.AlignLeft|Qt.AlignTop)
        mainLayout.addWidget(self.alignGroup, 10, 50, 50, 50, Qt.AlignLeft|Qt.AlignTop)
        # verticalSpacer = QSpacerItem(100, 40, QSizePolicy.Minimum, QSizePolicy.Expanding) 
        # mainLayout.addItem(verticalSpacer, 60, 0, 40, 100, Qt.AlignCenter)
        mainLayout.addWidget(self.qLabGroup, 60, 0, 40, 100)#, Qt.AlignLeft)
        self.setLayout(mainLayout)
        self.resize(1000,1000)
        self.show()

        ## Initializations 
        self.plotEvery = self.config.plotPeriod
        self.lastJ = -1
        self.pieceName = "jetee" # TODO get that from the dropdown menu
        # get the cues dict
        self.cuesDict = getCuesDict(filePath = Path(appctxt.get_resource(f"{self.pieceName}.xml")), 
                                        sr = self.config.sr, 
                                        hop_length = self.config.hop_length)
        # get the reference chroma vectors
        if self.config.mode == "score" :
            referenceFile = appctxt.get_resource(f"{self.pieceName}4.mid")
        elif self.config.mode == "audio" : 
            referenceFile = appctxt.get_resource(f"{self.pieceName}FF.wav")
        
        self.referenceChromas = getChromas(Path(referenceFile), 
                                                  sr = self.config.sr,
                                                  n_fft = self.config.n_fft, 
                                                  hop_length = self.config.hop_length,
                                                  window_length = self.config.window_length,
                                                  chromaType = self.config.chromaType,
                                                  n_chroma = self.config.n_chroma,
                                                  norm = self.config.norm,
                                                  normAudio = True,
                                                  windowType = self.config.window_type,
                                                  chromafb = None,
                                                  magPower = self.config.magPower
                                                  )
        logging.debug(f"reference Chromas shape is {self.referenceChromas.shape}")
        print(self.referenceChromas.shape)
        repeats = np.ones((self.referenceChromas.shape[0]))
        # repeats[600:800] = 2
        # repeats[1500:1700] = 2
        # self.referenceChromas = np.repeat(self.referenceChromas, list(repeats), axis=0)
        # self.testWavFile = appctxt.get_resource(f"{self.pieceName}FF.wav")
        self.testWavFile = appctxt.get_resource(f"recordedJeteeCuts2.wav")

        self.timer = QtCore.QTimer()
        self.setupThreads()
        self.signalsandSlots()

    def setupThreads(self):
        self.readQueue = queue.Queue()
        self.chromaBuffer = queue.LifoQueue(10000)
        ## threads
        self.audioThread = QThread()
        self.audioRecorder = AudioRecorder(queue = self.readQueue, 
                                           wavfile =  self.testWavFile, # None,#
                                           rate = self.config.sr,
                                           # ! be careful, audio streams chunk is 
                                           # ! equal to the hop_length
                                           chunk = self.config.hop_length,
                                           input_device_index=self.config.input_device_index)
        # ? Not sure if we need a separate thread for the audio stream. 
        # ? pyaudio already calls the callback on a different thread.
        self.audioRecorder.moveToThread(self.audioThread)

        self.chromaThread = QThread()
        self.chromatizer = Chromatizer(
                                    chromaBuffer = self.chromaBuffer,
                                    rate = self.config.sr,
                                    hop_length = self.config.hop_length,
                                    window_length = self.config.window_length,
                                    n_fft = self.config.n_fft,
                                    chromaType = self.config.chromaType,
                                    n_chroma = self.config.n_chroma,
                                    norm = self.config.norm, 
                                    normAudio = False, 
                                    windowType = self.config.window_type,
                                    magPower = self.config.magPower,
                                    chromafb = None,
                        )
        self.chromatizer.moveToThread(self.chromaThread)

        self.oscClientThread = QThread()
        self.oscClient = ClientOSC(ip = self.config.ipOut, port = self.config.portOut)
        self.oscClient.moveToThread(self.oscClientThread)

        self.oscServerThread = QThread()
        self.oscServer = ServerOSC(port = self.config.portIn)
        self.oscServer.moveToThread(self.oscServerThread)

        self.alignerThread = QThread()
        self.aligner = Aligner(self.referenceChromas, self.chromaBuffer,
                                n_chroma = self.config.n_chroma, 
                                c = self.config.c, 
                                maxRunCount = self.config.maxRunCount, 
                                metric = self.config.metric,
                                w = self.config.w_diag)
        self.aligner.moveToThread(self.alignerThread)

        self.qLabInterface = QLabInterface(self.appctxt, self.oscClient, self.oscClient, self.qLabGroup)

        self.audioThread.start()
        self.chromaThread.start()
        self.oscClientThread.start()
        
        # self.oscServerThread.start()
        self.alignerThread.start()
        logging.debug("setup threads done")


    def invokeAlign(self):
        logging.debug(f"in invokeAlign")
        self.signalToAligner.emit()

    def startAligner(self):
        logging.debug("to start timer")
        self.timer.setSingleShot(True)
        self.timer.singleShot(1000, self.aligner.align)

    def stopAligner(self):
        # if self.aligner.reachedEnd
        logging.debug("stopped timer")
        # self.timer.stop()
        print(np.mean(self.aligner.durs))
        plt.scatter(self.aligner.pathFront[:,0], self.aligner.pathFront[:,1],0.1)
        plt.show()

    def plotCurrentPath(self):
        recordedChromas = np.array(self.chromatizer.chromasList)[:,:,0]
        np.save("recordedChromas", recordedChromas)
        plt.scatter(self.aligner.pathFront[:,0], self.aligner.pathFront[:,1],0.1)
        plt.show()

    def signalsandSlots(self):
        self.audioRecorder.signalToChromatizer.connect(self.chromatizer.calculate)
        self.audioRecorder.signalEnd.connect(self.closeEvent)
        self.aligner.signalToMainThread.connect(self.updateAlignment)
        # self.aligner.signalToOSCclient.connect(self.oscClient.emit)
        self.signalToAligner.connect(self.aligner.align)
        # gui 
        self.toolbar.playPause.triggered.connect(self.startStopRecording)
        self.aligner.signalEnd.connect(self.stopAligner)
        # ! remove that after testing
        self.toolbar.save.triggered.connect(self.startAligner)
        # self.toolbar.preferences.triggered.connect(self.plotCurrentPath)
        self.toolbar.preferences.triggered.connect(self.stopAligner)

        # self.oscServer.serverSignal.connect(self.oscReceiverCallback)
        self.oscServer.serverSignal.connect(self.qLabInterface.qLabResponseCallbackRouter)

        # QLabBox signals
        self.qLabGroup.clientManualMessageText.returnPressed.connect(self.qLabInterface.sentManualOscMessage)
    

    def closeEvent(self, event):
        
        self.audioRecorder.closeStream()
        self.oscServer.shutdown()
        logging.debug(f"close Event")

    def startStopRecording(self):
        # TODO communicate with audio Recorder using slots (if audio recorder is a thread)
        self.audioRecorder.startStopStream()
        if self.audioRecorder.stopped is True:
            self.toolbar.playPause.setIcon(QtGui.QIcon(self.appctxt.get_resource("svg/rec.svg")))
        else:
            self.toolbar.playPause.setIcon(QtGui.QIcon(self.appctxt.get_resource("svg/pause.svg")))

    @pyqtSlot(object)
    def updateAlignment(self, args):
        t = args[0]
        j = args[1]
        if self.aligner.i % self.plotEvery == 0:
            self.alignGroup.updatePlot(t,j)
        if j > self.lastJ:
            if j in self.cuesDict.keys():
                events = self.cuesDict[j]
                for event in events:
                    if event['type'] == 'cue':
                        self.qLabInterface.sendCueTrigger(event)
                        self.scoreGroup.cueLcd.display(event["ind"])
                    elif event['type'] == 'bar':
                        self.scoreGroup.barLcd.display(event["ind"])
        self.lastJ = j
        # spot = [{'pos': np.array(args), 'data': 1}]
        # self.alignGroup.scatter.addPoints(spot)
        # self.graphWidget.plot(line[:,0], line[:,1])

if __name__ == "__main__":
    QThread.currentThread().setObjectName('MainThread')
    logging.getLogger('matplotlib.font_manager').disabled = True
    logging.getLogger().setLevel(logging.DEBUG)
    # Uncomment below for terminal log messages
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

    appctxt = ApplicationContext()
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    mainWindow = ScoreFollower(appctxt)
    

    exit_code = app.exec_()
    sys.exit(exit_code)
