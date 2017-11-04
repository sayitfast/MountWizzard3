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
import PyQt5
from win32com.client.dynamic import Dispatch
import pythoncom


class AscomEnvironment(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    signalAscomEnvironmentConnected = PyQt5.QtCore.pyqtSignal([int])

    CYCLE_DATA = 2000

    def __init__(self, app):
        super().__init__()
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()

        self.app = app
        self.data = {}
        self.ascom = None
        self.chooser = None
        self.driverName = ''
        self.initConfig()

    def initConfig(self):
        try:
            if 'AscomEnvironmentDriverName' in self.app.config:
                self.driverName = self.app.config['AscomEnvironmentDriverName']
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['AscomEnvironmentDriverName'] = self.driverName

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        if self.driverName != '':
            pythoncom.CoInitialize()
            try:
                self.ascom = Dispatch(self.driverName)
                self.ascom.connected = True
                self.signalAscomEnvironmentConnected.emit(3)
            except Exception as e:
                self.logger.error('Could not dispatch driver: {0} and connect it. Stopping thread.'.format(self.driverName))
            finally:
                pass
            # now starting all the tasks for cyclic doing (the ones which rely on QTimer)
            self.getData()
        else:
            self.signalAscomEnvironmentConnected.emit(0)
            self.stop()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        while self.isRunning:
            PyQt5.QtWidgets.QApplication.processEvents()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    # noinspection PyBroadException
    def getData(self):
        try:
            self.data['DewPoint'] = self.ascom.DewPoint
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['Temperature'] = self.ascom.Temperature
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['Humidity'] = self.ascom.Humidity
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['Pressure'] = self.ascom.Pressure
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['SQR'] = self.ascom.SkyQuality
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['CloudCover'] = self.ascom.CloudCover
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['RainRate'] = self.ascom.RainRate
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['WindSpeed'] = self.ascom.WindSpeed
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['WindDirection'] = self.ascom.WindDirection
        except Exception:
            pass
        finally:
            pass
        PyQt5.QtCore.QTimer.singleShot(self.CYCLE_DATA, self.getData)

    def setupDriver(self):
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'ObservingConditions'
            self.driverName = self.chooser.Choose(self.driverName)
            self.app.messageQueue.put('Driver chosen:{0}'.format(self.driverName))
            self.logger.info('Driver chosen:{0}'.format(self.driverName))
        except Exception as e:
            self.app.messageQueue.put('Driver error in Setup Driver')
            self.logger.error('General error:{0}'.format(e))
        finally:
            pass
