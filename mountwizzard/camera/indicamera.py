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
    CYCLEPROPS = 3000
    SOLVERSTATUS = {'ERROR': 'Error', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'BUSY', }
    CAMERASTATUS = {'ERROR': 'Error', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'DOWNLOADING', 'READY': 'IDLE', 'IDLE': 'IDLE', 'INTEGRATING': 'INTEGRATING'}

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {}

        self.cameraConnected = False
        self.data['CameraStatus'] = 'DISCONNECTED'
        self.solverConnected = False
        self.data['SolverStatus'] = 'DISCONNECTED'
        self.tryConnectionCounter = 0
        self.imagingStarted = False

        self.data['AppAvailable'] = True
        self.data['AppName'] = 'INDICamera'
        self.data['AppInstallPath'] = ''

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        self.getStatus()
        self.getCameraProps()
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

    def getStatus(self):
        if 'Camera' in self.app.workerINDI.data:
            if 'CONNECTION' in self.app.workerINDI.data['Camera']:
                if self.app.workerINDI.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                    self.cameraConnected = True
                else:
                    self.cameraConnected = False
                    self.data['CameraStatus'] = 'DISCONNECTED'
                if self.cameraConnected:
                    if float(self.app.workerINDI.data['Camera']['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE']):
                        self.data['CameraStatus'] = 'INTEGRATING'
                    else:
                        self.data['CameraStatus'] = 'READY - IDLE'
            else:
                self.data['CameraStatus'] = 'ERROR'
                self.cameraConnected = False

        self.cameraStatus.emit(self.data['CameraStatus'])

        if self.cameraConnected:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
        else:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(2)

        if self.solverConnected:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
        else:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(2)

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUS, self.getStatus)

    def getCameraProps(self):
        if self.cameraConnected:
            self.data['Gain'] = 0
            self.data['Gains'] = ['High']
            self.data['CanSubframe'] = True
            self.data['CameraXSize'] = self.app.workerINDI.data['Camera']['CCD_INFO']['CCD_MAX_X']
            self.data['CameraYSize'] = self.app.workerINDI.data['Camera']['CCD_INFO']['CCD_MAX_Y']

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLEPROPS, self.getCameraProps)

    def getImage(self, modelData):
        binning = int(float(modelData['Binning']))
        exposureLength = int(float(modelData['Exposure']))
        speed = modelData['Speed']
        filename = modelData['File']
        path = modelData['BaseDirImages']
        imagePath = path + '/' + filename
        self.app.workerINDI.imagePath = imagePath
        if self.cameraConnected:
            self.app.workerINDI.receivedImage = False
            # Enable BLOB mode.
            self.app.INDICommandQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.app.workerINDI.data['Camera']['DriverName']}))
            # set to raw - no compression mode
            self.app.INDICommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CCD_COMPRESS'})], indi_attr={'name': 'CCD_COMPRESSION', 'device': self.app.workerINDI.data['Camera']['DriverName']}))
            # set frame type
            self.app.INDICommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'FRAME_LIGHT'})], indi_attr={'name': 'CCD_FRAME_TYPE', 'device': self.app.workerINDI.data['Camera']['DriverName']}))
            # set binning
            self.app.INDICommandQueue.put(indiXML.newNumberVector([indiXML.oneNumber(binning, indi_attr={'name': 'HOR_BIN'}), indiXML.oneNumber(binning, indi_attr={'name': 'VER_BIN'})], indi_attr={'name': 'CCD_BINNING', 'device': self.app.workerINDI.data['Camera']['DriverName']}))
            # Request image.
            self.app.INDICommandQueue.put(indiXML.newNumberVector([indiXML.oneNumber(exposureLength, indi_attr={'name': 'CCD_EXPOSURE_VALUE'})], indi_attr={'name': 'CCD_EXPOSURE', 'device': self.app.workerINDI.data['Camera']['DriverName']}))
            self.imagingStarted = True
            while not self.app.workerINDI.receivedImage:
                time.sleep(0.1)
                PyQt5.QtWidgets.QApplication.processEvents()
        modelData['Imagepath'] = self.app.workerINDI.imagePath
        return True, 'OK', modelData

    def solveImage(self, modelData):
        suc, mes, guid = self.SgSolveImage(modelData['ImagePath'],
                                           scaleHint=modelData['ScaleHint'],
                                           blindSolve=modelData['Blind'],
                                           useFitsHeaders=modelData['UseFitsHeaders'])
        if not suc:
            self.logger.warning('no start {0}'.format(mes))
            return False, mes, modelData
        while True:
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SgGetSolvedImageData(guid)
            mes = mes.strip('\n')
            if mes[:7] in ['Matched', 'Solve t', 'Valid s', 'succeed']:
                self.logger.info('modelData {0}'.format(modelData))
                solved = True
                modelData['RaJ2000Solved'] = float(ra_sol)
                modelData['DecJ2000Solved'] = float(dec_sol)
                modelData['Scale'] = float(scale)
                modelData['Angle'] = float(angle)
                modelData['TimeTS'] = float(timeTS)
                break
            elif mes != 'Solving':
                solved = False
                break
            # TODO: clarification should we again introduce model run cancel during plate solving -> very complicated solver should cancel if not possible after some time
            # elif app.model.cancel:
            #    solved = False
            #    break
            else:
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
        return solved, mes, modelData

    def connectCamera(self):
        if self.appRunning and self.app.INDIworker.driverNameCCD != '':
            self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.INDIworker.driverNameCCD}))

    def disconnectCamera(self):
        if self.cameraConnected:
            self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.INDIworker.driverNameCCD}))

    def solveImage(self, modelData):
        pass
