###########import statements#################
##standard PyQt imports (thanks christos!)###
from PyQt5 import QtGui, QtCore, QtSvg
from PyQt5.QtWidgets import (QComboBox,  QPushButton,
        QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QTextEdit,  QVBoxLayout, QLCDNumber,QLabel, QHBoxLayout, QTextEdit, QGridLayout)

from PyQt5.QtCore import (QObject, pyqtSlot, QThread, Qt)
from pyqtgraph import plot
import pyqtgraph as pg

import logging

import numpy as np

class QComboBoxBlocking(QComboBox):
    def setCurrentIndex(self, ix):
        self.blockSignals(True)
        QComboBox.setCurrentText(self, ix)
        self.blockSignals(False)

class QLabBox(QGroupBox):
    def __init__(self, config, parent):
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
        
        self.setObjectName("QLabBox")
        self.setTitle("&QLab - Disconnected")
        self.setStyleSheet('#QLabBox:title {color: #001219;background-color: #ae2012;}')
        self.setMinimumSize(1000,300)
        self.config = config
        self.layout = QHBoxLayout(self)


        self.connectButton = QPushButton("refresh")
        
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

        self.layout.addWidget(self.connectButton)
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
            self.setStyleSheet('#QLabBox:title {color: #001219;background-color: #38b000;}')
        else:
            self.setTitle("&QLab - Disconnected")
            self.setStyleSheet('#QLabBox:title {color: #001219;background-color: #ae2012;}')
    def setGreenTitle(self, workspaceID):
        self.setTitle(f"&QLab - Connected - {workspaceID}")
        self.setStyleSheet('#QLabBox:title {color: #001219;background-color: #38b000;}')
    def setRedTitle(self):
        self.setTitle("&QLab - Disconnected")
        self.setStyleSheet('#QLabBox:title {color: #001219;background-color: #ae2012;}')

class ScoreBox(QGroupBox):
    def __init__(self, config, parent):
        super(ScoreBox, self).__init__()
        # Set the logger
        # logTextBox = QTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s -%(threadName)s -%(lineno)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)

        # initializations
        self.setTitle("&Score")
        self.setFixedSize(300,300)
        self.config = config
        self.layout = QGridLayout(self)
        

        self.dropdownPiece = QComboBox(self)
        self.dropdownSection = QComboBox(self)
        # self.dropdownAudioSource = QComboBox(self)
        # self.dropdown.addItem("Jetee")

        self.layout.addWidget(self.dropdownPiece, 0, 0, 1, 1)# ,Qt.AlignCenter)
        self.layout.addWidget(self.dropdownSection, 1, 0, 1, 1)# ,Qt.AlignCenter)
        # self.layout.addWidget(self.bar)

        # self.layout.addWidget(self.barLabel, 2, 0, 1, 1, Qt.AlignCenter)
        # self.layout.addWidget(self.barDisp, 2, 1, 1, 1, Qt.AlignCenter)
        # self.layout.addWidget(self.cueLabel, 3, 0, 1, 1, Qt.AlignCenter)
        # self.layout.addWidget(self.cueDisp, 3, 1, 1, 1, Qt.AlignCenter)

        # layout.setColumnMinimumWidth(0, 50) 
        # self.layout.setColumnMinimumWidth(1, 30)
        # layout.setRowMinimumHeight(0, 20) 
        # layout.setRowMinimumHeight(1, 20) 
        
        #layout.setRowStretch(5, 1)
        self.setLayout(self.layout)

