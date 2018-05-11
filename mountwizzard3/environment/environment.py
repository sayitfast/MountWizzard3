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
import platform
import PyQt5
import time
# if we are on windows, we have ascom
if platform.system() == 'Windows':
    from environment import ascom_environment
# else we have the others
from environment import indi_environment
from environment import none_environment


class Environment(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalEnvironmentConnected = PyQt5.QtCore.pyqtSignal([int])
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    CYCLE = 200
    CYCLE_STATUS = 500
    CYCLE_DATA = 1000

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexChooser = PyQt5.QtCore.QMutex()
        self.dataTimer = None
        self.statusTimer = None
        self.cycleTimer = None

        self.app = app
        self.thread = thread
        self.data = {
            'Connected': False
        }
        # get supporting handlers
        if platform.system() == 'Windows':
            self.ascom = ascom_environment.AscomEnvironment(self, self.app, self.data)
        self.indi = indi_environment.INDIEnvironment(self, self.app, self.data)
        self.none = none_environment.NoneEnvironment(self, self.app, self.data)
        # set handler to none
        self.environmentHandler = self.none
        # setting default for moving average filtering
        self.movingAverageTemperature = [0] * 30
        self.movingAveragePressure = [0] * 30
        # connect change in environment to the subroutine of setting it up
        self.app.ui.pd_chooseEnvironment.activated.connect(self.chooserEnvironment)

    def initConfig(self):
        # first build the pull down menu
        self.app.ui.pd_chooseEnvironment.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseEnvironment.setView(view)
        self.app.ui.pd_chooseEnvironment.addItem('No Environment')
        if platform.system() == 'Windows':
            self.app.ui.pd_chooseEnvironment.addItem('ASCOM')
        self.app.ui.pd_chooseEnvironment.addItem('INDI')
        # load the config including pull down setup
        try:
            if platform.system() == 'Windows':
                if 'EnvironmentAscomDriverName' in self.app.config:
                    self.ascom.driverName = self.app.config['EnvironmentAscomDriverName']
                    self.app.ui.le_ascomEnvironmentDriverName.setText(self.app.config['EnvironmentAscomDriverName'])
            if 'Environment' in self.app.config:
                self.app.ui.pd_chooseEnvironment.setCurrentIndex(int(self.app.config['Environment']))
        except Exception as e:
            self.logger.error('Item in config.cfg for environment could not be initialized, error:{0}'.format(e))
        finally:
            pass
        self.chooserEnvironment()

    def storeConfig(self):
        if platform.system() == 'Windows':
            self.app.config['EnvironmentAscomDriverName'] = self.ascom.driverName
        self.app.config['Environment'] = self.app.ui.pd_chooseEnvironment.currentIndex()

    def chooserEnvironment(self):
        self.mutexChooser.lock()
        self.stop()
        self.app.sharedEnvironmentDataLock.lockForWrite()
        self.data['Connected'] = False
        self.app.sharedEnvironmentDataLock.unlock()
        if self.app.ui.pd_chooseEnvironment.currentText().startswith('No Environment'):
            self.environmentHandler = self.none
            self.logger.info('Actual environment is None')
        elif self.app.ui.pd_chooseEnvironment.currentText().startswith('ASCOM'):
            self.environmentHandler = self.ascom
            self.logger.info('Actual environment is ASCOM')
        elif self.app.ui.pd_chooseEnvironment.currentText().startswith('INDI'):
            self.environmentHandler = self.indi
            self.logger.info('Actual environment is INDI')
        if self.app.ui.pd_chooseEnvironment.currentText().startswith('No Environment'):
            self.signalEnvironmentConnected.emit(0)
        self.thread.start()
        self.mutexChooser.unlock()

    def run(self):
        self.logger.info('environment started')
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.environmentHandler.start()
        self.signalDestruct.connect(self.destruct, type=PyQt5.QtCore.Qt.BlockingQueuedConnection)
        # timers
        self.statusTimer = PyQt5.QtCore.QTimer(self)
        self.statusTimer.setSingleShot(False)
        self.statusTimer.timeout.connect(self.getStatusFromDevice)
        self.dataTimer = PyQt5.QtCore.QTimer(self)
        self.dataTimer.setSingleShot(False)
        self.dataTimer.timeout.connect(self.getDataFromDevice)
        self.statusTimer.start(self.CYCLE_STATUS)
        self.dataTimer.start(self.CYCLE_STATUS)
        self.cycleTimer = PyQt5.QtCore.QTimer(self)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.doCommand)
        self.cycleTimer.start(self.CYCLE)

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.signalDestruct.emit()
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('environment stopped')

    def doCommand(self):
        pass

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.signalDestruct.connect(self.destruct)
        self.cycleTimer.stop()
        self.dataTimer.stop()
        self.statusTimer.stop()
        self.environmentHandler.stop()

    @PyQt5.QtCore.pyqtSlot()
    def getStatusFromDevice(self):
        self.environmentHandler.getStatus()
        # get status to gui
        if not self.environmentHandler.application['Available']:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'gray')
        elif self.environmentHandler.application['Status'] == 'ERROR':
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'red')
        elif self.environmentHandler.application['Status'] == 'OK':
            self.app.sharedEnvironmentDataLock.lockForRead()
            connected = self.data['Connected']
            self.app.sharedEnvironmentDataLock.unlock()
            if not connected:
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'yellow')
            else:
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'green')

    @PyQt5.QtCore.pyqtSlot()
    def getDataFromDevice(self):
        self.app.sharedEnvironmentDataLock.lockForRead()
        connected = self.data['Connected']
        self.app.sharedEnvironmentDataLock.unlock()
        if connected:
            self.environmentHandler.getData()
            # calculating moving average of temp and pressure for refraction
            self.app.sharedEnvironmentDataLock.lockForWrite()
            self.movingAverageTemperature.append(self.data['Temperature'])
            self.movingAverageTemperature.pop(0)
            self.movingAveragePressure.append(self.data['Pressure'])
            self.movingAveragePressure.pop(0)
            self.data['MovingAverageTemperature'] = sum(self.movingAverageTemperature) / len(self.movingAverageTemperature)
            self.data['MovingAveragePressure'] = sum(self.movingAveragePressure) / len(self.movingAveragePressure)
            self.app.sharedEnvironmentDataLock.unlock()
        else:
            self.app.sharedEnvironmentDataLock.lockForWrite()
            self.data['DewPoint'] = 0.0
            self.data['Temperature'] = 0.0
            self.data['MovingAverageTemperature'] = 0.0
            self.data['Pressure'] = 0.0
            self.data['MovingAveragePressure'] = 0.0
            self.data['Humidity'] = 0.0
            self.data['CloudCover'] = 0.0
            self.data['RainRate'] = 0.0
            self.data['WindSpeed'] = 0.0
            self.data['WindDirection'] = 0.0
            self.data['SQR'] = 0.0
            self.app.sharedEnvironmentDataLock.unlock()
