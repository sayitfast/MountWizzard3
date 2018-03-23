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
if platform.system() == 'Windows':
    from win32com.client.dynamic import Dispatch
    import pythoncom


class Environment(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalEnvironmentConnected = PyQt5.QtCore.pyqtSignal([int])

    CYCLE_DATA = 2000

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexChooser = PyQt5.QtCore.QMutex()
        self.app = app
        self.thread = thread
        self.data = {
            'Connected': False
        }
        self.movingAverageTemperature = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.movingAveragePressure = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.ascom = None
        self.ascomChooser = None
        self.ascomDriverName = ''
        # connect change in environment to the subroutine of setting it up
        self.app.ui.pd_chooseEnvironment.currentIndexChanged.connect(self.chooserEnvironment)

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
            if 'EnvironmentAscomDriverName' in self.app.config:
                self.ascomDriverName = self.app.config['EnvironmentAscomDriverName']
                self.app.ui.le_ascomEnvironmentDriverName.setText(self.app.config['EnvironmentAscomDriverName'])
            if 'Environment' in self.app.config:
                self.app.ui.pd_chooseEnvironment.setCurrentIndex(int(self.app.config['Environment']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['EnvironmentAscomDriverName'] = self.ascomDriverName
        self.app.config['Environment'] = self.app.ui.pd_chooseEnvironment.currentIndex()

    def startAscom(self):
        if self.ascomDriverName != '' and self.ascom is None:
            try:
                self.ascom = Dispatch(self.ascomDriverName)
                self.ascom.connected = True
                self.logger.info('Driver chosen:{0}'.format(self.ascomDriverName))
                # connection made
                self.data['Connected'] = True
            except Exception as e:
                self.logger.error('Could not dispatch driver: {0} and connect it, error: {1}'.format(self.ascomDriverName, e))
            finally:
                pass
        elif self.ascomDriverName == '':
            # no connection made
            self.data['Connected'] = False

    def stopAscom(self):
        try:
            if self.ascom:
                self.ascom.connected = False
        except Exception as e:
            self.logger.error('Could not stop driver: {0} and close it, error: {1}'.format(self.ascomDriverName, e))
        finally:
            self.data['Connected'] = False
            self.ascom = None

    def chooserEnvironment(self):
        self.mutexChooser.lock()
        if self.app.ui.pd_chooseEnvironment.currentText().startswith('No Environment'):
            self.stopAscom()
            self.data['Connected'] = False
            self.logger.info('Actual environment is None')
        elif self.app.ui.pd_chooseEnvironment.currentText().startswith('ASCOM'):
            self.startAscom()
            self.logger.info('Actual environment is ASCOM')
        elif self.app.ui.pd_chooseEnvironment.currentText().startswith('INDI'):
            self.stopAscom()
            if self.app.workerINDI.environmentDevice != '':
                self.data['Connected'] = self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['CONNECTION']['CONNECT'] == 'On'
            else:
                self.data['Connected'] = False
            self.logger.info('Actual environment is INDI')
        if self.app.ui.pd_chooseEnvironment.currentText().startswith('No Environment'):
            self.signalEnvironmentConnected.emit(0)
        self.mutexChooser.unlock()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        if platform.system() == 'Windows':
            pythoncom.CoInitialize()
        self.chooserEnvironment()
        self.getData()
        while self.isRunning:
            if self.app.ui.pd_chooseEnvironment.currentText().startswith('INDI'):
                if self.app.workerINDI.environmentDevice != '' and self.app.workerINDI.environmentDevice in self.app.workerINDI.data['Device']:
                    self.data['Connected'] = self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['CONNECTION']['CONNECT'] == 'On'
                else:
                    self.data['Connected'] = False
            if self.data['Connected']:
                self.signalEnvironmentConnected.emit(3)
            else:
                if self.app.ui.pd_chooseEnvironment.currentText().startswith('No Environment'):
                    self.signalEnvironmentConnected.emit(0)
                else:
                    if self.app.ui.pd_chooseEnvironment.currentText().startswith('INDI') and self.app.workerINDI.environmentDevice != '':
                        self.signalEnvironmentConnected.emit(2)
                    else:
                        self.signalEnvironmentConnected.emit(1)
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.stopAscom()
        if platform.system() == 'Windows':
            pythoncom.CoUninitialize()
        self.thread.quit()
        self.thread.wait()

    def getData(self):
        if self.data['Connected']:
            if self.app.ui.pd_chooseEnvironment.currentText().startswith('ASCOM'):
                try:
                    if self.ascom:
                        if self.ascom.connected:
                            self.getAscomData()
                except Exception as e:
                    self.logger.error('Problem accessing ASCOm driver, error: {0}'.format(e))
                finally:
                    pass
            elif self.app.ui.pd_chooseEnvironment.currentText().startswith('INDI'):
                if self.app.workerINDI.data['Connected']:
                    self.getINDIData()
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
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_DATA, self.getData)

    def getINDIData(self):
        # check if client has device found
        if self.app.workerINDI.environmentDevice != '':
            # and device is connected
            if self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['CONNECTION']['CONNECT'] == 'On':
                # than get the data
                self.app.sharedEnvironmentDataLock.lockForWrite()
                self.data['DewPoint'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_DEWPOINT'])
                self.data['Temperature'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_TEMPERATURE'])
                self.data['Humidity'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_HUMIDITY'])
                self.data['Pressure'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_BAROMETER'])
                self.app.sharedEnvironmentDataLock.unlock()

    # noinspection PyBroadException
    def getAscomData(self):
        self.app.sharedEnvironmentDataLock.lockForWrite()
        try:
            self.data['DewPoint'] = self.ascom.DewPoint
        finally:
            pass
        try:
            self.data['Temperature'] = self.ascom.Temperature
        finally:
            pass
        try:
            self.data['Humidity'] = self.ascom.Humidity
        finally:
            pass
        try:
            self.data['Pressure'] = self.ascom.Pressure
        finally:
            pass
        try:
            self.data['SQR'] = self.ascom.SkyQuality
        finally:
            pass
        try:
            self.data['CloudCover'] = self.ascom.CloudCover
        finally:
            pass
        try:
            self.data['RainRate'] = self.ascom.RainRate
        finally:
            pass
        try:
            self.data['WindSpeed'] = self.ascom.WindSpeed
        finally:
            pass
        try:
            self.data['WindDirection'] = self.ascom.WindDirection
        finally:
            pass
        self.app.sharedEnvironmentDataLock.unlock()

    def setupDriver(self):
        try:
            self.ascomChooser = Dispatch('ASCOM.Utilities.Chooser')
            self.ascomChooser.DeviceType = 'ObservingConditions'
            self.ascomDriverName = self.ascomChooser.Choose(self.ascomDriverName)
            self.app.messageQueue.put('Driver chosen:{0}\n'.format(self.ascomDriverName))
            self.logger.info('Driver chosen:{0}'.format(self.ascomDriverName))
        except Exception as e:
            self.app.messageQueue.put('#BRDriver error in Setup Driver\n')
            self.logger.error('General error:{0}'.format(e))
        finally:
            pass
