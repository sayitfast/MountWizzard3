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
import platform
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
    DEFAULT_TITLE = 'background-color: rgb(8,36,48); color: rgb(192,192,192);'
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
        color: #C0C0C0;
        }
    QLineEdit {
        background-color: #101010;
        color: rgb(32, 144, 192);
        text-align: right;
        border - style: outset;
        border - radius: 2px;
        }
    QLineEdit[check='false'] {
        background-color: #101010;
        color: rgb(255, 0, 0);
        text-align: right;
        border - style: outset;
        border - radius: 2px;
        }
    QLineEdit[check='true'] {
        background-color: #101010;
        color: rgb(32, 144, 192);
        text-align: right;
        border - style: outset;
        border - radius: 2px;
        }    
    QLabel{
        background-color: transparent;
        }
    QCheckBox::indicator {
        border: 1px solid #404040;
        background-color: #101010;
        }
    QCheckBox::indicator:checked {
        background-color: rgb(32, 144, 192);
    }
    QDoubleSpinBox {
        background-color: #101010;
        color: rgb(32, 144, 192);
        text-align: right;
        border - style: outset;
        border - radius: 2px;
        font: 10pt;
        padding: 2 px;
        }
    QPushButton {
        background - color: #181818;
        border - style: outset;
        border - radius: 2px;
        font: 10pt;
        min - width: 10em;
        }
    QPushButton[running='true'] {
        background-color: rgb(16, 72, 124);
        color: #101010;
        } 
    QPushButton[running='false'] {
        background-color: #181818;
        color: #C0C0C0;
        }     
    QPushButton[cancel='true'] {
        background-color: rgb(96,0, 0);
        color: #101010;
        } 
    QPushButton[cancel='false'] {
        background-color: #181818;
        color: #C0C0C0;
        }
    QPushButton[iconset='true'] {
        text-align: left;
        padding-left: 6px;
        }
    QComboBox /* is the box itself */
    {  
        border-color: red;
        border-width: 5px;
        border-radius: 3px;
        border-style: solid;
        padding: 1px 0px 1px 3px;
    }
    QComboBox QListView /* is the list of popup */
    {   border-style: solid;
        border-color: #404040;
        border-width: 1px;
        border-radius: 3px;
        background-color: #181818;
    }
    QComboBox::drop-down /* is only the drop-down arrow surface */
    {   width: 20px;
        border: 1px;
        border-radius:3px;
        border-color: #404040;
        border-left-style:solid;
        border-top-style: none;
        border-bottom-style: none;
        border-right-style: none;
    }
    QComboBox::down-arrow /* is the arrow itself */
    {
        image: url(:/ArrowImages/images/whitearrowdown16.png);
        width: 16px;
        height: 16px;
    }

    """
    """


    QComboBox {
        background-color: #181818;
        border:1px solid #404040;
        border-radius:5px;
        padding:5px;
    }
    QComboBox::drop-down {
        width: 25px;
    }
    QComboBox QListView {
        border: 2px solid #404040;
        border - style: outset;
    QComboBox QAbstractItemView QListView::item:selected {
        background-color: red;
    }
    """
    """
    QComboBox::down-arrow, QSpinBox::down-arrow, QTimeEdit::down-arrow, QDateEdit::down-arrow{   
        image: url(:/icons/down_arrow.png);
        width: 7px;
        height: 5px;
    }
    """
    # define the tabbar main widget
    TAB_MAIN = """
    QTabBar::tab {
        background: gray;
        color: #101010;
        border: 3px solid #104450;
        border-bottom-color: #104450;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
        border-style: outset;
        min-width: 12ex;
        padding: 4px;
        padding-left: 4px;
        padding-right: 4px;
        margin-left: 1;
        margin-right: 1;
    }
    QTabBar::tab:selected {background: #2088C0;}
    QTabBar::tab:!selected {margin-top: 4px;}
    QTabBar::tab:selected {margin-left: 1px; margin-right: 1px;}
    QTabBar::tab:first:selected {margin-left: 2;}
    QTabBar::tab:last:selected {margin-right: 2;}
    QTabBar::tab:only-one {margin: 1;}
    """
    # make the settings tabbar the same look than the tabbar main
    TAB_SETTING = TAB_MAIN

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


