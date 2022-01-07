 
from PyQt5.QtWidgets import (QMenuBar,QAction)
from PyQt5.QtCore import Qt

class MenuBar(QMenuBar):
    def __init__(self, parent = None):
        super(MenuBar, self).__init__(parent)

        fileMenu = self.addMenu ("File")
        #editMenu = self.addMenu ("Edit")
        viewMenu = self.addMenu("View")
        helpMenu = self.addMenu("Help")
        # File actions
        importAction = QAction("Import",self)
        saveAction =  QAction("Save",self)
        saveAction.setShortcut("Ctrl+S")
        self.quitAction =  QAction("Quit",self)
        self.quitAction.setShortcut("Ctrl+Q")
        fileMenu.addAction(importAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(self.quitAction)
        # importAction.triggered.connect(self.importWidget.showWindow)
        # saveAction.triggered.connect(self.saveWidget.showWindow)
        # edit Actions
        # connectionsAction = QAction("Connections", self)
        # self.preferencesAction =  QAction("Preferences",self)
        # self.preferencesAction.setShortcutContext(Qt.ApplicationShortcut)
        # editMenu.addAction(connectionsAction)
        # editMenu.addAction(self.preferencesAction)
        # connectionsAction.triggered.connect(self.connectionsWidget.showWindow)
        # preferencesAction.triggered.connect(self.preferencesWidget.showWindow)

        # View Actions
        self.showMixerAction = QAction("Mixer", self)
        self.showMixerAction.setShortcut("F3")
        self.showMixerAction.setShortcutContext(Qt.ApplicationShortcut )

        showPianoRollAction =  QAction("Piano Roll",self)
        showStaffAction =  QAction("Staffs",self)

        showPianoRollAction.setCheckable(True)
        showPianoRollAction.setChecked(True)
        showStaffAction.setCheckable(True)
        showStaffAction.setChecked(True)
        self.showMixerAction.setCheckable(True)
        self.showMixerAction.setChecked(False)

        viewMenu.addAction(self.showMixerAction)
        viewMenu.addAction(showPianoRollAction)
        viewMenu.addAction(showStaffAction)
        
        #showPianoRollAction.triggered.connect(self.updatePianoRollShowFlag)
        # Help Actions
        self.instructionsAction = QAction("&Instructions", self)
        self.instructionsAction.setShortcut("F1")
        self.aboutAction =  QAction("&About",self)
        self.aboutQtAction =  QAction("&About Qt",self)
        helpMenu.addAction(self.instructionsAction)
        helpMenu.addAction(self.aboutAction)
        helpMenu.addAction(self.aboutQtAction)

        self.show()

