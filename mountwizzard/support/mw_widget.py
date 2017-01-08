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

# import basic stuff
import logging

# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class MwWidget(QWidget):

    logger = logging.getLogger(__name__)

    def __init__(self):
        super(MwWidget, self).__init__()                                                                                    # Initialize Class for UI
        self.blueColor = QColor(32, 144, 192)                                                                               # blue astro color
        self.yellowColor = QColor(192, 192, 0)
        self.greenColor = QColor(0, 255, 0)
        self.whiteColor = QColor(192, 192, 192)
        self.COLOR_POINTER = QColor(255, 0, 255)
        self.moving = False                                                                                                 # check if window moves with mouse pointer
        self.offset = None                                                                                                  # check offset from mouse pick point to window 0,0 reference point
        self.initUI()                                                                                                       # adapt the window to our purpose

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
        darkPalette.setColor(QPalette.Text, self.blueColor)
        darkPalette.setColor(QPalette.Button, QColor(24, 24, 24))
        darkPalette.setColor(QPalette.ButtonText, QColor(192, 192, 192))
        darkPalette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        darkPalette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(darkPalette)
        self.palette = QPalette()                                                                                                # title text
        self.palette.setColor(QPalette.Foreground, self.blueColor)
        self.palette.setColor(QPalette.Background, QColor(53, 53, 53))

