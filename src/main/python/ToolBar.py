# pyQt5 imports
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QLabel, QSpinBox, QLabel, QAction, QToolBar, QLCDNumber)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (QIcon)
class ToolBar(QToolBar):
    def __init__(self, appctxt, config, parent):
        super(ToolBar,self).__init__(parent)
        self.appctxt = appctxt
        self.config = config
        self.setIconSize(QSize(30,30))

        self.playPause = QAction("Play/Pause (Space)",self)
        self.playPause.setShortcut(Qt.Key_Space)
        self.playPause.setShortcutContext(Qt.ApplicationShortcut)
        self.playPause.setIcon(QIcon(self.appctxt.get_resource("svg/rec.svg")))

        # self.reset = QAction("Reset Memory (Ctrl+R)",self)
        # self.reset.setShortcut("Ctrl+R")
        # self.reset.setShortcutContext(Qt.ApplicationShortcut)
        # self.reset.setIcon(QIcon(self.appctxt.get_resource("Images/svg/reset.svg")))

        # self.condition = QAction("Condition (Ctrl+C)",self)
        # self.condition.setShortcut("Ctrl+C")
        # self.condition.setShortcutContext(Qt.ApplicationShortcut)
        # self.condition.setIcon(QIcon(self.appctxt.get_resource("Images/svg/upload.svg")))

        self.preferences = QAction("Preferences (Ctrl+P)",self)
        self.preferences.setShortcut("Ctrl+P")
        self.preferences.setShortcutContext(Qt.ApplicationShortcut)
        self.preferences.setIcon(QIcon(self.appctxt.get_resource("svg/settings.svg")))

        self.save = QAction("Save (Ctrl+S)",self)
        self.save.setShortcut("Ctrl+S")
        self.save.setShortcutContext(Qt.ApplicationShortcut)
        self.save.setIcon(QIcon(self.appctxt.get_resource("svg/save.svg")))

        
        self.lcd = QLCDNumber(self)
        self.lcd.display(1)
        self.lcd.setDigitCount(1)
        self.lcd.setFixedHeight(35)
        self.lcd.setFixedWidth(35)

        # self.bpmBox = QSpinBox(self)
        # self.bpmBox.setSuffix(" BPM")
        # #self.bpmBox.setMinimumSize(30,30)
        # self.bpmBox.setFixedHeight(35)
        # self.bpmBox.setRange(20,150)
        # self.bpmBox.setSingleStep(5)
        # self.bpmBox.setValue(self.config['metronome']["BPM"])

        # self.enforce = QAction("Enforce",self)
        # self.enforce.setShortcut("Ctrl+E")
        # self.enforce.setShortcutContext(Qt.ApplicationShortcut)

        # self.clear = QAction("Clear",self)
        # #self.clear.setShortcut("Ctrl+E")
        # self.clear.setShortcutContext(Qt.ApplicationShortcut)

        #self.enforce.setIcon(QIcon(self.appctxt.get_resource("Images/reset.svg")))
        #self.toolbarAction.setStatusTip("STARTPAUSE")
        #self.toolbarAction.setWhatsThis("srgsr")
        self.addAction(self.playPause)
        # self.addAction(self.reset)
        # self.addAction(self.condition)
        self.addAction(self.preferences)
        self.addAction(self.save)
        # self.addWidget(self.bpmBox)
        self.addWidget(self.lcd)
        self.keyIndicator = QLabel("          ", objectName='keyIndicator')