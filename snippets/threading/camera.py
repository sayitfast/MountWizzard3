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
from PyQt5 import QtCore, QtWidgets
import sys
import time

import numpy
import pyfits
# import .NET / COM Handling
from win32com.client import Dispatch
import pythoncom


class Camera(QtCore.QObject):
    logger = logging.getLogger(__name__)
    finishedSignal = QtCore.pyqtSignal()
    exposeSignal = QtCore.pyqtSignal(object)
    statusSignal = QtCore.pyqtSignal(str)

    CYCLE_PROPS = 500

    def __init__(self):
        super().__init__()
        self.connected = False
        # self.driverName = 'QSICamera.CCDCamera'
        self.driverName = 'ASCOM.Simulator.Camera'

        self.ascom = None
        self.status = ''
        self.props = {}
        self.isRunning = False
        self._mutex = QtCore.QMutex()

    def run(self):
        if self.driverName != '':
            if not self.isRunning:
                self.isRunning = True
                pythoncom.CoInitialize()
                try:
                    self.ascom = Dispatch(self.driverName)
                    self.ascom.connected = True
                except Exception as e:
                    # self.logger.error('Could not dispatch driver: {0} and connect it. Stopping thread.'.format(self.driverName))
                    print('could not dispatch', e)
                finally:
                    pass
                # now starting all the tasks for cyclic doing
                self.getProps()
        while self.isRunning:
            QtWidgets.QApplication.processEvents()
        self.finishedSignal.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def getProps(self):
        if self.isRunning:
            print('stat')
            self.props['CameraState'] = self.ascom.CameraState
            self.props['CameraXSize'] = self.ascom.CameraXSize
            self.props['CameraYSize'] = self.ascom.CameraYSize
            '''
            self.props['CanAbortExposure'] = self.ascom.CanAbortExposure
            self.props['CanFastReadout'] = self.ascom.CanFastReadout
            self.props['CanStopExposure'] = self.ascom.CanStopExposure
            self.props['CanGetCoolerPower'] = self.ascom.CanGetCoolerPower
            self.props['CCDTemperature'] = self.ascom.CCDTemperature
            self.props['Gain'] = self.ascom.Gain
            self.props['Gains'] = self.ascom.Gains
            self.props['InterfaceVersion'] = self.ascom.InterfaceVersion
            self.props['MaxBinX'] = self.ascom.MaxBinX
            self.props['MaxBinY'] = self.ascom.MaxBinY
            self.props['PixelSizeX'] = self.ascom.PixelSizeX
            self.props['PixelSizeY'] = self.ascom.PixelSizeY
            self.props['ReadoutMode'] = self.ascom.ReadoutMode
            self.props['ReadoutModes'] = self.ascom.ReadoutModes
            '''
            if self.props['CameraState'] in [0]:
                self.statusSignal.emit('IDLE')
            elif self.props['CameraState'] in [1, 2, 3]:
                self.statusSignal.emit('INTEGRATING')
            elif self.props['CameraState'] in [4]:
                self.statusSignal.emit('DOWNLOADING')
            else:
                self.statusSignal.emit('ERROR')
            QtCore.QTimer.singleShot(self.CYCLE_PROPS, self.getProps)

    def expose(self):
        if self.isRunning:
            try:
                self.ascom.BinX = 1
                self.ascom.BinY = 1
                self.ascom.NumX = 3388
                self.ascom.NumY = 2712
                self.ascom.StartX = 0
                self.ascom.StartY = 0
                # self.ascomCamera.Gains = modelData['gainValue']
                if self.ascom.CameraState == 0:
                    print('exposing', QtCore.QThread.currentThread())
                    self.ascom.StartExposure(3, True)
                else:
                    print('no exposure possible')
                    return
                while not self.ascom.ImageReady:
                    QtWidgets.QApplication.processEvents()
                print('exposing finished')
                # self.ascomCamera.ReadoutModes = modelData['speed']
                '''
                image = numpy.rot90(numpy.array(self.ascomCamera.ImageArray))
                image = numpy.flipud(image)
                hdu = pyfits.PrimaryHDU(image)
                imageData['imagepath'] = imageData['base_dir_images'] + '/' + imageData['file']
                hdu.writeto(imageData['imagepath'])
                '''
            except Exception as e:
                print(e)

    def setupDriverCamera(self):
        try:
            chooser = Dispatch('ASCOM.Utilities.Chooser')
            chooser.DeviceType = 'Camera'
            driverName = chooser.Choose('')
            print(driverName)
            self.connected = False
        except Exception as e:
            pass
        finally:
            pass


if __name__ == "__main__":

    class Widget(QtWidgets.QWidget):

        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            self.button = QtWidgets.QPushButton('Stop', self)

            self.buttonE = QtWidgets.QPushButton('Expose', self)
            self.state = QtWidgets.QPushButton('State', self)
            layout = QtWidgets.QVBoxLayout(self)
            layout.addWidget(self.button)
            layout.addWidget(self.buttonE)
            layout.addWidget(self.state)

            self.worker = Camera()
            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finishedSignal.connect(self.stopWorker)
            self.thread.start()
            self.button.clicked.connect(self.worker.stop)
            # self.worker.expose tuns in context of the new thread
            self.buttonE.clicked.connect(self.worker.expose)
            self.worker.statusSignal.connect(self.status)

        def status(self, wert):
            self.state.setText(str(wert))

        def stopWorker(self):
            self.thread.quit()
            self.thread.wait()

    app = QtWidgets.QApplication(sys.argv)
    widget = Widget()
    widget.show()
    widget.worker.stop()
    for i in range(0, 100):
        print(i)
        widget.thread.start()
        time.sleep(0.1)
        widget.worker.stop()

    while widget.worker.isRunning:
        QtWidgets.QApplication.processEvents()

    sys.exit(app.exec_())
