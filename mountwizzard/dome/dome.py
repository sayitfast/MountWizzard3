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
import platform
import threading
import PyQt5
import time
from win32com.client.dynamic import Dispatch
import pythoncom


class Dome(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    signalDomeConnected = PyQt5.QtCore.pyqtSignal([int])
    signalDomePointer = PyQt5.QtCore.pyqtSignal(float)
    signalDomePointerVisibility = PyQt5.QtCore.pyqtSignal(bool)

    CYCLE_DATA = 500

    def __init__(self, app):
        super().__init__()
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()

        self.app = app
        self.data = {
            'Connected': False
        }
        self.ascom = None
        self.ascomChooser = None
        self.ascomDriverName = ''
        self.chooserLock = threading.Lock()

    def initConfig(self):
        # first build the pull down menu
        self.app.ui.pd_chooseDome.clear()
        self.app.ui.pd_chooseDome.addItem('No Dome')
        if platform.system() == 'Windows':
            self.app.ui.pd_chooseDome.addItem('ASCOM')
        self.app.ui.pd_chooseDome.addItem('INDI')
        # load the config including pull down setup
        try:
            if 'DomeAscomDriverName' in self.app.config:
                self.ascomDriverName = self.app.config['DomeAscomDriverName']
                self.app.ui.pd_chooseDome.setText(self.app.config['DomeAscomDriverName'])
            if 'Dome' in self.app.config:
                self.app.ui.pd_chooseDome.setCurrentIndex(int(self.app.config['Dome']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        # connect change in dome to the subroutine of setting it up
        self.app.ui.pd_chooseDome.currentIndexChanged.connect(self.chooserDome)

    def storeConfig(self):
        self.app.config['DomeAscomDriverName'] = self.ascomDriverName
        self.app.config['Dome'] = self.app.ui.pd_chooseDome.currentIndex()

    def startAscom(self):
        if self.ascomDriverName != '' and not self.ascom:
            try:
                self.ascom = Dispatch(self.ascomDriverName)
                self.ascom.connected = True
                self.logger.info('Driver chosen:{0}'.format(self.ascomDriverName))
            except Exception as e:
                self.logger.error('Could not dispatch driver: {0} and connect it'.format(self.ascomDriverName))
            finally:
                pass
            # connection made
            self.data['Connected'] = True
        else:
            # no connection made
            self.data['Connected'] = False

    def stopAscom(self):
        if self.ascom:
            self.ascom.connected = False
            self.ascom = None

    def chooserDome(self):
        self.chooserLock.acquire()
        if self.app.ui.pd_chooseDome.currentText().startswith('No Dome'):
            self.stopAscom()
            self.data['Connected'] = False
            self.logger.info('Actual dome is None')
        elif self.app.ui.pd_chooseDome.currentText().startswith('ASCOM'):
            self.startAscom()
            self.logger.info('Actual dome is ASCOM')
        elif self.app.ui.pd_chooseDome.currentText().startswith('INDI'):
            self.stopAscom()
            if self.app.workerINDI.isRunning:
                self.data['Connected'] = True
            else:
                self.data['Connected'] = False
            self.logger.info('Actual dome is INDI')
        if self.data['Connected']:
            self.signalDomeConnected.emit(3)
        else:
            self.signalDomeConnected.emit(1)
        self.signalDomePointerVisibility.emit(self.data['Connected'])
        self.chooserLock.release()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        if platform.system() == 'Windows':
            pythoncom.CoInitialize()
        self.chooserDome()
        self.getData()
        while self.isRunning:
            if self.data['Connected']:
                if not self.app.domeCommandQueue.empty():
                    command, value = self.app.domeCommandQueue.get()
                    if command == 'SlewAzimuth':
                        self.ascom.SlewToAzimuth(float(value))
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        if platform.system() == 'Windows':
            pythoncom.CoUninitialize()
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def getData(self):
        if self.data['Connected']:
            if self.app.ui.pd_chooseDome.currentText().startswith('ASCOM'):
                if self.ascom:
                    if self.ascom.connected:
                        self.getAscomData()
            elif self.app.ui.pd_chooseDome.currentText().startswith('INDI'):
                self.getINDIData()
        else:
            self.data = {
                'Connected': False,
                'Slewing': False,
                'Azimuth': 0.0,
                'Altitude': 0.0,
            }
        if 'Azimuth' in self.data:
            self.signalDomePointer.emit(self.data['Azimuth'])
        PyQt5.QtCore.QTimer.singleShot(self.CYCLE_DATA, self.getData)

    def getINDIData(self):
        pass

    def getAscomData(self):
        try:
            self.data['Slewing'] = self.ascom.Slewing
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['Azimuth'] = self.ascom.Azimuth
        except Exception:
            pass
        finally:
            pass
        try:
            self.data['Altitude'] = self.ascom.Altitude
        except Exception:
            pass
        finally:
            pass

    def setupDriver(self):
        try:
            self.ascomChooser = Dispatch('ASCOM.Utilities.Chooser')
            self.ascomChooser.DeviceType = 'Dome'
            self.ascomDriverName = self.ascomChooser.Choose(self.ascomDriverName)
            self.app.messageQueue.put('Driver chosen:{0}\n'.format(self.ascomDriverName))
            self.logger.info('Driver chosen:{0}'.format(self.ascomDriverName))
        except Exception as e:
            self.app.messageQueue.put('#BRDriver error in Setup Driver\n')
            self.logger.error('General error:{0}'.format(e))
        finally:
            pass
