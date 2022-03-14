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
        
        self.setObjectName("QLabBox")
        self.setTitle("&QLab - Disconnected")
        self.setStyleSheet('#QLabBox:title {color: rgb(0,0,0);background-color: rgb(200, 0, 0);}')
        self.setMinimumSize(1000,300)
        self.appctxt = appctxt
        self.layout = QHBoxLayout(self)


        # self.status = QStatusBar(self)
        # self.status.showMessage("Disconnected")
        # self.status.setStyleSheet("background-color: rgb(0, 255, 0);")

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
        self.setTitle("&ScoreBox")
        self.setFixedSize(300,300)
        self.appctxt = appctxt
        self.layout = QGridLayout(self)
        self.barLabel = QLabel("Bar")
        self.cueLabel = QLabel("Cue")
        self.barLcd = QLCDNumber()
        self.barLcd = QLCDNumber(self)
        self.barLcd.display(-1)
        self.barLcd.setDigitCount(3)
        # self.barLcd.setFixedHeight(35)
        # self.barLcd.setFixedWidth(35)
        self.cueLcd = QLCDNumber()
        self.cueLcd = QLCDNumber(self)
        self.cueLcd.display(-1)
        self.cueLcd.setDigitCount(3)
        self.barLabel.setBuddy(self.barLcd)
        self.cueLabel.setBuddy(self.cueLcd)

        self.dropdownPiece = QComboBoxBlocking(self)
        self.dropdownAudioSource = QComboBoxBlocking(self)
        # self.dropdown.addItem("Jetee")

        self.layout.addWidget(self.dropdownPiece, 0, 0, 1, 1,Qt.AlignCenter)
        self.layout.addWidget(self.dropdownAudioSource, 1, 0, 1, 1,Qt.AlignCenter)
        # self.layout.addWidget(self.bar)

        self.layout.addWidget(self.barLabel, 2, 0, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.barLcd, 2, 1, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.cueLabel, 3, 0, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.cueLcd, 3, 1, 1, 1, Qt.AlignCenter)
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
        # self.plot.setXRange(0, 2000, padding=0)
        # self.plot.setYRange(0, 2000, padding=0)
        

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

    def reset(self):
        self.scatter.clear()
        # self.scatter.sigPlotChanged.emit(self.scatter)
        # print(dir(self.scatter))
        print("cleared scatter")


class QLabInterface(QObject):
    # signalToAligner = pyqtSignal()
    def __init__(self, appctxt, oscClient, oscListener, qLabGroup):
        super(QLabInterface, self).__init__()

        # initializations
        self.setObjectName("QLabInterface")
        self.appctxt = appctxt
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