class AudioBox(QGroupBox):
    def __init__(self, config, parent):
        super(AudioBox, self).__init__()

        self.setTitle("&Audio Settings")
        # self.setFixedSize(300,300)
        self.config = config
        self.layout = QGridLayout(self)

        self.dropdownMode = QComboBox(self)
        self.modeLabel = QLabel("Mode")
        self.modeLabel.setBuddy(self.dropdownMode)

        self.rmsDisp = QLineEdit(self)
        self.rmsDisp.setEnabled(False)
        self.rmsDisp.setObjectName("rmsDisp")

        self.rmsThrDisp = QLineEdit(self)
        self.rmsThrDisp.setEnabled(True)
        self.rmsThrDisp.setObjectName("rmsThrDisp")
        rmsValidator = QtGui.QDoubleValidator()
        rmsValidator.setNotation(0)
        rmsValidator.setBottom(0.0)
        rmsValidator.setTop(1000.0)
        rmsValidator.setDecimals(2)
        self.rmsThrDisp.setValidator(rmsValidator)
        self.rmsThrDisp.setText(str(self.config.defaultRmsThr))

        self.dropdownAudioInput = QComboBox(self)
        self.inputLabel = QLabel("Input")
        self.inputLabel.setBuddy(self.dropdownMode)

        self.dropdownAudioOutput = QComboBox(self)
        self.outputLabel = QLabel("Output")
        self.outputLabel.setBuddy(self.dropdownMode)

        self.layout.addWidget(self.modeLabel, 0, 0, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.dropdownMode, 0, 1, 1, 2)#, Qt.AlignCenter)
        
        self.layout.addWidget(self.inputLabel, 1, 0, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.dropdownAudioInput, 1, 1, 1, 2)#, Qt.AlignCenter)
        self.layout.addWidget(self.rmsDisp, 1, 3, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.rmsThrDisp, 1, 4, 1, 1)#, Qt.AlignCenter)

        self.layout.addWidget(self.outputLabel, 2, 0, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.dropdownAudioOutput, 2, 1, 1, 2)#, Qt.AlignCenter)

        self.setLayout(self.layout)

class AlignBox(QGroupBox):
    def __init__(self, config, parent):
        super(AlignBox, self).__init__()
        # Set the logger
        # logTextBox = QTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s.%(msecs)05d %(levelname)s %(module)s - %(funcName)s -%(threadName)s -%(lineno)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)

        # initializations
        self.setTitle("&Alignment")
        self.config = config
        self.layout = QGridLayout(self)

        self.win = pg.GraphicsWindow(size=(500,500))
        self.win.setBackground('#001219')
        # self.win.getAxis('left').setTextPen('b')


        self.setMinimumSize(300,300)
        self.plot = self.win.addPlot(title = "Minimum Cost Path",
                                #   labels = {
                                #   'bottom':"Audio Frames",
                                #   'left':"Score Frames"},
                                   )
        self.scatter = pg.ScatterPlotItem(
            size=3, brush=pg.mkBrush("#94d2bd"))
        self.plot.addItem(self.scatter)

        label_style = {"color": "#bb3e03", "font-size": "14pt"}
        self.plot.setLabel("bottom", "Audio Frames", **label_style)
        self.plot.setLabel("left", "Score Frames", **label_style)
        # self.plot.getAxis("left").setLabel(**label_style)
        # self.plot.setXRange(0, 2000, padding=0)
        # self.plot.setYRange(0, 2000, padding=0)
        

        # layout
        self.barLabel = QLabel("Bar")
        self.barLabel.setObjectName('bar')
        self.cueLabel = QLabel("Cue")
        self.cueLabel.setObjectName('cue')

        self.barVal = QtGui.QIntValidator()
        self.barVal.setBottom(0)
        # self.barVal.setTop(1000.0)
        self.barDisp = QLineEdit(self)
        self.barDisp.setEnabled(True)
        self.barDisp.setText(str(0))
        self.barDisp.setObjectName("barDisp")
        self.barDisp.setValidator(self.barVal)

        self.cueVal = QtGui.QIntValidator()
        self.cueVal.setBottom(0)
        # self.curVal.setT
        self.cueDisp = QLineEdit(self)
        self.cueDisp.setText(str(0))
        self.cueDisp.setObjectName("cueDisp")
        self.cueDisp.setValidator(self.cueVal)

        self.barLabel.setBuddy(self.barDisp)
        self.cueLabel.setBuddy(self.cueDisp)
        
        

        self.layout.addWidget(self.barLabel, 0, 0, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.barDisp, 0, 1, 1, 1, Qt.AlignLeft)
        self.layout.addWidget(self.cueLabel, 0, 2, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.cueDisp, 0, 3, 1, 1, Qt.AlignLeft)
        self.layout.addWidget(self.win, 1, 0, 4, 4)#, Qt.AlignCenter)
        # layout.setColumnMinimumWidth(0, 50) 
        # self.layout.setColumnMinimumWidth(1, 30)
        # layout.setRowMinimumHeight(0, 20) 
        # layout.setRowMinimumHeight(1, 20) 
        
        #layout.setRowStretch(5, 1)
        self.setLayout(self.layout)

    def updatePlot(self, t,j):
        spot = [{'pos': np.array([t,j]), 'data': 1}]
        self.scatter.addPoints(spot)

    def reset(self):
        self.scatter.clear()
        # self.scatter.sigPlotChanged.emit(self.scatter)
        # print(dir(self.scatter))
        print("cleared scatter")


