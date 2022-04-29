###########import statements#################
##standard PyQt imports (thanks christos!)###
from syslog import LOG_DAEMON
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
# from offline.utils_offline import Params, getChromas, getCuesDict
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
        mainLayout.addWidget(self.scoreGroup, 10, 0, 25, 50)#, Qt.AlignLeft|Qt.AlignTop)
        mainLayout.addWidget(self.audioGroup, 35, 0, 25, 50)#, Qt.AlignLeft|Qt.AlignTop)
        mainLayout.addWidget(self.alignGroup, 10, 50, 50, 50)#, Qt.AlignLeft|Qt.AlignTop)
        # verticalSpacer = QSpacerItem(100, 40, QSizePolicy.Minimum, QSizePolicy.Expanding) 
        # mainLayout.addItem(verticalSpacer, 60, 0, 40, 100, Qt.AlignCenter)
        mainLayout.addWidget(self.qLabGroup, 60, 0, 40, 100)#, Qt.AlignLeft)
        self.setLayout(mainLayout)
        self.resize(1000,1000)
        self.show()

        ## setup threads/slots
        
        
        self.setupThreads()
        
        ## new dropdowns
        

        self.scoreGroup.dropdownPiece.currentIndexChanged.connect(self.changedPiece)
        self.scoreGroup.dropdownSection.currentIndexChanged.connect(self.changedSection)
        self.audioGroup.dropdownAudioInput.currentIndexChanged.connect(self.changedAudioInput)
        self.audioGroup.dropdownMode.currentIndexChanged.connect(self.changedMode)
        self.audioGroup.dropdownAudioOutput.currentIndexChanged.connect(self.changedAudioOutput)

        self.updateModeItems()
        
        self.updateAudioInputItems()
        self.updatePieceItems()
        self.updateAudioOutputItems()
        self.pieceName = "Jetee" # perito
        # self.changedPiece(0) # isws perito

        ## aligner
        self.plotEvery = self.config.plotPeriod
        self.lastJ = -1
        
        self.alignerThread = QThread()
        # self.referenceChromas = np.zeros((12,2000))
        self.aligner = Aligner(self.referenceChromas, self.chromaBuffer,
                                n_chroma = self.config.n_chroma, 
                                c = self.config.c, 
                                maxRunCount = self.config.maxRunCount, 
                                metric = self.config.metric,
                                power = self.config.power,
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

    def updateModeItems(self):
        modeItems = ['Microphone', 'Wav File']
        self.mode = modeItems[0]
        self.audioGroup.dropdownMode.blockSignals(True)
        self.audioGroup.dropdownMode.addItems(modeItems)
        self.audioGroup.dropdownMode.setCurrentIndex(-1)
        self.audioGroup.dropdownMode.setCurrentIndex(self.audioGroup.dropdownMode.findText(self.mode))
        self.audioGroup.dropdownMode.blockSignals(False)

    def changedMode(self, i):
        print(f"in changedMode")
        if self.mode != self.audioGroup.dropdownMode.currentText():
            self.mode = self.audioGroup.dropdownMode.currentText()
            print(f"mode changed to {self.mode} / heading to update the AudioInputItems")
            self.updateAudioInputItems()

    def updatePieceItems(self):
        print("in UpdatePieceItems")
        self.pieceNames =  [f.parts[-1] for f in Path(resource_path(f"resources/Pieces")).iterdir() if f.is_dir()]
        self.pieceName = "Jetee"  # scoreNames[0]
        self.scoreGroup.dropdownPiece.blockSignals(True)
        self.scoreGroup.dropdownPiece.clear()
        self.scoreGroup.dropdownPiece.addItems(self.pieceNames)
        self.scoreGroup.dropdownPiece.setCurrentIndex(-1)
        self.scoreGroup.dropdownPiece.blockSignals(False)
        self.scoreGroup.dropdownPiece.setCurrentIndex(self.scoreGroup.dropdownPiece.findText(self.pieceName)) # TODO maybe allow to send signal here

    def changedPiece(self, i):
        print(f"in ChangedPiece {i}")
        # if self.pieceName != self.scoreGroup.dropdownPiece.currentText():
        self.pieceName = self.scoreGroup.dropdownPiece.currentText()
        self.updateSectionItems()
        
    def updateSectionItems(self):
        print(f"in updateSectionItems")
        self.sectionNames =  [f.parts[-1] for f in Path(resource_path(f"resources/Pieces/{self.pieceName}")).iterdir() if f.is_dir()]
        self.sectionNames.sort(key = lambda x: int(x.split("_")[0]))
        self.sectionName = self.sectionNames[0]
        print(f"section name is {self.sectionName}")
        self.scoreGroup.dropdownSection.blockSignals(True)
        self.scoreGroup.dropdownSection.clear()
        self.scoreGroup.dropdownSection.addItems(self.sectionNames)
        self.scoreGroup.dropdownSection.setCurrentIndex(-1)
        self.scoreGroup.dropdownSection.blockSignals(False)
        print(f"before")
        # self.scoreGroup.dropdownSection.setCurrentText("aderfe") # TODO maybe allow to send signal here
        self.scoreGroup.dropdownSection.setCurrentIndex(self.scoreGroup.dropdownSection.findText(self.sectionName))
        print(f"done")

    def changedSection(self, i):
        print("in changedSection")
        self.sectionName = self.scoreGroup.dropdownSection.currentText()
        self.updateReferenceData()
        if self.audioGroup.dropdownMode.currentText() == 'Wav File':
            self.updateAudioInputItems()
        elif self.audioGroup.dropdownMode.currentText() == 'Microphone':
            if self.setupFinished:
                self.reset()
    
    def updateAudioInputItems(self):
        print(f"in updateAudioInputItems")
        if self.mode == 'Microphone':
            audioInputNames = [dev['name'] for dev in self.audioRecorder.inputDevices]
            self.audioInputName = self.audioRecorder.defaultInputInfo['name']
            print(f"audioInputName became {self.audioInputName}")
            self.audioGroup.dropdownAudioInput.blockSignals(True)
            self.audioGroup.dropdownAudioInput.clear()
            self.audioGroup.dropdownAudioInput.addItems(audioInputNames)
            self.audioGroup.dropdownAudioInput.setCurrentIndex(-1)
            self.audioGroup.dropdownAudioInput.blockSignals(False)
            self.audioGroup.dropdownAudioInput.setCurrentIndex(self.audioGroup.dropdownAudioInput.findText(self.audioInputName)) # maybe not
        elif self.mode == 'Wav File':
            testAudios =  [f.parts[-1] for f in Path(resource_path(f"resources/Pieces/{self.pieceName}/{self.sectionName}/testAudio")).iterdir() if f.is_file() and f.parts[-1]!=".DS_Store"]
            self.audioInputName = testAudios[0]
            print(f"audioInputName became {self.audioInputName}")
            self.audioGroup.dropdownAudioInput.blockSignals(True)
            self.audioGroup.dropdownAudioInput.clear()
            self.audioGroup.dropdownAudioInput.addItems(testAudios)
            self.audioGroup.dropdownAudioInput.setCurrentIndex(-1)
            
            self.audioGroup.dropdownAudioInput.blockSignals(False)
            self.audioGroup.dropdownAudioInput.setCurrentIndex(self.audioGroup.dropdownAudioInput.findText(self.audioInputName))

    def changedAudioInput(self, i):
        print("in changedAudioInput")
        if self.setupFinished:
            self.reset()
        # if self.audioInputName != self.audioGroup.dropdownAudioInput.currentText():
        print("audioInputName changed indeed")
        self.audioInputName = self.audioGroup.dropdownAudioInput.currentText()
        # print(f"in audioSourceSelectionChange new name is {self.audioSourceName}")
        # self.audioRecorder.closeStream()
        if self.mode == 'Microphone':
            self.audioRecorder.input_device_index = [dev['index'] for dev in self.audioRecorder.inputDevices if dev['name'] == self.audioInputName][0]
            # self.audioRecorder.output_device_index = [dev['index'] for dev in self.audioRecorder.outputDevices if dev['name'] == self.audioOutputName]
            self.audioRecorder.createStream(self.mode) 
            print(f"in changedAudioInput created stream for Microphone")
        else:
            self.audioRecorder.createStream(resource_path(f"resources/Pieces/{self.pieceName}/{self.sectionName}/testAudio/{self.audioInputName}"))
            print(f"in changedAudioInput created stream for resources/Pieces/{self.pieceName}/{self.sectionName}/testAudio/{self.audioInputName}")
    
    def updateInputChannels(self):
        # ! that's not thread safe
        chans = [int(c)-1 for c in self.audioGroup.channelDisp.text().split(';')]
        if chans == [-1]:
            self.audioRecorder.inputChannels = list(range(self.audioRecorder.actualMaxInputChannels))  
        else:
            self.audioRecorder.inputChannels = chans
        logging.debug(f'inputChannels are {self.audioRecorder.inputChannels}')
        
        # self.changedAudioInput(0)

    def updateAudioOutputItems(self):
        print(f"in updateAudioOutputItems")
        audioOutputNames = [dev['name'] for dev in self.audioRecorder.outputDevices]
        self.audioOutputName = self.audioRecorder.defaultOutputInfo['name']
        print(f"audioOutputName became {self.audioOutputName}")
        self.audioGroup.dropdownAudioOutput.blockSignals(True)
        self.audioGroup.dropdownAudioOutput.clear()
        self.audioGroup.dropdownAudioOutput.addItems(audioOutputNames)
        self.audioGroup.dropdownAudioOutput.setCurrentIndex(-1)
        self.audioGroup.dropdownAudioOutput.blockSignals(False)
        self.audioGroup.dropdownAudioOutput.setCurrentIndex(self.audioGroup.dropdownAudioOutput.findText(self.audioOutputName)) # maybe not
            
    def changedAudioOutput(self, i):
        print("in changedAudioOutput")
        if self.setupFinished:
            self.reset()
        # if self.audioInputName != self.audioGroup.dropdownAudioInput.currentText():
        self.audioOutputName = self.audioGroup.dropdownAudioOutput.currentText()
        # print(f"in audioSourceSelectionChange new name is {self.audioSourceName}")
        # self.audioRecorder.closeStream()
        self.audioRecorder.output_device_index = [dev['index'] for dev in self.audioRecorder.outputDevices if dev['name'] == self.audioOutputName][0]
        # self.audioRecorder.output_device_index = [dev['index'] for dev in self.audioRecorder.outputDevices if dev['name'] == self.audioOutputName]
        if self.mode == 'Wav File':
            self.audioRecorder.createStream(self.mode) 
        print(f"in changedAudioOutput created stream for wav file")

    def updateReferenceData(self):
        # get the cues dict
        # self.cuesDict = getCuesDict(filePath = Path(f"{self.pieceName}.xml"), 
        #                                 sr = self.config.sr, 
        #                                 hop_length = self.config.hop_length)
        print(f"in updateReferenceData")
        sectionNameNoNumber = "".join(self.sectionName.split('_')[1:])
        self.cuesDict = np.load(resource_path(f"resources/Pieces/{self.pieceName}/{self.sectionName}/cuesDict_{self.pieceName}_{sectionNameNoNumber}.npy"), allow_pickle=True).item()
        frames = list(self.cuesDict.keys())
        frames.sort()
        self.barFrameList = []
        self.cueFrameList = []
        self.barList = []
        self.cueList = []
        self.bar2frameDict = {}
        self.cue2frameDict = {}
        self.frame2barDict = {}
        self.frame2cueDict = {}
        for frame in frames:
            events = self.cuesDict[frame]
            # barsList.extend([int(event['ind']) for event in events if event['type']=='bar'])
            # cuesList.extend([int(event['name']) for event in events if event['type']=='cue'])
            for event in events:
                if event['type'] == 'bar':
                    self.barFrameList.append(frame)
                    self.bar2frameDict[int(event['ind'])] = frame
                    self.frame2barDict[frame] = int(event['ind'])
                    self.barList.append(int(event['ind']))
                    
                elif event['type'] == 'cue':
                    self.cueFrameList.append(frame)
                    self.cue2frameDict[int(event['name'])] = frame
                    self.frame2cueDict[frame] = int(event['name'])
                    self.cueList.append(int(event['name']))
        self.lastStartingCue = min(self.cueList)
        self.lastStartingBar = min(self.barList)
        self.lastStartingFrame = 0
        self.currentCue = self.lastStartingCue
        self.currentBar = self.lastStartingBar
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
        self.referenceChromas = np.load(resource_path(f"resources/Pieces/{self.pieceName}/{self.sectionName}/referenceAudioChromas_{self.pieceName}_{sectionNameNoNumber}.npy"))
        if self.setupFinished:
            self.aligner.referenceChromas = self.referenceChromas
        
        # np.save("cuesDict.npy", self.cuesDict)
        # np.save("referenceChromas.npy", self.referenceChromas)
        # logging.debug(f"reference Chromas shape is {self.referenceChromas.shape}")
        # print(self.referenceChromas.shape)
        # repeats = np.ones((self.referenceChromas.shape[0]))
        # repeats[600:700] = 2
        # repeats[800:900] = 2
        # repeats[1500:1700] = 2
        # self.referenceChromas = np.repeat(self.referenceChromas, list(repeats), axis=0)

        self.alignGroup.plot.setXRange(0, self.referenceChromas.shape[0]+500, padding=0)
        self.alignGroup.plot.setYRange(0, self.referenceChromas.shape[0]+500, padding=0)

        # print(self.frame2cueDict)
        # print(self.cues)
        ax = self.alignGroup.plot.getAxis('left')
        ax.setTicks([[(v, str(self.frame2barDict[v])) for v in self.barFrameList ] ]) 
        ax.setGrid(255*0.2)

        ax2 = self.alignGroup.plot.getAxis('right')
        ax2.setTicks([[(v, str(self.frame2cueDict[v])) for v in self.cueFrameList ] ]) # , [(v, str(v)) for v in cueFrameList ]

        # send feedback to TD
        self.qLabInterface.sendFeedback("piece", self.pieceName)
        self.qLabInterface.sendFeedback("section", self.sectionName)

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

        self.qLabInterface = QLabInterface(self.config, self.oscClient, 
                                            self.oscClient, self.qLabGroup, 
                                            main = self)

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
    def stopButtonCallback(self):
        self.reset()
        self.alignGroup.barDisp.setText(str(self.lastStartingBar))

        # frame = self.bar2frameDict[int(self.lastStartingBar)]
        self.aligner.j_todo = self.lastStartingFrame
        self.aligner.j_todo_flag = True

        self.alignGroup.cueDisp.setText(str(self.lastStartingCue))
        self.alignGroup.barDisp.setText(str(self.lastStartingBar))
        self.qLabInterface.sendFeedback('stop')
        # frame = self.cue2frameDict[int(self.lastStartingBar)]
        # self.aligner.j_todo = frame
        # self.aligner.j_todo_flag = True

    @pyqtSlot()
    def reset(self):
        logging.debug("in main reset")
        if self.audioRecorder.stopped is False:
            self.startStopRecording()
            QThread.msleep(1000)
        # if isStop == False:
        self.alignGroup.cueDisp.setText(str(self.cueList[0]))
        self.alignGroup.barDisp.setText(str(self.barList[0]))
        
        self.audioRecorder.reset()
        self.aligner.reset()
        print("out of aligner")
        self.alignGroup.reset()
        # self.alignGroup.scatter.clear()
        # self.alignGroup.scatter.sigPlotChanged.emit(self.alignGroup.scatter)
        print("before starting aligner")
        self.startAligner()
        logging.debug("finished main reset")
        self.qLabInterface.sendFeedback('reset')
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
        self.toolbar.stop.triggered.connect(self.stopButtonCallback)
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
        self.alignGroup.barDisp.returnPressed.connect(self.processNewBarInput)
        self.alignGroup.cueDisp.returnPressed.connect(self.processNewCueInput)
        self.audioGroup.rmsThrDisp.returnPressed.connect(self.updateRmsThr)
        self.audioGroup.channelDisp.returnPressed.connect(self.updateInputChannels)

        # 
        self.qLabInterface.signalNewBarOsc.connect(self.processNewBarInputOSC)
        self.qLabInterface.signalNewCueOsc.connect(self.processNewCueInputOSC)
    
    @pyqtSlot()
    def updateRmsThr(self):
        self.chromatizer.rmsThr = float(self.audioGroup.rmsThrDisp.text())
        logging.debug(f'User set RMS THR to {float(self.audioGroup.rmsThrDisp.text())}')

    # @pyqtSlot()
    # def processNewBarInput(self, ):
    #     logging.debug(f'User set bar {self.alignGroup.barDisp.text()}')
    #     # self.aligner.setStartingScoreFrame(self.bar2frameDict[int(self.alignGroup.barDisp.text())])
    #     frame = self.bar2frameDict[int(self.alignGroup.barDisp.text())]
    #     self.aligner.j_todo = frame
    #     self.aligner.j_todo_flag = True

    @pyqtSlot()
    def processNewBarInput(self):
        newBar = self.alignGroup.barDisp.text()
        
        logging.debug(f'User set cue {newBar}')  
        try:
            frame = self.bar2frameDict[int(newBar)]
        except:
            logging.debug(f'{newBar} is not a valid bar number')
            return
        self.currentBar = int(newBar) 
        self.aligner.j_todo = frame
        self.aligner.j_todo_flag = True
        self.qLabInterface.sendFeedback('bar', int(newBar))
        # if is playing then don't update lastStartedBar
        if self.audioRecorder.stopped == True:
            logging.debug(f'updating lastStartingBar to {newBar}')
            
            self.lastStartingBar = int(newBar)
            self.lastStartingFrame = frame
            # self.lastStartingCue = self.frame2cueDict[frame]
            

    @pyqtSlot()
    def processNewCueInput(self):
        newCue = self.alignGroup.cueDisp.text()
        
        logging.debug(f'User set cue {newCue}')
        try:
            frame = self.bar2frameDict[int(newCue)]
        except:
            logging.debug(f'{newCue} is not a valid cue number')
            return
        self.currentCue = int(newCue)
        frame = self.cue2frameDict[int(newCue)]
        self.aligner.j_todo = frame
        self.aligner.j_todo_flag = True
        self.qLabInterface.sendFeedback('cue', int(newCue))
        # if is playing then don't update lastStartedBar
        if self.audioRecorder.stopped == True:
            logging.debug(f'updating lastStartingCue to {newCue}')
            self.lastStartingCue = int(newCue)
            self.lastStartingBar = self.frame2barDict[frame]
            self.lastStartingFrame = frame

    @pyqtSlot(str)
    def processNewBarInputOSC(self, bar):
        logging.debug(f'User OSC set bar {bar}')
        try:
            frame = self.bar2frameDict[int(bar)]
        except:
            logging.debug(f'{bar} is not a valid bar number')
            return
        self.currentBar = int(bar)
        self.alignGroup.barDisp.setText(bar)
        frame = self.bar2frameDict[int(bar)]
        self.aligner.j_todo = frame
        self.aligner.j_todo_flag = True
        self.qLabInterface.sendFeedback('bar', int(bar))
        # if is playing then don't update lastStartedBar
        if self.aligner.recording == False:
            logging.debug(f'updating lastStartingBar to {bar}')
            
            self.lastStartingBar = int(bar)
            self.lastStartingCue = self.frame2cueDict[frame]
            self.lastStartingFrame = frame

    @pyqtSlot(str)
    def processNewCueInputOSC(self, cue):
        logging.debug(f'User OSC set cue {cue}')  
        try:
            frame = self.bar2frameDict[int(cue)]
        except:
            logging.debug(f'{cue} is not a valid cue number')
            return
        self.currentCue = int(cue)
        self.alignGroup.cueDisp.setText(cue)
        frame = self.cue2frameDict[int(cue)]
        self.aligner.j_todo = frame
        self.aligner.j_todo_flag = True
        self.qLabInterface.sendFeedback('cue', int(cue))
        if self.aligner.recording == False:
            logging.debug(f'updating lastStartingCue to {cue}')
            self.lastStartingCue = int(cue)
            self.lastStartingBar = self.frame2barDict[frame]
            self.lastStartingFrame = frame

    def nextBar(self):
        logging.debug(f'User OSC Next bar')
        barInd = self.barList.index(self.currentBar)
        if barInd < len(self.barList)-1:
            nextBar = self.barList[barInd+1]
            self.processNewBarInputOSC(str(nextBar))
        else:
            logging.debug(f'bar out of bounds')
    def prevBar(self):
        logging.debug(f'User OSC Prev bar')
        barInd = self.barList.index(self.currentBar)
        if barInd > 0:
            prevBar = self.barList[barInd-1]
            self.processNewBarInputOSC(str(prevBar))
        else:
            logging.debug(f'bar out of bounds')
    def nextCue(self):
        logging.debug(f'User OSC Next cue')
        cueInd = self.cueList.index(self.currentCue)
        if cueInd < len(self.cueList)-1:
            nextCue = self.cueList[cueInd+1]
            self.processNewCueInputOSC(str(nextCue))
        else:
            logging.debug(f'cue out of bounds')
    def prevCue(self):
        logging.debug(f'User OSC Prev cue')
        cueInd = self.cueList.index(self.currentCue)
        if cueInd > 0:
            prevCue = self.cueList[cueInd-1]
            self.processNewCueInputOSC(str(prevCue))
        else:
            logging.debug(f'cue out of bounds')

              

    

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
    def startStopRecording(self, feedback = False):
        # TODO communicate with audio Recorder using slots (if audio recorder is a thread)
        logging.debug(f"before {self.audioRecorder.stopped}")
        self.audioRecorder.startStopStream()
        logging.debug(f"after {self.audioRecorder.stopped}")
        if self.audioRecorder.stopped is True:
            self.qLabInterface.sendStopTrigger()
            if feedback is True:
                self.qLabInterface.sendFeedback('pause')
            self.aligner.recording = False
            self.toolbar.playPause.setIcon(QtGui.QIcon(resource_path("resources/svg/rec.svg")))
            logging.debug(f"{len(self.aligner.dursJ)} J iterations with mean running time = {np.mean(self.aligner.dursJ)}")
            logging.debug(f"{len(self.aligner.dursT)} T iterations with mean running time = {np.mean(self.aligner.dursT)}")
        else:
            self.qLabInterface.sendStartTrigger()
            if feedback is True:
                self.qLabInterface.sendFeedback('start')
            self.aligner.recording = True
            self.toolbar.playPause.setIcon(QtGui.QIcon(resource_path("resources/svg/pause.svg")))
        logging.debug(f"set aligner.recording to {self.aligner.recording}")

    @pyqtSlot()
    def startRecording(self, feedback = False):
        if self.audioRecorder.stopped is True:
            self.audioRecorder.startStopStream()
            self.qLabInterface.sendStartTrigger()
            if feedback is True:
                self.qLabInterface.sendFeedback('start')
            self.aligner.recording = True
            self.toolbar.playPause.setIcon(QtGui.QIcon(resource_path("resources/svg/pause.svg")))

            logging.debug(f"set aligner.recording to {self.aligner.recording}")
    @pyqtSlot()
    def stopRecording(self, feedback = False):
        if self.audioRecorder.stopped is False:
            self.audioRecorder.startStopStream()
            self.qLabInterface.sendStopTrigger()
            if feedback is True:
                self.qLabInterface.sendFeedback('pause')
            self.aligner.recording = False
            self.toolbar.playPause.setIcon(QtGui.QIcon(resource_path("resources/svg/rec.svg")))
            logging.debug(f"set aligner.recording to {self.aligner.recording}")

    @pyqtSlot(object)
    def updateAlignment(self, args):
        t = args[0]
        j = args[1]
        # self.audioGroup.tuningDisp.setText(str(self.chromatizer.tuning))
        if self.aligner.i % self.plotEvery == 0:
            self.alignGroup.updatePlot(t,j)
        if j > self.lastJ:
            if j in self.cuesDict.keys():
                events = self.cuesDict[j]
                for event in events:
                    if event['type'] == 'cue':
                        self.qLabInterface.sendCueTrigger(event)
                        self.alignGroup.cueDisp.setText(str(event["name"]))
                        self.currentCue = int(event['name'])
                    elif event['type'] == 'bar':
                        self.qLabInterface.sendBarTrigger(event)
                        self.alignGroup.barDisp.setText(str(event["ind"]))
                        self.currentBar = int(event['ind'])
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