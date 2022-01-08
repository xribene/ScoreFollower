###########import statements#################
##standard PyQt imports (thanks christos!)###
from PyQt5 import QtGui, QtCore, QtSvg
from PyQt5.QtWidgets import (QGridLayout, QWidget, QApplication, QPlainTextEdit, QMainWindow,
                            QGridLayout, QStyleFactory)
from PyQt5.QtCore import (pyqtSlot, QThread, Qt)
from PyQt5.QtGui import (QPen, QTransform)
from PyQt5.QtSvg import QGraphicsSvgItem
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
# from OnlineDTW import OnlineDTW
# from OSCClient import OSCclient
from MenuBar import MenuBar
from ToolBar import ToolBar
from OSC import ClientOSC, ServerOSC
from utils import Params, getReferenceChromas
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

class ScoreFollower(QWidget):

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

        # layout
        s = QStyleFactory.create('Fusion')
        self.setStyle(s)
        mainLayout = QGridLayout(self) 
        # mainLayout.addWidget(logTextBox.widget)
        mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.toolbar, 0,0,3,1, Qt.AlignLeft|Qt.AlignTop)

        self.setLayout(mainLayout)
        self.resize(400,400)
        self.show()

        
        # TODO a window for the user to choose which score to use
        self.pieceName = "wtq"
        # get the reference chroma vectors
        
        if self.config.mode == "score" :
            referenceFile = appctxt.get_resource(f"{self.pieceName}.xml")
        elif self.config.mode == "audio" : 
            referenceFile = appctxt.get_resource(f"{self.pieceName}.wav")
        
        self.referenceChromas = getReferenceChromas(Path(referenceFile), 
                                                  sr = self.config.sr,
                                                  n_fft = self.config.n_fft, 
                                                  hop_length = self.config.hop_length,
                                                  chromaType = self.config.chromaType
                                                  )

        self.testWavFile = appctxt.get_resource(f"{self.pieceName}.wav")

        self.setupThreads()
        self.signalsandSlots()

    def setupThreads(self):
        self.readQueue = queue.Queue()
        self.chromaQueue = queue.Queue()
        ## threads
        self.audioThread = QThread()
        self.audioRecorder = AudioRecorder(queue = self.readQueue, 
                                           wavfile = self.testWavFile,
                                           rate = self.config.sr,
                                           # ! be careful, audio streams chunk is 
                                           # ! equal to the hop_length
                                           chunk = self.config.hop_length,
                                           input_device_index=self.config.input_device_index)
        # ? Not sure if we need a separate thread for the audio stream. 
        # ? pyaudio already calls the callback on a different thread.
        self.audioRecorder.moveToThread(self.audioThread)

        self.chromaThread = QThread()
        self.chromatizer = Chromatizer(inputqueue = self.readQueue,
                                    outputqueue = self.chromaQueue,
                                    rate = self.config.sr,
                                    hop_length = self.config.hop_length,
                                    n_fft = self.config.n_fft,
                                    chromaType = self.config.chromaType)
        self.chromatizer.moveToThread(self.chromaThread)

        self.oscClientThread = QThread()
        self.oscClient = ClientOSC()
        self.oscClient.moveToThread(self.oscClientThread)

        self.oscServerThread = QThread()
        self.oscServer = ServerOSC()
        self.oscServer.moveToThread(self.oscServerThread)

        # self.dtwThread = QThread()
        # self.onlineDTW = OnlineDTW(self.scorechroma.chroma, self.chromaQueue, cues)
        # self.onlineDTW.moveToThread(self.dtwThread)

        self.audioThread.start()
        self.chromaThread.start()
        self.oscClientThread.start()
        # self.oscServerThread.start()
        # self.dtwThread.start()
        logging.debug("setup threads done")

    def signalsandSlots(self):
        self.audioRecorder.signalToChromatizer.connect(self.chromatizer.calculate)
        self.audioRecorder.signalEnd.connect(self.closeEvent)
        # self.chromatizer.signalToOnlineDTW.connect(self.onlineDTW.align)
        # self.onlineDTW.signalToGUIThread.connect(self.plotter)
        # self.onlineDTW.signalToOSCclient.connect(self.oscclient.emit)

        # gui 
        self.toolbar.playPause.triggered.connect(self.startStopRecording)
        # ! remove that after testing
        self.toolbar.save.triggered.connect(self.oscClient.emit)
        self.oscServer.serverSignal.connect(self.oscReceiverCallback)

    def closeEvent(self, event):
        # recordedChromas = np.array(self.chromatizer.chromasList)[:,:,0]
        # np.save("recordedChromas", recordedChromas)
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
    def oscReceiverCallback(self, args):
        logging.debug(f"main osc receiver got {args}")

    # @pyqtSlot(object)
    # def plotter(self, line):
    #     line.sort(axis = 0)
    #     self.curve.setData(line)

if __name__ == "__main__":
    QThread.currentThread().setObjectName('MainThread')
    logging.getLogger().setLevel(logging.DEBUG)
    # Uncomment below for terminal log messages
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

    appctxt = ApplicationContext()
    app = QApplication(sys.argv)
    mainWindow = ScoreFollower(appctxt)
    exit_code = app.exec_()
    sys.exit(exit_code)
