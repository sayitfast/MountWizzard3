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
import logging
import os
import sys

# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import PyQt5


class MwWidget(QWidget):

    logger = logging.getLogger(__name__)
    COLOR_ASTRO = QColor(32, 144, 192)  # blue astro color
    COLOR_BLUE = QColor(0, 0, 255)
    COLOR_YELLOW = QColor(192, 192, 0)
    COLOR_GREEN = QColor(0, 255, 0)
    COLOR_GREEN_HORIZON = QColor(0, 64, 0)
    COLOR_GREEN_HORIZON_DARK = QColor(0, 32, 0)
    COLOR_WHITE = QColor(255, 255, 255)
    COLOR_RED = QColor(255, 0, 0)
    COLOR_ORANGE = QColor(192, 96, 96)
    COLOR_BLACK = QColor(0, 0, 0)
    COLOR_POINTER = QColor(255, 0, 255)
    COLOR_TRACKWIDGETTEXT = QColor(255, 255, 255)
    COLOR_TRACKWIDGETPOINTS = QColor(128, 128, 128)
    COLOR_WINDOW = QColor(32, 32, 32)
    COLOR_WINDOW_TEXT = QColor(192, 192, 192)
    COLOR_BACKGROUND = QColor(53, 53, 53)
    COLOR_BASE = QColor(25, 25, 25)
    COLOR_BASE_MAIN = QColor(16, 72, 96)
    COLOR_ALTERNATE_BASE = QColor(53, 53, 53)
    COLOR_HIGHLIGHT = QColor(42, 130, 218)

    # define the basic style of the mountwizzard theme
    BASIC_STYLE = """
    QWidget {
        background-color: #181818;
    }
    QLabel {
        background-color: transparent;
        color: #C0C0C0;
    }
    QLabel#mainBackgound {
        border-width: 3px;
        border-color: rgb(16, 72, 96);
        border-style: outset;
        border-radius: 2px;
        background-color: rgb(8, 36, 48);
    }
    
    /* QLine Edit*/
    QLineEdit {
        background-color: #101010;
        color: rgb(32, 144, 192);
        text-align: right;
        border-width: 1px;
        border-color: #404040;
        border-style: outset;
        border-radius: 2px;
    }
    QLineEdit[check='false'] {
        background-color: #101010;
        color: rgb(255, 0, 0);
    }
    QLineEdit[check='true'] {
        background-color: #101010;
        color: rgb(32, 144, 192);
    }

    /* Checkboxes */
    QCheckBox {
        color: #C0C0C0;
    }
    QCheckBox::indicator {
        border-width: 1px;
        border-color: #404040;
        background-color: #101010;
        border-style: outset;
        border-radius: 2px;
    }
    QCheckBox::indicator:checked {
        background-color: rgb(32, 144, 192);
    }
    
    /* Spin Boxes */
    QDoubleSpinBox {
        background-color: #101010;
        color: rgb(32, 144, 192);
        text-align: right;
        font-family: Arial;
        font-style: normal;
        font-size: 10pt;
        font-weight: bold;
        border-color: #404040;
        border-width: 1px;
        border-style: outset;
        border-radius: 2px;
        padding-right: 2px;
    }
    QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right; /* position at the top right corner */
        width: 12px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
        border-width: 1px;
        border-radius: 2px;
        border-color: #404040;
        border-style: outset;
        background-color: #181818;
    }
    QDoubleSpinBox::up-arrow {
        image: url(mountwizzard/icons/arrow-up.ico);
        width: 12px;
        height: 16px;
    }
    QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right; /* position at the top right corner */
        width: 12px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
        border-width: 1px;
        border-style: outset;
        border-radius: 2px;
        border-color: #404040;
        background-color: #181818;
    }
    QDoubleSpinBox::down-arrow {
        image: url(mountwizzard/icons/arrow-down.ico);
        width: 12px;
        height: 16px;
    }
    
    /* Push Buttons */
    QPushButton {
        background-color: #202020;
        color: #C0C0C0;
        border-color: #404040;
        border-width: 1px;
        border-style: outset;
        border-radius: 2px;
        font: 10pt;
        min - width: 10em;
    }
    QPushButton:pressed {
        background-color: #181818;
        color: #C0C0C0;
        border-color: #404040;
        border-width: 2px;
        border-style: inset;
        border-radius: 2px;
    }
    QPushButton[running='true'] {
        background-color: rgb(16, 72, 96);
        color: #C0C0C0;
    } 
    QPushButton[running='false'] {
        background-color: #202020;
        color: #C0C0C0;
    }     
    QPushButton[cancel='true'] {
        background-color: rgb(96,0, 0);
        color: #000000;
    } 
    QPushButton[cancel='false'] {
        background-color: #202020;
        color: #C0C0C0;
    }
    QPushButton[iconset='true'] {
        text-align: left;
        padding-left: 6px;
    }
    
    /* Combo Boxes */
    QComboBox {
        text-align: right;
        color: #C0C0C0;
        border-color: #404040;
        border-width: 1px;
        border-style: outset;
        border-radius: 2px;
        padding-left: 5px;
        background-color: #202020;
    }
    QComboBox::drop-down {
        subcontrol-origin: border;
        subcontrol-position: right; /* position at the top right corner */
        width: 20px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
        border-color: #404040;
        border-width: 1px;
        border-style: outset;
        border-radius: 2px;
        background-color: #202020;
    }
    QComboBox::down-arrow {
        image: url(mountwizzard/icons/arrow-down.ico);
        width: 20px;
        height: 32px;
    }
    QComboBox:item {
        padding-left: 20px;  /* move text right to make room for tick mark */
        height: 30px;
        background-color: #202020;
    }
    QComboBox:item:selected {
        padding-left: 20px;
        border-width: 2px;
        border-radius: 2px;
        border-style: outset;
        border-color: rgb(16, 72, 96);
        background-color: rgb(32, 144, 192);
    }
    /* lines */
    QFrame[frameShape="4"] {/* horizontal lines */
        color: rgb(16, 72, 96);
    }
    QFrame[frameShape="5"] {/* vertical lines */
        color: rgb(16, 72, 96);
    }
    QTabWidget:pane {
        border-width: 2px;
        border-color: #404040;
        border-radius: 2px;
        border-style: outset;
    }
    QTabBar::tab {
        background-color: #202020;
        color: #C0C0C0;
        border-width: 2px;
        border-color: rgb(16, 72, 96);
        border-radius: 2px;
        border-style: outset;
        min-width: 12ex;
        padding: 4px;
        padding-left: 4px;
        padding-right: 4px;
    }
    QTabBar::tab:selected {
        color: #000000;
        background: rgb(32, 144, 192);
    }
    QTabBar::tab:!selected {
        margin-top: 4px;
    }
    QTabBar::tab:only-one {
        margin: 1;
    }
    """

    def __init__(self):
        # noinspection PyArgumentList
        super(MwWidget, self).__init__()
        self.palette = QPalette()
        self.bundle_dir = ''
        self.showStatus = False
        self.initUI()

    def closeEvent(self, closeEvent):
        self.showStatus = False

    def widgetIcon(self, gui, icon):
        gui.setIcon(PyQt5.QtGui.QIcon(self.bundle_dir + '\\icons\\' + icon))
        gui.setProperty('iconset', True)
        gui.style().unpolish(gui)
        gui.style().polish(gui)
        gui.setIconSize(PyQt5.QtCore.QSize(16, 16))

    # noinspection PyProtectedMember
    def initUI(self):
        # self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowFlags((self.windowFlags() | Qt.CustomizeWindowHint) & ~Qt.WindowMaximizeButtonHint)
        self.setMouseTracking(True)

        # sizing in gui should be fixed, because I have a static layout
        self.setFixedSize(790, 640)
        # set app icon
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            self.bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            self.bundle_dir = os.path.dirname(sys.modules['__main__'].__file__)
        self.setWindowIcon(QIcon(self.bundle_dir + '\\icons\\mw.ico'))
        self.setStyleSheet(self.BASIC_STYLE)