class QLabInterface(QObject):
    # signalToAligner = pyqtSignal()
    def __init__(self, config, oscClient, oscListener, qLabGroup):
        super(QLabInterface, self).__init__()

        # initializations
        self.setObjectName("QLabInterface")
        self.config = config
        self.oscClient = oscClient
        self.oscListener = oscListener
        self.qLabGroup = qLabGroup
        self.connectionStatus = False
        self.greetingsCnt = 0
        self.greetingsRsp = 0
        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.checkConnection)
        # self.timer.start(1000)

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
        address = f"/workspace/{self.workspaceID}/playhead/{int(cue['name'])}"
        self.oscClient.emit(address, arg = None)
        self.updateClientText(address, args = None)
        
    def sendBarTrigger(self, cue):
        address = f"/bar/{cue['ind']}"
        self.oscClient.emit(address, arg = None)
        self.updateClientText(address, args = None)

    def checkConnection(self):
        # print(f"{self.connectionStatus} {self.greetingsCnt} - {self.greetingsRsp}")
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
        # print(self.qLabGroup.clientManualMessageText.text())
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

    def updateListenerText(self, source, address, args):
        if isinstance(address, str):
            address = address.split("/")[1:]
        self.qLabGroup.cursor2.setPosition(0)
        self.qLabGroup.serverMessageText.setTextCursor(self.qLabGroup.cursor2)
        self.qLabGroup.serverMessageText.insertHtml(f"<b style='color:green;'>{source}</b><br>/{'/'.join(address)}<br>{args}<br><br>")

    def updateListenerTextUnformatted(self, source, address, args):
        if isinstance(address, str):
            address = address.split("/")[1:]
        self.qLabGroup.cursor2.setPosition(0) # <b style='color:red;'>English</b>
        self.qLabGroup.serverMessageText.setTextCursor(self.qLabGroup.cursor2)
        self.qLabGroup.serverMessageText.insertHtml(f"<b style='color:red;'>{source}</b><br>{address}<br>{args}<br><br>")

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
        shown = False
        # first part should be always "reply"
        # print(addressParts)
        if addressParts[0] != "reply":
            raise # TODO not a good idea to raise like this
        # logging.debug(f"QLabInterface osc receiver got {address} and args {args}")
        # check if this is a response to Version    

        if len(addressParts) > 0:
            if addressParts[1] == "version":
                self.versionCallback(addressParts, args)
                

        if len(addressParts) > 2:
            # check if this is a response to THUMP
            if addressParts[3] == "thump":
                self.thumpCallback(addressParts, args)
            else:
                self.updateListenerText("qLab", addressParts, args)
                logging.debug(f"QLabInterface osc receiver got {address} and {args}")
                shown = True
        if shown is False:
            self.updateListenerText("qLab", addressParts, args)
    
    def touchResponseCallbackRouter(self, load):
        address = load[0]
        args = load[1]
        addressParts = address.split("/")[1:]

        # first part should be always "reply"
        # print(addressParts)
        if addressParts[0] != "response":
            logging.error(f"TouchResponseCallback got {address} and args {args}")
            raise # TODO not a good idea to raise like this
        
        # check if this is a response to Version

        self.updateListenerText("touchDesigner", addressParts, args)

    def unknownResponseCallbackRouter(self, load):
        address = load[0]
        args = load[1]
        self.updateListenerTextUnformatted("unkown", address, args)