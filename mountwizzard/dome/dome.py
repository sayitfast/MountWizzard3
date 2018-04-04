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
# Python  v3.6.4
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import platform
import PyQt5
import time
import indi.indi_xml as indiXML
if platform.system() == 'Windows':
    from win32com.client.dynamic import Dispatch
    import pythoncom
    from dome import ascom_dome
from dome import indi_dome
from dome import none_dome


class Dome(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalDomeConnected = PyQt5.QtCore.pyqtSignal([int])
    signalDomePointer = PyQt5.QtCore.pyqtSignal(float, bool)
    signalSlewFinished = PyQt5.QtCore.pyqtSignal()
    domeStatusText = PyQt5.QtCore.pyqtSignal(str)

    CYCLE_DATA = 1000
    CYCLE_STATUS = 1000
    START_DOME_TIMEOUT = 4

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexChooser = PyQt5.QtCore.QMutex()

        self.app = app
        self.thread = thread
        self.data = {
            'Connected': False,
            'Slewing': False
        }
        # get supporting handlers
        self.ascom = ascom_dome.AscomDome(self, self.app, self.data)
        self.indi = indi_dome.INDIDome(self, self.app, self.data)
        self.none = none_dome.NoneDome(self, self.app, self.data)
        # set handler to none
        self.domeHandler = self.none

        # connect change in dome to the subroutine of setting it up
        self.app.ui.pd_chooseDome.activated.connect(self.chooserDome)

    def initConfig(self):
        # first build the pull down menu
        self.app.ui.pd_chooseDome.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseDome.setView(view)
        self.app.ui.pd_chooseDome.addItem('No Dome')
        if platform.system() == 'Windows':
            self.app.ui.pd_chooseDome.addItem('ASCOM')
        self.app.ui.pd_chooseDome.addItem('INDI')
        # load the config including pull down setup
        try:
            if 'DomeAscomDriverName' in self.app.config:
                self.ascom.driverName = self.app.config['DomeAscomDriverName']
                self.app.ui.le_ascomDomeDriverName.setText(self.app.config['DomeAscomDriverName'])
            if 'Dome' in self.app.config:
                self.app.ui.pd_chooseDome.setCurrentIndex(int(self.app.config['Dome']))
        except Exception as e:
            self.logger.error('Item in config.cfg for dome could not be initialized, error:{0}'.format(e))
        finally:
            pass
        self.chooserDome()

    def storeConfig(self):
        self.app.config['DomeAscomDriverName'] = self.ascom.driverName
        self.app.config['Dome'] = self.app.ui.pd_chooseDome.currentIndex()

    def chooserDome(self):
        self.mutexChooser.lock()
        self.stop()
        self.data['Connected'] = False
        if self.app.ui.pd_chooseDome.currentText().startswith('No Dome'):
            self.domeHandler = self.none
            self.logger.info('Actual dome is None')
        elif self.app.ui.pd_chooseDome.currentText().startswith('ASCOM'):
            self.domeHandler = self.ascom
            self.logger.info('Actual dome is ASCOM')
        elif self.app.ui.pd_chooseDome.currentText().startswith('INDI'):
            self.domeHandler = self.indi
            self.logger.info('Actual dome is INDI')
        if self.app.ui.pd_chooseDome.currentText().startswith('No Dome'):
            self.signalDomeConnected.emit(0)
        self.thread.start()
        self.mutexChooser.unlock()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.domeHandler.start()
        self.getStatusFromDevice()
        self.getDataFromDevice()
        while self.isRunning:
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        self.domeHandler.stop()

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def getStatusFromDevice(self):
        self.domeHandler.getStatus()
        # get status to gui
        if not self.domeHandler.application['Available']:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_domeConnected, 'color', 'gray')
        elif self.domeHandler.application['Status'] == 'ERROR':
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_domeConnected, 'color', 'red')
        elif self.domeHandler.application['Status'] == 'OK':
            if self.data['Connected'] == 'Off':
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_domeConnected, 'color', 'yellow')
            else:
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_domeConnected, 'color', 'green')
        # loop
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS, self.getStatusFromDevice)

    def getDataFromDevice(self):
        if self.data['Connected']:
            self.domeHandler.getData()
        else:
            self.app.sharedDomeDataLock.lockForWrite()
            self.data['Slewing'] = False
            self.data['Azimuth'] = 0.0
            self.data['Altitude'] = 0.0
            self.app.sharedDomeDataLock.unlock()
        # signaling
        self.app.sharedDomeDataLock.lockForRead()
        if 'Azimuth' in self.data:
            self.signalDomePointer.emit(self.data['Azimuth'], self.data['Connected'])
        self.app.sharedDomeDataLock.unlock()
        # loop
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_DATA, self.getDataFromDevice)
