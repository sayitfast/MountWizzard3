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
# standard solutions
import logging
from baseclasses import widget
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
        self.initConfig()

    def initConfig(self):
        try:
            if 'MessagePopupWindowPositionX' in self.app.config:
                self.move(self.app.config['MessagePopupWindowPositionX'], self.app.config['MessagePopupWindowPositionY'])
            if 'MessagePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['MessagePopupWindowShowStatus']
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['MessagePopupWindowPositionX'] = self.pos().x()
        self.app.config['MessagePopupWindowPositionY'] = self.pos().y()
        self.app.config['MessagePopupWindowShowStatus'] = self.showStatus

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.show()
