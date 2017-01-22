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
    COLOR_ASTRO = QColor(32, 144, 192)  # blue astro color
    COLOR_BLUE = QColor(0, 0, 255)
    COLOR_YELLOW = QColor(192, 192, 0)
    COLOR_GREEN = QColor(0, 255, 0)
    COLOR_GREEN_LIGHT = QColor(0, 92, 0)
    COLOR_WHITE = QColor(255, 255, 255)
    COLOR_RED = QColor(255, 0, 0)
    COLOR_BLACK = QColor(0, 0, 0)
    COLOR_POINTER = QColor(255, 0, 255)
    COLOR_TRACKWIDGETTEXT = QColor(255, 255, 255)
    COLOR_TRACKWIDGETPOINTS = QColor(128, 128, 128)
    COLOR_WINDOW = QColor(32, 32, 32)
    COLOR_WINDOW_TEXT = QColor(192, 192, 192)
    COLOR_BACKGROUND = QColor(53, 53, 53)
    COLOR_BASE = QColor(25, 25, 25)
    COLOR_ALTERNATE_BASE = QColor(53, 53, 53)
    COLOR_HIGHLIGHT = QColor(42, 130, 218)

    def __init__(self):
        super(MwWidget, self).__init__()                                                                                    # Initialize Class for UI
        self.palette = QPalette()                                                                                           # title text
        self.moving = False                                                                                                 # check if window moves with mouse pointer
        self.offset = None                                                                                                  # check offset from mouse pick point to window 0,0 reference point
        self.modifiers = None
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
        darkPalette.setColor(QPalette.Window, self.COLOR_WINDOW)
        darkPalette.setColor(QPalette.WindowText, self.COLOR_WINDOW_TEXT)
        darkPalette.setColor(QPalette.Base, self.COLOR_BASE)
        darkPalette.setColor(QPalette.AlternateBase, self.COLOR_ALTERNATE_BASE)
        darkPalette.setColor(QPalette.ToolTipBase, self.COLOR_WHITE)
        darkPalette.setColor(QPalette.ToolTipText, self.COLOR_WHITE)
        darkPalette.setColor(QPalette.Text, self.COLOR_ASTRO)
        darkPalette.setColor(QPalette.Button, self.COLOR_BASE)
        darkPalette.setColor(QPalette.ButtonText, self.COLOR_WINDOW_TEXT)
        darkPalette.setColor(QPalette.BrightText, self.COLOR_RED)
        darkPalette.setColor(QPalette.Highlight, self.COLOR_HIGHLIGHT)
        darkPalette.setColor(QPalette.HighlightedText, self.COLOR_BLACK)
        self.setPalette(darkPalette)
        self.palette.setColor(QPalette.Foreground, self.COLOR_ASTRO)
        self.palette.setColor(QPalette.Background, self.COLOR_BACKGROUND)

