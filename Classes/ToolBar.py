# pyQt5 imports
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QLabel, QSpinBox, QLabel, QAction, QToolBar, QLCDNumber)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (QIcon)
from offline.utils_offline import resource_path
class ToolBar(QToolBar):
    def __init__(self, appctxt, config, parent):
        super(ToolBar,self).__init__(parent)
        self.appctxt = appctxt
        self.config = config
        self.setIconSize(QSize(30,30))

        self.playPause = QAction("Play/Pause (Space)",self)
        self.playPause.setShortcut(Qt.Key_Space)
        self.playPause.setShortcutContext(Qt.ApplicationShortcut)
        self.playPause.setIcon(QIcon(resource_path("resources/svg/rec.svg")))

        # self.reset = QAction("Reset Memory (Ctrl+R)",self)
        # self.reset.setShortcut("Ctrl+R")
        # self.reset.setShortcutContext(Qt.ApplicationShortcut)
        # self.reset.setIcon(QIcon(self."Images/svg/reset.svg")))

        # self.condition = QAction("Condition (Ctrl+C)",self)
        # self.condition.setShortcut("Ctrl+C")
        # self.condition.setShortcutContext(Qt.ApplicationShortcut)
        # self.condition.setIcon(QIcon(self."Images/svg/upload.svg")))

        # self.preferences = QAction("Preferences (Ctrl+P)",self)
        # self.preferences.setShortcut("Ctrl+P")
        # self.preferences.setShortcutContext(Qt.ApplicationShortcut)
        # self.preferences.setIcon(QIcon(resource_path("extraResources/settings.svg")))

        # self.save = QAction("Save (Ctrl+S)",self)
        # self.save.setShortcut("Ctrl+S")
        # self.save.setShortcutContext(Qt.ApplicationShortcut)
        # self.save.setIcon(QIcon(resource_path("extraResources/save.svg")))

        self.reset = QAction("Reset (Ctrl+R)",self)
        self.reset.setShortcut("Ctrl+R")
        self.reset.setShortcutContext(Qt.ApplicationShortcut)
        self.reset.setIcon(QIcon(resource_path("resources/svg/reset.svg")))

        self.addAction(self.playPause)
        # self.addAction(self.reset)
        # self.addAction(self.condition)
        # self.addAction(self.preferences)
        self.addAction(self.reset)
        # self.addWidget(self.bpmBox)
        # self.addWidget(self.lcd)
        # self.keyIndicator = QLabel("          ", objectName='keyIndicator')