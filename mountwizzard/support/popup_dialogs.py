############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################


# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from support.popup_dialog_ui import Ui_PopupDialog


class MyPopup(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.moving = False                                                                                                 # check if window moves with mouse pointer
        self.offset = None                                                                                                  # check offset from mouse pick point to window 0,0 reference point
        self.ui = Ui_PopupDialog()
        self.ui.setupUi(self)
        self.initUI()

    def mousePressEvent(self, mouseEvent):                                                                                  # overloading the mouse events for handling customized windows
        self.modifiers = mouseEvent.modifiers()
        if mouseEvent.button() == Qt.LeftButton:
            self.moving = True
            self.offset = mouseEvent.pos()

    def mouseMoveEvent(self, mouseEvent):
        if self.moving:
            cursor = QCursor()
            self.move(cursor.pos() - self.offset)

    def mouseReleaseEvent(self, mouseEvent):
        if self.moving:
            cursor = QCursor()
            self.move(cursor.pos() - self.offset)
            self.moving = False

    def initUI(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        darkPalette = QPalette()                                                                                            # set dark palette
        darkPalette.setColor(QPalette.Window, QColor(32, 32, 32))
        darkPalette.setColor(QPalette.WindowText, QColor(192, 192, 192))
        darkPalette.setColor(QPalette.Base, QColor(25, 25, 25))
        darkPalette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        darkPalette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        darkPalette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        darkPalette.setColor(QPalette.Text, QColor(32, 144, 192))
        darkPalette.setColor(QPalette.Button, QColor(24, 24, 24))
        darkPalette.setColor(QPalette.ButtonText, QColor(192, 192, 192))
        darkPalette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        darkPalette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(darkPalette)
        palette = QPalette()                                                                                                # title text
        palette.setColor(QPalette.Foreground, QColor(32, 144, 192))
        palette.setColor(QPalette.Background, QColor(53, 53, 53))
        self.ui.windowTitle.setPalette(palette)

