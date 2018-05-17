############################################################
# -*- coding: utf-8 -*-
#
#       #   #  #   #   #  ####
#      ##  ##  #  ##  #     #
#     # # # #  # # # #     ###
#    #  ##  #  ##  ##        #
#   #   #   #  #   #     ####
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import PyQt5
from baseclasses import widget
from gui import message_window_ui


class MessageWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(MessageWindow, self).__init__()
        self.app = app
        self.showStatus = False
        self.ui = message_window_ui.Ui_MessageDialog()
        self.ui.setupUi(self)
        self.initUI()
        # allow sizing of the window
        self.setFixedSize(PyQt5.QtCore.QSize(16777215, 16777215))
        # self.setSizePolicy(PyQt5.QtWidgets.QSizePolicy.Pref, PyQt5.QtWidgets.QSizePolicy.Ignored)
        self.setMinimumSize(790, 200)
        self.setMaximumSize(790, 16777215)
        self.initConfig()

    def resizeEvent(self, QResizeEvent):
        # allow message window to be resized in height
        self.ui.messages.setGeometry(10, 10, 771, self.height() - 20)

    def initConfig(self):
        try:
            if 'MessageWindowPositionX' in self.app.config:
                x = self.app.config['MessageWindowPositionX']
                y = self.app.config['MessageWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'MessageWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['MessageWindowShowStatus']
            if 'MessageWindowHeight' in self.app.config:
                self.resize(791, self.app.config['MessageWindowHeight'])
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for messages window, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['MessageWindowPositionX'] = self.pos().x()
        self.app.config['MessageWindowPositionY'] = self.pos().y()
        self.app.config['MessageWindowShowStatus'] = self.showStatus
        self.app.config['MessageWindowHeight'] = self.height()

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.show()
