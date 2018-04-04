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
# if we are on windows, we have ascom
if platform.system() == 'Windows':
    from win32com.client.dynamic import Dispatch
    import pythoncom
    from environment import ascom_environment
# else we have the others
from environment import indi_environment
from environment import none_environment


class Environment(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalEnvironmentConnected = PyQt5.QtCore.pyqtSignal([int])

    CYCLE_DATA = 2000
    CYCLE_STATUS = 2000

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexChooser = PyQt5.QtCore.QMutex()
        self.app = app
        self.thread = thread
        self.dropDownBuildFinished = False
        self.data = {
            'Connected': False
        }
        # get supporting handlers
        self.ascom = ascom_environment.AscomEnvironment(self, self.app, self.data)
        self.indi = indi_environment.INDIEnvironment(self, self.app, self.data)
        self.none = none_environment.NoneEnvironment(self, self.app, self.data)
        # set handler to none
        self.environmentHandler = self.none

        self.movingAverageTemperature = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.movingAveragePressure = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # connect change in environment to the subroutine of setting it up
        self.app.ui.pd_chooseEnvironment.currentIndexChanged.connect(self.chooserEnvironment)

    def initConfig(self):
        # first build the pull down menu
        self.dropDownBuildFinished = False
        self.app.ui.pd_chooseEnvironment.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseEnvironment.setView(view)
        self.app.ui.pd_chooseEnvironment.addItem('No Environment')
        if platform.system() == 'Windows':
            self.app.ui.pd_chooseEnvironment.addItem('ASCOM')
        self.app.ui.pd_chooseEnvironment.addItem('INDI')
        self.dropDownBuildFinished = True
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

    def storeConfig(self):
        self.app.config['EnvironmentAscomDriverName'] = self.ascom.driverName
        self.app.config['Environment'] = self.app.ui.pd_chooseEnvironment.currentIndex()

    def chooserEnvironment(self):
        if not self.dropDownBuildFinished:
            return
        self.mutexChooser.lock()
        self.stop()
        if self.app.ui.pd_chooseEnvironment.currentText().startswith('No Environment'):
            self.environmentHandler = self.none
            self.logger.info('Actual environment is None')
        elif self.app.ui.pd_chooseEnvironment.currentText().startswith('ASCOM'):
            self.environmentHandler= self.ascom
            self.logger.info('Actual environment is ASCOM')
        elif self.app.ui.pd_chooseEnvironment.currentText().startswith('INDI'):
            self.environmentHandler = self.indi
            self.logger.info('Actual environment is INDI')
        if self.app.ui.pd_chooseEnvironment.currentText().startswith('No Environment'):
            self.signalEnvironmentConnected.emit(0)
        self.thread.start()
        self.mutexChooser.unlock()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        print('environ thread started')
        self.environmentHandler.start()
        self.getDataFromDevice()
        self.getStatusFromDevice()
        while self.isRunning:
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        print('environ loop stopped')
        self.environmentHandler.stop()
        print('environ stopped')

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            print('stop environ')
            self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def getStatusFromDevice(self):
        if not self.isRunning:
            return
        self.environmentHandler.getStatus()
        # get status to gui
        if not self.environmentHandler.application['Available']:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'gray')
        elif self.environmentHandler.application['Status'] == 'ERROR':
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'red')
        elif self.environmentHandler.application['Status'] == 'OK':
            if self.data['Connected'] == 'Off':
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'yellow')
            else:
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_environmentConnected, 'color', 'green')
        # loop
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS, self.getStatusFromDevice)

    def getDataFromDevice(self):
        if not self.isRunning:
            return
        if self.data['Connected']:
            self.environmentHandler.getData()
            # calculating moving average of temp and pressure for refraction
            self.movingAverageTemperature.append(self.data['Temperature'])
            self.movingAverageTemperature.pop(0)
            self.movingAveragePressure.append(self.data['Pressure'])
            self.movingAveragePressure.pop(0)
            self.app.sharedEnvironmentDataLock.lockForWrite()
            self.data['MovingAverageTemperature'] = sum(self.movingAverageTemperature) / len(self.movingAverageTemperature)
            self.data['MovingAveragePressure'] = sum(self.movingAveragePressure) / len(self.movingAveragePressure)
            self.app.sharedEnvironmentDataLock.unlock()
        else:
            self.app.sharedEnvironmentDataLock.lockForWrite()
            self.data = {
                'Connected': False,
                'DewPoint': 0.0,
                'Temperature': 0.0,
                'MovingAverageTemperature': 0.0,
                'Humidity': 0,
                'Pressure': 0,
                'MovingAveragePressure': 0,
                'CloudCover': 0,
                'RainRate': 0,
                'WindSpeed': 0,
                'WindDirection': 0,
                'SQR': 0
            }
            self.app.sharedEnvironmentDataLock.unlock()
        # loop
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_DATA, self.getDataFromDevice)
