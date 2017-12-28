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
from baseclasses import widget
import PyQt5
from gui import message_dialog_ui


class MessageWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(MessageWindow, self).__init__()
        self.app = app
        self.showStatus = False
        self.ui = message_dialog_ui.Ui_MessageDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.setSizePolicy(PyQt5.QtWidgets.QSizePolicy.Fixed, PyQt5.QtWidgets.QSizePolicy.Ignored)
        self.setMinimumSize(790, 200)
        # self.setFixedSize(790)
        self.initConfig()

    def resizeEvent(self, QResizeEvent):
        # allow message window to be resized in height
        self.ui.messages.setGeometry(10, 10, 771, self.height() - 20)

    def initConfig(self):
        try:
            if 'MessagePopupWindowPositionX' in self.app.config:
                x = self.config['MessagePopupWindowPositionX']
                y = self.config['MessagePopupWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'MessagePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['MessagePopupWindowShowStatus']
            if 'MessagePopupWindowHeight' in self.app.config:
                self.resize(791, self.app.config['MessagePopupWindowHeight'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['MessagePopupWindowPositionX'] = self.pos().x()
        self.app.config['MessagePopupWindowPositionY'] = self.pos().y()
        self.app.config['MessagePopupWindowShowStatus'] = self.showStatus
        self.app.config['MessagePopupWindowHeight'] = self.height()

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.show()
