############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import logging
import PyQt5
import time
import indi.indi_xml as indiXML
from camera.cameraBase import MWCamera


class INDICamera(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()
    cameraStatus = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 200

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.data = {}
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        if 'Camera' not in self.data:
            self.data['Camera'] = {}
        if 'Solver' not in self.data:
            self.data['Solver'] = {}
        self.data['Camera']['Status'] = 'DISCONNECTED'
        self.data['Camera']['CanSubframe'] = False
        self.data['Solver']['Status'] = 'DISCONNECTED'
        self.data['Camera']['Gains'] = 'Not Selected'
        self.data['Camera']['Gain'] = 0

        self.cameraConnected = False
        self.solverConnected = False
        self.tryConnectionCounter = 0
        self.imagingStarted = False

        self.data['AppAvailable'] = True
        self.data['AppName'] = 'INDICamera'
        self.data['AppInstallPath'] = ''

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        self.setStatus()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        while self.isRunning:
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def setStatus(self):
        if self.app.workerINDI.cameraDevice != '':
            self.data['Camera'].update(self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice])
            if 'CONNECTION' in self.data['Camera']:
                if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                    if float(self.data['Camera']['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE']):
                        self.data['Camera']['Status'] = 'INTEGRATING'
                    else:
                        self.data['Camera']['Status'] = 'IDLE'
                    self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
                else:
                    self.app.workerModelingDispatcher.signalStatusCamera.emit(2)
                    self.data['Camera']['Status'] = 'DISCONNECTED'
            else:
                self.data['Camera']['Status'] = 'ERROR'
            if 'CCD_EXPOSURE' in self.data['Camera']:
                self.cameraStatus.emit(self.data['Camera']['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'])
        else:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(0)

        if 'CONNECTION' in self.data['Solver']:
            if self.data['Solver']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusSolver.emit(2)
        else:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(0)

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUS, self.setStatus)

    def getImage(self, imageParams):
        binning = int(float(imageParams['Binning']))
        exposureLength = int(float(imageParams['Exposure']))
        speed = imageParams['Speed']
        filename = imageParams['File']
        path = imageParams['BaseDirImages']
        imagePath = path + '/' + filename
        self.app.workerINDI.imagePath = imagePath
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                self.app.workerINDI.receivedImage = False
                # Enable BLOB mode.
                self.app.INDICommandQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.app.workerINDI.cameraDevice}))
                # set to raw - no compression mode
                self.app.INDICommandQueue.put(
                    indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CCD_COMPRESSED'})],
                                            indi_attr={'name': 'CCD_COMPRESSION', 'device': self.app.workerINDI.cameraDevice}))
                # set frame type
                self.app.INDICommandQueue.put(
                    indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'FRAME_LIGHT'})],
                                            indi_attr={'name': 'CCD_FRAME_TYPE', 'device': self.app.workerINDI.cameraDevice}))
                # set binning
                self.app.INDICommandQueue.put(
                    indiXML.newNumberVector([indiXML.oneNumber(binning, indi_attr={'name': 'HOR_BIN'}), indiXML.oneNumber(binning, indi_attr={'name': 'VER_BIN'})],
                                            indi_attr={'name': 'CCD_BINNING', 'device': self.app.workerINDI.cameraDevice}))
                # Request image.
                self.app.INDICommandQueue.put(
                    indiXML.newNumberVector([indiXML.oneNumber(exposureLength, indi_attr={'name': 'CCD_EXPOSURE_VALUE'})],
                                            indi_attr={'name': 'CCD_EXPOSURE', 'device': self.app.workerINDI.cameraDevice}))

                self.imagingStarted = True
                while not self.app.workerINDI.receivedImage:
                    time.sleep(1)
                    PyQt5.QtWidgets.QApplication.processEvents()
            imageParams['Imagepath'] = self.app.workerINDI.imagePath
            imageParams['Success'] = True
            imageParams['Message'] = 'OK'
        else:
            imageParams['Imagepath'] = ''
            imageParams['Success'] = False
            imageParams['Message'] = 'No Picture Taken'
        return imageParams

    def solveImage(self, imageParams):
        return imageParams

    def connectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
           if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'Off':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))

    def disconnectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))
