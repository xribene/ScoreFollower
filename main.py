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
# from tslearn.metrics import dtw, dtw_path
# from scipy.spatial.distance import cdist
import numpy as np
from matplotlib import pyplot as plt
###############################################
from Classes.AudioRecorder import AudioRecorder
from Classes.Chromatizer import Chromatizer
from Classes.Aligner import Aligner
# from OSCClient import OSCclient
from Classes.MenuBar import MenuBar
from Classes.ToolBar import ToolBar
from Classes.OSC import ClientOSC, ServerOSC
from Classes.GuiClasses import *
import music21.alpha
import encodings
from librosa import * 
from offline.utils_offline import Params, getChromas, getCuesDict
from offline.utils_offline import *
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
    signalToAligner = pyqtSignal()
    def __init__(self):
        super(ScoreFollower, self).__init__()
        self.setupFinished = False
        # Set the logger
        # logTextBox = QTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s -%(threadName)s -%(lineno)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)

        # initializations
        self.config = Params(resource_path("resources/config.json"))
        self.setObjectName("ScoreFollower")
        self.rms = 0.0
        self.a = 0.25

        # gui elements
        self.menuBar = MenuBar(self)
        self.toolbar = ToolBar(parent = self, config = self.config)
        self.scoreGroup = ScoreBox(self.config, self)
        self.audioGroup = AudioBox(self.config, self)
        self.alignGroup = AlignBox(self.config, self)
        self.qLabGroup = QLabBox(self.config, self)        
        mainLayout = QGridLayout(self) 
        # mainLayout.addWidget(logTextBox.widget)
        mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.toolbar, 0, 0, 10, 100, Qt.AlignCenter|Qt.AlignTop)
        mainLayout.addWidget(self.scoreGroup, 10, 0, 25, 50, Qt.AlignLeft|Qt.AlignTop)
        mainLayout.addWidget(self.audioGroup, 35, 0, 25, 50, Qt.AlignLeft|Qt.AlignTop)
        mainLayout.addWidget(self.alignGroup, 10, 50, 50, 50, Qt.AlignLeft|Qt.AlignTop)
        # verticalSpacer = QSpacerItem(100, 40, QSizePolicy.Minimum, QSizePolicy.Expanding) 
        # mainLayout.addItem(verticalSpacer, 60, 0, 40, 100, Qt.AlignCenter)
        mainLayout.addWidget(self.qLabGroup, 60, 0, 40, 100)#, Qt.AlignLeft)
        self.setLayout(mainLayout)
        self.resize(1000,1000)
        self.show()

        ## setup threads/slots
        
        
        self.setupThreads()
        
        ## set dropdown menus
        self.audioSourceName = ""
        scoreNames =  [f.parts[-1] for f in Path(resource_path(f"resources/Pieces")).iterdir() if f.is_dir()]
        self.pieceName = "Jetee"  # scoreNames[0]
        testAudios =  [f.parts[-1] for f in Path(resource_path(f"resources/Pieces/{self.pieceName}/testAudio")).iterdir() if f.is_file() and f.parts[-1]!=".DS_Store"]
        # self.audioSourceName = "microphone" # testAudios[0]

        # self.audioGroup.dropdownAudioSource.blockSignals(True)
        # self.audioGroup.dropdownAudioSource.clear()
        # self.audioGroup.dropdownAudioSource.addItems(testAudios)
        # self.audioGroup.dropdownAudioSource.addItem("microphone")
        # self.audioGroup.dropdownAudioSource.setCurrentText(self.audioSourceName)
        # self.audioGroup.dropdownAudioSource.blockSignals(False)
        self.updateAudioSourceMenu()

        self.scoreGroup.dropdownPiece.blockSignals(True)
        self.scoreGroup.dropdownPiece.addItems(scoreNames)
        self.scoreGroup.dropdownPiece.setCurrentText(self.pieceName)
        self.scoreGroup.dropdownPiece.blockSignals(False)

        self.scoreGroup.dropdownPiece.currentIndexChanged.connect(self.pieceSelectionChange)
        self.audioGroup.dropdownAudioSource.currentIndexChanged.connect(self.audioSourceSelectionChange)

        # self.pieceName = "Jetee"  # scoreNames[0]
        self.setNewPiece()
        self.setNewAudioSource()
        # self.updateAudioSourceMenu()
        # self.audioSourceName = "microphone" # testAudios[0]
        # self.audioGroup.dropdownAudioSource.setCurrentText(self.audioSourceName)
        
        ## this had to go after creating audioRecorder       
        # self.setNewAudioSource()

        self.plotEvery = self.config.plotPeriod
        self.lastJ = -1
        
        self.alignerThread = QThread()
        self.aligner = Aligner(self.referenceChromas, self.chromaBuffer,
                                n_chroma = self.config.n_chroma, 
                                c = self.config.c, 
                                maxRunCount = self.config.maxRunCount, 
                                metric = self.config.metric,
                                w = self.config.w_diag)
        self.aligner.moveToThread(self.alignerThread)
        self.alignerThread.start()

        self.signalsandSlots()

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.aligner.align)

        self.startAligner()

        # # self.testWavFile = f"{self.pieceName}FF.wav")
        # if self.config.audioInput == "mic":
        #     self.audioSource = "microphone"
        # else:
        #     self.testWavFile = resource_path(f"resources/TestAudio/{self.pieceName}/{self.config.audioInput}")
        self.setupFinished = True

        

    def pieceSelectionChange(self,i):
        print("in pieceSelectionChange")
        
        if self.pieceName != self.scoreGroup.dropdownPiece.currentText():
            self.pieceName = self.scoreGroup.dropdownPiece.currentText()
            self.setNewPiece()
            print("in pieceSelectionChange setted New Piece")
            self.updateAudioSourceMenu()
            print("in pieceSelectionChange updated AudioSourceMenu")
            self.setNewAudioSource()
            print("in pieceSelectionChange setNewAudioSource")
        if self.setupFinished:
            self.reset()

    def updateAudioSourceMenu(self):
        testAudios =  [f.parts[-1] for f in Path(resource_path(f"resources/Pieces/{self.pieceName}/testAudio")).iterdir() if f.is_file() and f.parts[-1]!=".DS_Store"]
        # testAudios2 =  [f for f in Path(f"resources/Pieces/{self.pieceName}/testAudio").iterdir()]

        # logging.debug(f"available testAudios {testAudios2}")
        self.audioGroup.dropdownAudioSource.blockSignals(True)
        self.audioGroup.dropdownAudioSource.clear()
        self.audioGroup.dropdownAudioSource.addItems(testAudios)
        self.audioSourceName = "microphone" # testAudios[0]
        self.audioGroup.dropdownAudioSource.addItem(self.audioSourceName)
        self.audioGroup.dropdownAudioSource.setCurrentText(self.audioSourceName)
        self.audioGroup.dropdownAudioSource.blockSignals(False)
        
        # self.audioSourceName = "microphone" # testAudios[0]
        # self.audioGroup.dropdownAudioSource.setCurrentText(self.audioSourceName)

    def audioSourceSelectionChange(self,):
        if self.setupFinished:
            self.reset()
        print("in audioSourceSelectionChange")
        if self.audioSourceName != self.audioGroup.dropdownAudioSource.currentText():
            print("in audioSourceSelectionChange new name")
            self.audioSourceName = self.audioGroup.dropdownAudioSource.currentText()
            print(f"in audioSourceSelectionChange new name is {self.audioSourceName}")
            self.setNewAudioSource()

    def setNewAudioSource(self):
        print(f"in setNewAudioSource")
        self.audioRecorder.closeStream()
        if self.audioSourceName == "microphone":
            self.audioRecorder.createStream(self.audioSourceName) 
            print(f"in setNewAudioSource created stream for microphone")
        else:
            print(f"self.audioSourceName is {self.audioSourceName}")
            self.audioRecorder.createStream(resource_path(f"resources/Pieces/{self.pieceName}/testAudio/{self.audioSourceName}"))
            print(f"in setNewAudioSource created stream for resources/Pieces/{self.pieceName}/testAudio/{self.audioSourceName}")


    def setNewPiece(self):
        # get the cues dict
        # self.cuesDict = getCuesDict(filePath = Path(f"{self.pieceName}.xml"), 
        #                                 sr = self.config.sr, 
        #                                 hop_length = self.config.hop_length)
        print(f"in setNewPiece")
        self.cuesDict = np.load(resource_path(f"resources/Pieces/{self.pieceName}/cuesDict_{self.pieceName}.npy"), allow_pickle=True).item()
        frames = list(self.cuesDict.keys())
        frames.sort()
        # barsList = []
        # cuesList = []
        self.bar2frameDict = {}
        self.cue2frameDict = {}
        for frame in frames:
            events = self.cuesDict[frame]
            # barsList.extend([int(event['ind']) for event in events if event['type']=='bar'])
            # cuesList.extend([int(event['name']) for event in events if event['type']=='cue'])
            for event in events:
                if event['type'] == 'bar':
                    # barsList.append(int(event['ind']))
                    self.bar2frameDict[int(event['ind'])] = frame
                elif event['type'] == 'cue':
                    # cuesList.append(int(event['name']))
                    self.cue2frameDict[int(event['name'])] = frame
                    
        # logging.debug(f'cues')
        
        # get the reference chroma vectors
        # if self.config.mode == "score" :
        #     referenceFile = resource_path(f"resources/Pieces/{self.pieceName}/{self.pieceName}.mid")
        # elif self.config.mode == "audio" : 
        #     referenceFile = resource_path(f"resources/Pieces/{self.pieceName}/{self.pieceName}.wav")
        
        # self.referenceChromas = getChromas(Path(referenceFile), 
        #                                           sr = self.config.sr,
        #                                           n_fft = self.config.n_fft, 
        #                                           hop_length = self.config.hop_length,
        #                                           window_length = self.config.window_length,
        #                                           chromaType = self.config.chromaType,
        #                                           n_chroma = self.config.n_chroma,
        #                                           norm = self.config.norm,
        #                                           normAudio = True,
        #                                           windowType = self.config.window_type,
        #                                           chromafb = None,
        #                                           magPower = self.config.magPower
        #                                           )
        self.referenceChromas = np.load(resource_path(f"resources/Pieces/{self.pieceName}/referenceAudioChromas_{self.pieceName}.npy"))
        if self.setupFinished:
            self.aligner.referenceChromas = self.referenceChromas
        
        # np.save("cuesDict.npy", self.cuesDict)
        # np.save("referenceChromas.npy", self.referenceChromas)
        # logging.debug(f"reference Chromas shape is {self.referenceChromas.shape}")
        # print(self.referenceChromas.shape)
        repeats = np.ones((self.referenceChromas.shape[0]))
        repeats[600:700] = 2
        repeats[800:900] = 2
        # repeats[1500:1700] = 2
        # self.referenceChromas = np.repeat(self.referenceChromas, list(repeats), axis=0)

        self.alignGroup.plot.setXRange(0, self.referenceChromas.shape[0]+500, padding=0)
        self.alignGroup.plot.setYRange(0, self.referenceChromas.shape[0]+500, padding=0)

    def setupThreads(self):
        self.readQueue = queue.Queue()
        self.chromaBuffer = queue.LifoQueue(1000)
        ## threads
        self.audioThread = QThread()
        self.audioRecorder = AudioRecorder(queue = self.readQueue, 
                                        #    wavfile =  self.testWavFile, # None,#
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
                                    defaultRmsThr= self.config.defaultRmsThr
                        )
        self.chromatizer.moveToThread(self.chromaThread)

        self.oscClientThread = QThread()
        self.oscClient = ClientOSC(ip = self.config.ipOut, port = self.config.portOut)
        self.oscClient.moveToThread(self.oscClientThread)

        self.oscServerThread = QThread()
        self.oscServer = ServerOSC(port = self.config.portIn)
        self.oscServer.moveToThread(self.oscServerThread)

        # self.alignerThread = QThread()
        # self.aligner = Aligner(self.referenceChromas, self.chromaBuffer,
        #                         n_chroma = self.config.n_chroma, 
        #                         c = self.config.c, 
        #                         maxRunCount = self.config.maxRunCount, 
        #                         metric = self.config.metric,
        #                         w = self.config.w_diag)
        # self.aligner.moveToThread(self.alignerThread)

        self.qLabInterface = QLabInterface(self.config, self.oscClient, self.oscClient, self.qLabGroup)

        self.audioThread.start()
        self.chromaThread.start()
        self.oscClientThread.start()
        
        self.qLabInterface.checkConnection()
        # self.oscServerThread.start()
        # self.alignerThread.start()
        logging.debug("setup threads done")


    # def invokeAlign(self):
    #     logging.debug(f"in invokeAlign")
    #     self.signalToAligner.emit()

    def startAligner(self):
        # if self.timer:
        #     logging.debug("deleting previous timer")
        #     self.timer.stop()
        #     self.timer.deleteLater()
        logging.debug("refiring singleShot timer")
        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.aligner.align)
        # self.timer.setSingleShot(True)
        self.aligner.resetActivated = False
        self.timer.start(100)

        # self.timer.setSingleShot(True)
        # self.timer.singleShot(1000, self.aligner.align)

    @pyqtSlot()
    def reset(self):
        logging.debug("in main reset")
        if self.audioRecorder.stopped is False:
            self.startStopRecording()
            QThread.msleep(1000)
        self.alignGroup.cueDisp.setText(str(0))
        self.alignGroup.barDisp.setText(str(0))
        self.audioRecorder.reset()
        self.aligner.reset()
        self.alignGroup.reset()
        # self.alignGroup.scatter.clear()
        # self.alignGroup.scatter.sigPlotChanged.emit(self.alignGroup.scatter)
        self.startAligner()
        logging.debug("finished main reset")
        # self.timer.stop()
        # print(np.mean(self.aligner.durs))

    def plotCurrentPath(self):
        recordedChromas = np.array(self.chromatizer.chromasList)[:,:,0]
        
        np.save("recordedChromas", recordedChromas)

    def signalsandSlots(self):
        self.audioRecorder.signalToChromatizer.connect(self.chromatizer.calculate)
        self.audioRecorder.signalToChromatizer.connect(self.rmsCalculator)
        # self.audioRecorder.signalEnd.connect(self.closeEvent)
        self.aligner.signalToMainThread.connect(self.updateAlignment)
        # self.aligner.signalToOSCclient.connect(self.oscClient.emit)
        # self.signalToAligner.connect(self.aligner.align)
        # gui 
        self.toolbar.playPause.triggered.connect(self.startStopRecording)
        self.aligner.signalEnd.connect(self.alignerStoppedCallback)
        # ! remove that after testing
        self.toolbar.reset.triggered.connect(self.reset)
        # self.toolbar.save.triggered.connect(self.startAligner)
        # self.toolbar.preferences.triggered.connect(self.plotCurrentPath)
        # self.toolbar.preferences.triggered.connect(self.stopAligner)

        # self.oscServer.serverSignal.connect(self.oscReceiverCallback)
        self.oscServer.serverSignalFromQlab.connect(self.qLabInterface.qLabResponseCallbackRouter)
        self.oscServer.serverSignalFromTouchDesigner.connect(self.qLabInterface.touchResponseCallbackRouter)
        self.oscServer.serverSignalFromUknownSource.connect(self.qLabInterface.unknownResponseCallbackRouter)

        # QLabBox signals
        self.qLabGroup.clientManualMessageText.returnPressed.connect(self.qLabInterface.sentManualOscMessage)
        self.qLabGroup.connectButton.clicked.connect(self.qLabInterface.checkConnection)

        # User sets starting bar signal
        self.alignGroup.barDisp.editingFinished.connect(self.processNewBarInput)
        self.alignGroup.cueDisp.editingFinished.connect(self.processNewCueInput)
        self.audioGroup.rmsThrDisp.editingFinished.connect(self.updateRmsThr)
    
    @pyqtSlot()
    def updateRmsThr(self):
        self.chromatizer.rmsThr = float(self.audioGroup.rmsThrDisp.text())
        logging.debug(f'User set RMS THR to {float(self.audioGroup.rmsThrDisp.text())}')
        
    @pyqtSlot()
    def processNewBarInput(self):
        logging.debug(f'User set bar {self.alignGroup.barDisp.text()}')
    @pyqtSlot()
    def processNewCueInput(self):
        logging.debug(f'User set cue {self.alignGroup.cueDisp.text()}')   
    @pyqtSlot(object)
    def rmsCalculator(self, audioFrame):
        y = audioFrame.astype('float32') / 32768.0
        power = np.mean(np.abs(y) ** 2, axis=0, keepdims=True)
        new_rms = np.sqrt(power)
        self.rms = self.a * new_rms[0] + (1 - self.a) * self.rms
        self.audioGroup.rmsDisp.setText(f"{self.rms*10:.2f}")
        # logging.debug(f'rms value is {self.rms*10}')
        

    @pyqtSlot()
    def alignerStoppedCallback(self):
        print(f"IN SIGNAL END FROM ALIGNER ABOUT TO STOP RECORDING")
        self.startStopRecording()
        # self.reset()

    def closeEvent(self, event):
        
        self.audioRecorder.closeEverything()
        self.oscServer.shutdown()
        logging.debug(f"close Event")

    @pyqtSlot()
    def startStopRecording(self):
        # TODO communicate with audio Recorder using slots (if audio recorder is a thread)
        logging.debug(f"before {self.audioRecorder.stopped}")
        self.audioRecorder.startStopStream()
        logging.debug(f"after {self.audioRecorder.stopped}")
        if self.audioRecorder.stopped is True:
            self.aligner.recording = False
            self.toolbar.playPause.setIcon(QtGui.QIcon(resource_path("resources/svg/rec.svg")))
        else:
            self.aligner.recording = True
            self.toolbar.playPause.setIcon(QtGui.QIcon(resource_path("resources/svg/pause.svg")))
        logging.debug(f"set aligner.recording to {self.aligner.recording}")

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
                        self.alignGroup.cueDisp.setText(str(event["name"]))
                    elif event['type'] == 'bar':
                        self.qLabInterface.sendBarTrigger(event)
                        self.alignGroup.barDisp.setText(str(event["ind"]))
        self.lastJ = j
        # spot = [{'pos': np.array(args), 'data': 1}]
        # self.alignGroup.scatter.addPoints(spot)
        # self.graphWidget.plot(line[:,0], line[:,1])

if __name__ == "__main__":
    QThread.currentThread().setObjectName('MainThread')
    logging.getLogger().setLevel(logging.DEBUG)
    # Uncomment below for terminal log messages
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

    styleSheet = resource_path("resources/styleSheet.css")
    app = QApplication(sys.argv)
    with open(styleSheet,"r") as fh:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + fh.read())
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    mainWindow = ScoreFollower()
    exit_code = app.exec_()
    sys.exit(exit_code)