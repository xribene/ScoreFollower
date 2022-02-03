###########import statements#################
##standard PyQt imports (thanks christos!)###
from PyQt5 import QtGui, QtCore, QtSvg
from PyQt5.QtWidgets import (QGridLayout, QWidget, QApplication, QPlainTextEdit, QMainWindow,
                            QGridLayout, QStyleFactory, QTextEdit)
from PyQt5.QtCore import (pyqtSlot, QThread, Qt, pyqtSignal)
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
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
from offline.utils_offline import Params, getChromas
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
        # self.graphWidget = pg.PlotWidget()
        self.textEdit = QTextEdit()

        self.win = pg.GraphicsWindow()
        self.plot = self.win.addPlot(title = "Minimum Cost Path",
                                  labels = {
                                  'bottom':"Score Frame (V(t))",
                                  'left':"Audio Frame (V(j))"},
                                   backround = "white")
        # self.curve = self.p.plot(pen="r", background="w")
        # self.plot = pg.plot()
        self.scatter = pg.ScatterPlotItem(
            size=10, brush=pg.mkBrush(255, 255, 255, 120))
        self.plot.addItem(self.scatter)
        # layout
        s = QStyleFactory.create('Fusion')
        self.setStyle(s)
        mainLayout = QGridLayout(self) 
        # mainLayout.addWidget(logTextBox.widget)
        mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.toolbar)#, 0,0,3,1, Qt.AlignLeft|Qt.AlignTop)
        mainLayout.addWidget(self.win)
        mainLayout.addWidget(self.textEdit)

        self.cursor = QtGui.QTextCursor(self.textEdit.document())
        self.cursor.setPosition(0)
        self.textEdit.setTextCursor(self.cursor)

        # self.textEdit.setHtml("<font color='red' size='6'><red>Hello PyQt5!\nHello</font>")
        # self.textEdit.insertPlainText('your text here\n')

        # self.cursor.setPosition(0)
        # self.textEdit.insertHtml("<font color='red' size='3'><red>Hello PyQt5!\nHello</font>")
        # mainLayout.addWidget(self.plot)

        self.setLayout(mainLayout)
        self.resize(1000,1000)
        self.show()

        
        # TODO a window for the user to choose which score to use
        self.pieceName = "jetee"
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
        repeats = list(np.ones((self.referenceChromas.shape[0])))
        # for i in range(100,150):
        #     repeats[i] += 1
 
        for i in range(600,800):
            repeats[i] += 1
        for i in range(1500,1700):
            repeats[i] += 1
        self.referenceChromas = np.repeat(self.referenceChromas, repeats, axis=0)
        # self.testWavFile = appctxt.get_resource(f"{self.pieceName}FF.wav")
        self.testWavFile = appctxt.get_resource(f"recordedJetee.wav")

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
        self.oscClient = ClientOSC(port = 53000)
        self.oscClient.moveToThread(self.oscClientThread)

        self.oscServerThread = QThread()
        self.oscServer = ServerOSC(port = 53001)
        self.oscServer.moveToThread(self.oscServerThread)

        self.alignerThread = QThread()
        self.aligner = Aligner(self.referenceChromas, self.chromaBuffer,
                                n_chroma = self.config.n_chroma, 
                                c = self.config.c, 
                                maxRunCount = self.config.maxRunCount, 
                                metric = self.config.metric,
                                w = self.config.w_diag)
        self.aligner.moveToThread(self.alignerThread)

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
        # self.timer.timeout.connect(self.invokeAlign)

        # self.timer.start(int(1000*self.config.hop_length / self.config.sr / 2))
        # self.timer.start(5)
        self.timer.singleShot(1000, self.aligner.align)
        #self.timer.start(100)
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
        self.aligner.signalToGUIThread.connect(self.plotPath)
        self.aligner.signalToOSCclient.connect(self.oscClient.emit)
        self.signalToAligner.connect(self.aligner.align)
        # gui 
        self.toolbar.playPause.triggered.connect(self.startStopRecording)
        self.aligner.signalEnd.connect(self.stopAligner)
        # ! remove that after testing
        self.toolbar.save.triggered.connect(self.startAligner)
        # self.toolbar.preferences.triggered.connect(self.plotCurrentPath)
        self.toolbar.preferences.triggered.connect(self.stopAligner)

        self.oscServer.serverSignal.connect(self.oscReceiverCallback)

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
    def oscReceiverCallback(self, args):
        logging.debug(f"main osc receiver got {args}")
        self.cursor.setPosition(0)
        self.textEdit.setTextCursor(self.cursor)
        self.textEdit.insertHtml(f"<font color='green' size='6'><red>/cue <b>{args[0]}</b></font><br>")

    @pyqtSlot(object)
    def plotPath(self, args):
        # line = args[0]
        # logging.debug(f"in plotPath j={args[1]}")
        # self.curve.setData(line)

        # spots = [{'pos': pos[:, i], 'data': 1}
        #          for i in range(n)] + [{'pos': [0, 0], 'data': 1}]
        spot = [{'pos': np.array(args), 'data': 1}]
        # adding points to the scatter plot
        self.scatter.addPoints(spot)
        # self.graphWidget.plot(line[:,0], line[:,1])

if __name__ == "__main__":
    QThread.currentThread().setObjectName('MainThread')
    logging.getLogger('matplotlib.font_manager').disabled = True
    logging.getLogger().setLevel(logging.DEBUG)
    # Uncomment below for terminal log messages
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

    appctxt = ApplicationContext()
    app = QApplication(sys.argv)
    mainWindow = ScoreFollower(appctxt)
    exit_code = app.exec_()
    sys.exit(exit_code)
