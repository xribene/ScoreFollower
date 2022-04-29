###########import statements#################
##standard PyQt imports (thanks christos!)###
from PyQt5 import QtGui, QtCore, QtSvg
from PyQt5.QtWidgets import (QComboBox,  QPushButton,
        QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QTextEdit,  QVBoxLayout, QLCDNumber,QLabel, QHBoxLayout, QTextEdit, QGridLayout)

from PyQt5.QtCore import (QObject, pyqtSlot, pyqtSignal, QThread, Qt)
from pyqtgraph import plot
import pyqtgraph as pg

import logging

import numpy as np

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
        self.serverMessageText.document().setMaximumBlockCount(10)
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
        # self.setFixedSize(300,300)
        self.setMinimumSize(300,100)
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
        self.setMinimumSize(300,300)
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

        # self.tuningDisp = QLineEdit(self)
        # self.tuningDisp.setEnabled(False)
        # self.tuningDisp.setObjectName("tuningDisp")

        self.channelDisp = QLineEdit(self)
        self.channelDisp.setEnabled(True)
        self.channelDisp.setObjectName("tuningDisp")
        rx = QtCore.QRegExp(r"^([1-9]{1,2};)*[0-9]{1,2}$")
        chanValidator = QtGui.QRegExpValidator(rx, self)
        self.channelDisp.setValidator(chanValidator)
        self.channelDisp.setText(str(0))

        self.dropdownAudioInput = QComboBox(self)
        self.inputLabel = QLabel("Input")
        self.inputLabel.setBuddy(self.dropdownMode)

        self.dropdownAudioOutput = QComboBox(self)
        self.outputLabel = QLabel("Output")
        self.outputLabel.setBuddy(self.dropdownMode)

        self.layout.addWidget(self.modeLabel,          0, 0, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.dropdownMode,       0, 1, 1, 3)#, Qt.AlignCenter)
        
        self.layout.addWidget(self.inputLabel,         1, 0, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.dropdownAudioInput, 1, 1, 1, 3)#, Qt.AlignCenter)
        self.layout.addWidget(self.rmsDisp,            2, 1, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.rmsThrDisp,         2, 2, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.channelDisp,         2, 3, 1, 1)#, Qt.AlignCenter)

        self.layout.addWidget(self.outputLabel,        3, 0, 1, 1)#, Qt.AlignCenter)
        self.layout.addWidget(self.dropdownAudioOutput,3, 1, 1, 3)#, Qt.AlignCenter)

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

        self.win = pg.GraphicsWindow()#size=(500,500)
        self.win.setBackground('#001219')
        # self.win.getAxis('left').setTextPen('b')


        # self.setMinimumSize(300,300)
        self.plot = self.win.addPlot(title = "Minimum Cost Path",
                                #   labels = {
                                #   'bottom':"Audio Frames",
                                #   'left':"Score Frames"},
                                   )
        self.scatter = pg.ScatterPlotItem(
            size=3, brush=pg.mkBrush("#94d2bd"))
        self.plot.addItem(self.scatter)

        label_style = {"color": "#bb3e03", "font-size": "14pt"}
        self.plot.setLabel("bottom", "Audio time (sec)", **label_style)
        self.plot.setLabel("left", "Score Bars", **label_style)
        self.plot.setLabel("right", "Score Cues", **label_style)
        # axis_style = {
        #     # 'tickTextOffset': [5, 2],
        #                 # 'tickTextWidth': 30,
        #                 # 'tickTextHeight': 18,
        #                 # 'autoExpandTextSpace': True,
        #                 # 'autoReduceTextSpace': True,
        #                 # 'tickFont': QtGui.QFont("Times", QtGui.QFont.Bold),
        #                 # 'stopAxisAtTick': (False, False),
        #                 # 'textFillLimits': [(0, 0.8), (2, 0.6), (4, 0.4), (6, 0.2)],
        #                 # 'showValues': True,
        #                 # 'tickLength': -5,
        #                 # 'maxTickLevel': 2,
        #                 # 'maxTextLevel': 2,
        #                 # 'tickAlpha': None
        #                 }
        # axis_style = self.plot.getAxis("left").style
        # axis_style['tickFond'] = QtGui.QFont("Times", QtGui.QFont.Bold)
        # axis_style['tickTextOffset'] = [5,2]
        # self.plot.getAxis("left").setStyle(**axis_style)
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
    signalNewBarOsc = pyqtSignal(str)
    signalNewCueOsc = pyqtSignal(str)
    def __init__(self, config, oscClient, oscListener, qLabGroup, main):
        super(QLabInterface, self).__init__()

        # initializations
        self.setObjectName("QLabInterface")
        self.config = config
        self.main = main
        self.oscClient = oscClient
        self.oscListener = oscListener
        self.qLabGroup = qLabGroup
        self.connectionStatus = False
        self.greetingsCnt = 0
        self.greetingsRsp = 0

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
        address = f"cue/{int(cue['name'])}"
        self.oscClient.emit(address, arg = None)
        self.updateClientText(address, args = None)
        
    def sendBarTrigger(self, cue):
        address = f"/bar/{cue['ind']}"
        self.oscClient.emit(address, arg = None)
        self.updateClientText(address, args = None)

    def sendStartTrigger(self):
        address = f"/start"
        # self.oscClient.emit(address, arg = None)
        # self.updateClientText(address, args = None)

    def sendStopTrigger(self):
        address = f"/stop"
        # self.oscClient.emit(address, arg = None)
        # self.updateClientText(address, args = None)
    
    def sendFeedback(self, mode, args = None):
        if mode == 'cue':
            address = f"/feedback/cue/{args}"
        elif mode == 'bar':
            address = f"/feedback/bar/{args}"
        elif mode == 'start':
            address = f"/feedback/started"
        elif mode == 'stop':
            address = f"/feedback/stopped"
        elif mode == 'reset':
            address = f"/feedback/reset"
        elif mode == 'pause':
            address = f"/feedback/paused"
        elif mode == 'piece':
            address = f"/feedback/piece/{args}"
        elif mode == 'section':
            address = f"/feedback/section/{args}"
        self.oscClient.emit(address, arg = args)
        self.updateClientText(address, args = args)



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
        # TODO # ! There is no QLab interface anymore. 
        # TODO Move the callbackRouters in main.py
        # TODO because there's gonna be a ton of extra signals/slots
        # TODO for each new command
        # ! or just have the parent/main.py as an input here
        address = load[0]
        args = load[1]
        addressParts = address.split("/")[1:]
        
        # first part should be always "reply"
        print(addressParts)
        if addressParts[0] != "response":
            logging.error(f"TouchResponseCallback got {address} and args {args}")
            raise # TODO not a good idea to raise like this
        
        if len(addressParts) >= 2:
            if addressParts[1] == "setBar":
                newBar = addressParts[2]
                self.signalNewBarOsc.emit(newBar)
                logging.debug(f"Setting bar to {addressParts[2]}")

            elif addressParts[1] == "setCue":
                newCue = addressParts[2]
                self.signalNewCueOsc.emit(newCue)
                logging.debug(f"Setting cue to {addressParts[2]}")

            elif addressParts[1] == "nextBar":
                self.main.nextBar()
                logging.debug(f"Received /nextBar command")
            elif addressParts[1] == "prevBar":
                self.main.prevBar()
                logging.debug(f"Received /prevBar command")
            
            elif addressParts[1] == "nextCue":
                self.main.nextCue()
                logging.debug(f"Received /nextCue command")
            elif addressParts[1] == "prevCue":
                self.main.prevCue()
                logging.debug(f"Received /prevCue command")
            
            elif addressParts[1] == "start":
                logging.debug(f"Received /start command from TD")
                self.main.startRecording(feedback = True)
            elif addressParts[1] == "stop":
                logging.debug(f"Received /stop command from TD")
                self.main.stopButtonCallback()
            elif addressParts[1] == "startStop":
                logging.debug(f"Received /starSTop command from TD")
                self.main.startStopRecording(feedback = True)
            elif addressParts[1] == "pause":
                logging.debug(f"Received /pause command from TD")
                self.main.stopRecording(feedback = True)
            elif addressParts[1] == "reset":
                logging.debug(f"Received /reset command from TD")
                self.main.reset()

            elif addressParts[1] == "nextSection":
                logging.debug(f"Received /nextSection command from TD")
                logging.debug(f'current section is {self.main.sectionName} with index {self.main.sectionNames.index(self.main.sectionName)}')
                
                currentInd = self.main.sectionNames.index(self.main.sectionName)
                if currentInd < len(self.main.sectionNames) - 1:
                    logging.debug(f'inside IF')
                    
                    self.main.sectionName = self.main.sectionNames[currentInd + 1]
                    self.main.scoreGroup.dropdownSection.setCurrentIndex(currentInd + 1)
                    # ! TODO same name on different sections doesn't work because of index.
            elif addressParts[1] == "prevSection":
                logging.debug(f"Received /prevSection command from TD")
                currentInd = self.main.sectionNames.index(self.main.sectionName)
                if currentInd > 0:
                    self.main.stopRecording()
                    self.main.sectionName = self.main.sectionNames[currentInd - 1]
                    self.main.scoreGroup.dropdownSection.setCurrentIndex(currentInd - 1)

            elif addressParts[1] == "nextPiece":
                logging.debug(f"Received /nextPiece command from TD")
                currentInd = self.main.pieceNames.index(self.main.pieceName)
                print(f"currentInd {currentInd} and pieceNames {self.main.pieceNames}")
                if currentInd < len(self.main.pieceNames) - 1:
                    print(f"Setting piece to {self.main.pieceNames[currentInd + 1]}")
                    self.main.stopRecording()
                    self.main.pieceName = self.main.pieceNames[currentInd + 1]
                    self.main.scoreGroup.dropdownPiece.setCurrentIndex(currentInd + 1)
            elif addressParts[1] == "prevPiece":
                logging.debug(f"Received /prevPiece command from TD")
                currentInd = self.main.pieceNames.index(self.main.pieceName)
                print(f"currentInd {currentInd} and pieceNames {self.main.pieceNames}")
                if currentInd > 0:
                    print(f"Setting piece to {self.main.pieceNames[currentInd - 1]}")
                    self.main.stopRecording()
                    self.main.pieceName = self.main.pieceNames[currentInd - 1]
                    self.main.scoreGroup.dropdownPiece.setCurrentIndex(currentInd - 1)
            elif addressParts[1] == "setPiece":
                logging.debug(f"Received {addressParts} command from TD")
                try:
                    newInd = self.main.pieceNames.index(addressParts[2])
                    self.main.stopRecording()
                    self.main.pieceName = self.main.pieceNames[newInd]
                    self.main.scoreGroup.dropdownPiece.setCurrentIndex(newInd)
                except:
                    logging.error(f"Could not find {addressParts[2]} in {self.main.pieceNames}")
                    
        self.updateListenerText("touchDesigner", addressParts, args)

    def unknownResponseCallbackRouter(self, load):
        address = load[0]
        args = load[1]
        self.updateListenerTextUnformatted("unkown", address, args)