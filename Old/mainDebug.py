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
from utils import Params, getReferenceChromas
from fbs_runtime.application_context.PyQt5 import ApplicationContext
import librosa
from scipy.fft import rfft
import scipy.io as sio
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

        chromafbMat = sio.loadmat("/home/xribene/Projects/code_matlab_2019/F2CM.mat")['F2CM']#,mat_dtype =np.float32)
        self.chromafbMat = chromafbMat[:,:4097]

        # gui elements
        self.menuBar = MenuBar(self)
        self.toolbar = ToolBar(appctxt = appctxt, parent = self, config = self.config)

        # self.win = pg.GraphicsWindow()
        # self.img = pg.ImageItem()
        # self.win.addItem(self.img)
        self.win = pg.GraphicsWindow()
        self.plot = self.win.addPlot(title = "Spectrogram",
                                  labels = {
                                  'bottom':"Score Frame (V(t))",
                                  'left':"Audio Frame (V(j))"},
                                   backround = "white")
        self.plotChroma = self.win.addPlot(title = "Chroma",
                                  labels = {
                                  'bottom':"Score Frame (V(t))",
                                  'left':"Audio Frame (V(j))"},
                                   backround = "white")
        self.plotChroma2 = self.win.addPlot(title = "ChromaMIDI",
                                  labels = {
                                  'bottom':"Score Frame (V(t))",
                                  'left':"Audio Frame (V(j))"},
                                   backround = "white")
        self.plotChroma3 = self.win.addPlot(title = "ChromaMat",
                                  labels = {
                                  'bottom':"Score Frame (V(t))",
                                  'left':"Audio Frame (V(j))"},
                                   backround = "white")
        self.img = pg.ImageItem()
        self.imgChroma = pg.ImageItem()
        self.imgChroma2 = pg.ImageItem()
        self.imgChroma3 = pg.ImageItem()

        self.plot.addItem(self.img)
        self.plotChroma.addItem(self.imgChroma)
        self.plotChroma2.addItem(self.imgChroma2)
        self.plotChroma3.addItem(self.imgChroma3)

        self.img_array = np.zeros((1000, 500))#self.config.n_fft//2+1))
        self.chroma_array = np.zeros((1000, self.config.n_chroma))
        self.chroma_array2 = np.zeros((1000, self.config.n_chroma))
        self.chroma_array3 = np.zeros((1000, self.config.n_chroma))

        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        self.img.setLookupTable(lut)
        self.img.setLevels([-50,40])
        self.imgChroma.setLevels([0,1])
        self.imgChroma2.setLevels([0,1])
        self.imgChroma3.setLevels([0,1])

        freq = np.arange((self.config.n_fft//2)+1)/(float(self.config.n_fft)/self.config.sr)
        yscale = 1.0/((self.config.n_fft//2+1)/freq[-1])
        self.img.scale((1./self.config.sr)*self.config.n_fft, yscale)

        # self.setLabel('left', 'Frequency', units='Hz')

        self.buffer = np.zeros(self.config.window_length - self.config.hop_length).astype(np.float32)
        self.fft_window = librosa.filters.get_window(self.config.window_type, self.config.window_length, fftbins=True)
        self.chromafb = librosa.filters.chroma(sr = self.config.sr, n_fft = self.config.n_fft, tuning=0.0, n_chroma=self.config.n_chroma)



        # self.win = pg.GraphicsWindow()
        # self.plot = self.win.addPlot(title = "Minimum Cost Path",
        #                           labels = {
        #                           'bottom':"Score Frame (V(t))",
        #                           'left':"Audio Frame (V(j))"},
        #                            backround = "white")
        # self.scatter = pg.ScatterPlotItem(
        #                     size=10, brush=pg.mkBrush(255, 255, 255, 120))
        # self.plot.addItem(self.scatter)
        # layout
        s = QStyleFactory.create('Fusion')
        self.setStyle(s)
        mainLayout = QGridLayout(self) 
        # mainLayout.addWidget(logTextBox.widget)
        # mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.toolbar)#, 0,0,3,1, Qt.AlignLeft|Qt.AlignTop)
        # mainLayout.addWidget(self.win)
        # mainLayout.addWidget(self.textEdit)

        mainLayout.addWidget(self.win)

        self.setLayout(mainLayout)
        self.resize(1000,1000)
        self.show()

        
        # TODO a window for the user to choose which score to use
        self.status.piece= "jetee"

        self.testWavFile = appctxt.get_resource(f"{self.status.piece}FF.wav")
        # self.testWavFile = appctxt.get_resource(f"recordedJetee.wav")

        self.timer = QtCore.QTimer()
        midiFile = appctxt.get_resource(f"{self.status.piece}4.mid")
        self.midiChromas = getReferenceChromas(Path(midiFile), 
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
        self.i = 0

        self.setupThreads()
        self.signalsandSlots()

    def setupThreads(self):
        self.readQueue = queue.Queue()
        # self.chromaBuffer = queue.LifoQueue(10000)
        ## threads
        self.audioThread = QThread()
        self.audioRecorder = AudioRecorder(queue = self.readQueue, 
                                           wavfile = self.testWavFile, # 
                                           rate = self.config.sr,
                                           # ! be careful, audio streams chunk is 
                                           # ! equal to the hop_length
                                           chunk = self.config.hop_length,
                                           input_device_index=self.config.input_device_index)
        # ? Not sure if we need a separate thread for the audio stream. 
        # ? pyaudio already calls the callback on a different thread.
        self.audioRecorder.moveToThread(self.audioThread)
        self.audioThread.start()
        logging.debug("setup threads done")

    def signalsandSlots(self):
        # self.audioRecorder.signalToChromatizer.connect(self.chromatizer.calculate)
        self.audioRecorder.signalToChromatizer.connect(self.updatePlots)

        self.audioRecorder.signalEnd.connect(self.closeEvent)
        self.toolbar.playPause.triggered.connect(self.startPauseAlignment)

    def closeEvent(self, event):
        self.audioRecorder.closeStream()
        logging.debug(f"close Event")

    def startPauseAlignment(self):
        # TODO communicate with audio Recorder using slots (if audio recorder is a thread)
        self.audioRecorder.startStopStream()
        if self.audioRecorder.stopped is True:
            self.toolbar.playPause.setIcon(QtGui.QIcon(self.appctxt.get_resource("svg/rec.svg")))
        else:
            self.toolbar.playPause.setIcon(QtGui.QIcon(self.appctxt.get_resource("svg/pause.svg")))

    @pyqtSlot(object)
    def updatePlots(self, frame):

        y = frame.astype('float32') / 32768.0
        y_conc = np.concatenate((self.buffer, y))
        # logging.debug(f"{self.buffer.shape} {y.shape} {y_conc.shape}")
        self.buffer = y_conc[self.config.hop_length:]
        chunk_win = self.fft_window * y_conc
        real_fft = rfft(chunk_win, n = self.config.n_fft)
        fft_mag = np.abs(real_fft)**2
        psd = 20 * np.log10(fft_mag)
        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:] = np.reshape(psd, (1,-1))[:,:500]
        self.img.setImage(self.img_array, autoLevels=False)

        raw_chroma = np.dot(self.chromafb, np.abs(real_fft)**self.config.magPower)
        norm_chroma = librosa.util.normalize(raw_chroma, norm=self.config.norm, axis=0).reshape(-1,1)

        raw_chromaMat = np.dot(self.chromafb, np.abs(real_fft)**2)
        norm_chromaMat = librosa.util.normalize(raw_chromaMat, norm=self.config.norm, axis=0).reshape(-1,1)

        self.chroma_array = np.roll(self.chroma_array, -1, 0)
        self.chroma_array[-1:] = np.reshape(norm_chroma, (1,-1))
        self.imgChroma.setImage(self.chroma_array, autoLevels=False)

        self.chroma_array2 = np.roll(self.chroma_array2, -1, 0)
        self.chroma_array2[-1:] = np.reshape(self.midiChromas[min(self.i,self.midiChromas.shape[0]),:], (1,-1))
        self.imgChroma2.setImage(self.chroma_array2, autoLevels=False)

        self.chroma_array3 = np.roll(self.chroma_array3, -1, 0)
        self.chroma_array3[-1:] = np.reshape(norm_chromaMat, (1,-1))
        self.imgChroma3.setImage(self.chroma_array3, autoLevels=False)

        self.i += 1

if __name__ == "__main__":
    QThread.currentThread().setObjectName('MainThread')
    logging.getLogger().setLevel(logging.DEBUG)
    # Uncomment below for terminal log messages
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

    appctxt = ApplicationContext()
    app = QApplication(sys.argv)
    mainWindow = ScoreFollower(appctxt)
    exit_code = app.exec_()
    sys.exit(exit_code)
