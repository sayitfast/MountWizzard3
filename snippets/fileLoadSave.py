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
import PyQt5


class MwFileDialogue(PyQt5.QtWidgets.QFileDialog):
    logger = logging.getLogger(__name__)

    def __init__(self, window):
        super().__init__()
        # set app icon
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(sys.modules['__main__'].__file__)
        self.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        self.setWindowIcon(PyQt5.QtGui.QIcon(bundle_dir + '\\icons\\mw.ico'))
        ph = window.geometry().height()
        px = window.geometry().x()
        py = window.geometry().y()
        dw = window.width()
        dh = window.height()
        self.setGeometry(px, py + ph - dh, dw, dh)
        self.setNameFilter("Data Files (*.dat)")
        self.setFileMode(PyQt5.QtWidgets.QFileDialog.AnyFile)
