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
from astrometry import astrometryClient


class INDICamera(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    cameraStatusText = PyQt5.QtCore.pyqtSignal(str)
    solverStatusText = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 200
    CYCLE_MAIN_LOOP = 200

    def __init__(self, app, thread, commandQueue):
        super().__init__()
        self.app = app
        self.thread = thread
        self.commandQueue = commandQueue
        self.data = {}
        self.solver = astrometryClient.AstrometryClient(self, self.app)
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()

        self.cancel = False
        self.counter = 0
        self.receivedImage = True
        self.imagingStarted = False

        if 'Camera' not in self.data:
            self.data['Camera'] = {}
        if 'Solver' not in self.data:
            self.data['Solver'] = {}
        self.data['Camera']['Status'] = 'DISCONNECTED'
        self.data['Solver']['Status'] = 'DISCONNECTED'
        self.data['Camera']['CONNECTION'] = {'CONNECT': 'Off'}
        self.data['Solver']['CONNECTION'] = {'CONNECT': 'Off'}
        self.data['Camera']['AppAvailable'] = True
        self.data['Camera']['AppName'] = 'INDICamera'
        self.data['Camera']['AppInstallPath'] = ''
        self.data['Solver']['AppAvailable'] = False
        self.data['Solver']['AppName'] = 'ANSRV'
        self.data['Solver']['AppInstallPath'] = ''

        self.app.workerINDI.receivedImage.connect(lambda: self.setReceivedImage())

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.setStatus()
        self.mainLoop()

    def mainLoop(self):
        if not self.commandQueue.empty():
            command = self.commandQueue.get()
            if command['Command'] == 'GetImage':
                command['ImageParams'] = self.getImage(command['ImageParams'])
            elif command['Command'] == 'SolveImage':
                command['ImageParams'] = self.solveImage(command['ImageParams'])
        self.mutexIsRunning.lock()
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_MAIN_LOOP, self.mainLoop)
        self.mutexIsRunning.unlock()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def setReceivedImage(self):
        self.receivedImage = True

    def setStatus(self):
        # check if INDIClient is running and camera device is there
        if self.app.workerINDI.isRunning and self.app.workerINDI.cameraDevice != '':
            self.data['Camera'].update(self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice])
            if 'CONNECTION' and 'CCD_EXPOSURE' in self.data['Camera']:
                if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                    if self.data['Camera']['CCD_EXPOSURE']['state'] in ['Busy']:
                        if float(self.data['Camera']['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE']):
                            self.data['Camera']['Status'] = 'INTEGRATING'
                            self.cameraStatusText.emit('INTEGRATE')
                        else:
                            self.data['Camera']['Status'] = 'DOWNLOADING'
                            self.cameraStatusText.emit('DOWNLOAD')
                    elif self.data['Camera']['CCD_EXPOSURE']['state'] in ['Ok', 'Idle']:
                        if not self.receivedImage:
                            self.data['Camera']['Status'] = 'INTEGRATING'
                            self.cameraStatusText.emit('INTEGRATE')
                        else:
                            self.data['Camera']['Status'] = 'IDLE'
                            self.cameraStatusText.emit('IDLE')

                    elif self.data['Camera']['CCD_EXPOSURE']['state'] == 'Error':
                        self.data['Camera']['Status'] = 'ERROR'
                        self.cameraStatusText.emit('ERROR')

                    self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
                else:
                    self.app.workerModelingDispatcher.signalStatusCamera.emit(2)
                    self.data['Camera']['Status'] = 'DISCONNECTED'
            else:
                self.data['Camera']['Status'] = 'ERROR'

            if 'CCD_EXPOSURE' in self.data['Camera']:
                self.cameraExposureTime.emit('{0:02.0f}'.format(float(self.data['Camera']['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'])))
        else:
            self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'
            self.app.workerModelingDispatcher.signalStatusCamera.emit(1)
            self.cameraStatusText.emit('---')
            self.cameraExposureTime.emit('---')

        # reduced status speed for astrometry
        self.counter += 1
        if self.counter % 5 == 0:
            if self.app.ui.checkEnableAstrometry.isChecked():
                self.data['Solver']['Status'] = self.solver.checkAstrometryServerRunning()
                if self.data['Solver']['Status'] == 2:
                    self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
                    self.solverStatusText.emit('IDLE')
                    self.data['Solver']['CONNECTION']['CONNECT'] = 'On'
                elif self.data['Solver']['Status'] == 1:
                    self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
                    self.solverStatusText.emit('SOLVE')
                    self.data['Solver']['CONNECTION']['CONNECT'] = 'On'
                elif self.data['Solver']['Status'] == 0:
                    self.app.workerModelingDispatcher.signalStatusSolver.emit(1)
                    self.solverStatusText.emit('DISCONN')
                    self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'
            else:
                self.app.workerModelingDispatcher.signalStatusSolver.emit(0)
                self.solverStatusText.emit('---')
                self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'

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
        self.cancel = False
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                # Enable BLOB mode.
                self.app.INDICommandQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.app.workerINDI.cameraDevice}))
                # set to raw - no compression mode
                self.app.INDICommandQueue.put(
                    indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CCD_COMPRESS'})],
                                            indi_attr={'name': 'CCD_COMPRESSION', 'device': self.app.workerINDI.cameraDevice}))
                # set frame type
                self.app.INDICommandQueue.put(
                    indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'FRAME_LIGHT'})],
                                            indi_attr={'name': 'CCD_FRAME_TYPE', 'device': self.app.workerINDI.cameraDevice}))
                # set binning
                self.app.INDICommandQueue.put(
                    indiXML.newNumberVector([indiXML.oneNumber(binning, indi_attr={'name': 'HOR_BIN'}), indiXML.oneNumber(binning, indi_attr={'name': 'VER_BIN'})],
                                            indi_attr={'name': 'CCD_BINNING', 'device': self.app.workerINDI.cameraDevice}))
                # set gain (necessary) ?
                # todo: implement gain setting
                # Request image.
                self.app.INDICommandQueue.put(
                    indiXML.newNumberVector([indiXML.oneNumber(exposureLength, indi_attr={'name': 'CCD_EXPOSURE_VALUE'})],
                                            indi_attr={'name': 'CCD_EXPOSURE', 'device': self.app.workerINDI.cameraDevice}))
                self.receivedImage = False
                # todo: transfer between indi subsystem and camera has to be with signals an to be interruptable
                while not self.receivedImage and self.app.workerModelingDispatcher.isRunning and not self.cancel:
                    time.sleep(0.1)
                    PyQt5.QtWidgets.QApplication.processEvents()
            imageParams['Imagepath'] = self.app.workerINDI.imagePath
            imageParams['Message'] = 'OK'
        else:
            imageParams['Imagepath'] = ''
            imageParams['Message'] = 'No Picture Taken'
        return imageParams

    def solveImage(self, imageParams):
        if 'Imagepath' not in imageParams:
            return imageParams
        if self.app.ui.checkEnableAstrometry.isChecked():
            if not self.solver.isSolving:
                result = self.solver.solveImage(imageParams['Imagepath'], imageParams['RaJ2000'], imageParams['DecJ2000'], imageParams['ScaleHint'])
                if result:
                    if result['Message'] == 'Solve OK':
                        imageParams['RaJ2000Solved'] = result['ra'] * 24 / 360
                        imageParams['DecJ2000Solved'] = result['dec']
                        imageParams['Angle'] = result['orientation']
                        imageParams['Scale'] = result['pixscale']
                    imageParams['Message'] = result['Message']
                else:
                    imageParams['Message'] = 'Solve aborted'
            else:
                imageParams['Message'] = 'Solve failed because other solving process is still running'
                self.logger.error('There is a solving process already running')
        else:
            self.logger.error('Astrometry is disabled')
        return imageParams

    def connectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'Off':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))

    def disconnectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))
