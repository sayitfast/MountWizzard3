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
import time
import PyQt5
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch
import pythoncom


class MaximDLCamera(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()
    cameraStatus = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 200
    CYCLEPROPS = 3000

    SOLVERSTATUS = {'ERROR': 'ERROR', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'BUSY', }
    CAMERASTATUS = {'1': 'DISCONNECTED', '0': 'DISCONNECTED', '5': 'DOWNLOADING', '2': 'IDLE', '3': 'INTEGRATING'}

    def __init__(self, app, commandQueue):
        super().__init__()
        self.app = app
        self.commandQueue = commandQueue
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {'Camera': {}, 'Solver': {}}

        self.driverNameCamera = 'MaxIm.CCDCamera'
        self.driverNameDocument = 'MaxIm.Document'
        self.maximCamera = None
        self.maximDocument = None

        self.data['Camera']['AppAvailable'] = True
        self.data['Camera']['AppName'] = 'None'
        self.data['Camera']['AppInstallPath'] = 'None'
        self.data['Solver']['AppAvailable'] = True
        self.data['Solver']['AppName'] = 'None'
        self.data['Solver']['AppInstallPath'] = 'None'
        self.data['Camera']['Status'] = '---'
        self.data['Camera']['CONNECTION'] = {'CONNECT': 'Off'}
        self.data['Solver']['Status'] = '---'
        self.data['Solver']['CONNECTION'] = {'CONNECT': 'Off'}

        self.appExe = 'MaxIm_DL.exe'

        self.data['Camera']['AppAvailable'], self.data['Camera']['AppName'], self.data['Camera']['AppInstallPath'] = self.app.checkRegistrationKeys('MaxIm DL')
        if self.data['Camera']['AppAvailable']:
            self.app.messageQueue.put('Found: {0}\n'.format(self.data['Camera']['AppName']))
            self.logger.info('Name: {0}, Path: {1}'.format(self.data['Camera']['AppName'], self.data['Camera']['AppInstallPath']))
        else:
            self.logger.info('Application MaxIm DL not found on computer')
        self.data['Solver']['AppAvailable'] = self.data['Camera']['AppAvailable']
        self.data['Solver']['AppName'] = self.data['Camera']['AppName']
        self.data['Solver']['AppInstallPath'] = self.data['Camera']['AppInstallPath']

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        if self.driverNameCamera != '' and self.driverNameDocument != '':
            pythoncom.CoInitialize()
            try:
                if not self.maximCamera:
                    self.maximCamera = Dispatch(self.driverNameCamera)
                if not self.maximDocument:
                    self.maximDocument = Dispatch(self.driverNameDocument)
                if not self.maximCamera.LinkEnabled:
                    self.maximCamera.LinkEnabled = True
                self.data['Camera']['CONNECTION']['CONNECT'] = 'On'
                self.data['Solver']['CONNECTION']['CONNECT'] = 'On'
                self.setCameraProps()
            except Exception as e:
                self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'
                self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'
                self.logger.error('error: {0}'.format(e))
                self.isRunning = False
            finally:
                if self.isRunning:
                    self.setStatus()
                    self.setCameraProps()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        while self.isRunning:
            if not self.commandQueue.empty():
                command = self.commandQueue.get()
                if command['Command'] == 'GetImage':
                    command['ImageParams'] = self.getImage(command['ImageParams'])
                elif command['Command'] == 'SolveImage':
                    command['ImageParams'] = self.solveImage(command['ImageParams'])
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.maximCamera.LinkEnabled = False
        self.maximCamera = None
        self.maximDocument = None
        pythoncom.CoUninitialize()
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def setStatus(self):
        if self.maximCamera:
            mes = str(self.maximCamera.CameraStatus)
            print(mes)
            if mes in self.CAMERASTATUS:
                self.data['Camera']['CONNECTION']['CONNECT'] = 'On'
                self.data['Solver']['CONNECTION']['CONNECT'] = 'On'
                self.data['Camera']['Status'] = self.CAMERASTATUS[mes]
                if self.data['Camera']['Status'] == 'DISCONNECTED':
                    self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'
                    self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'
            else:
                self.logger.error('Unknown camera status: {0}'.format(mes))

        self.cameraStatus.emit(self.data['Camera']['Status'])
        self.cameraExposureTime.emit('---')

        if 'CONNECTION' in self.data['Camera']:
            if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusCamera.emit(2)
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

    def setCameraProps(self):
        if self.maximCamera:
            if 'CONNECTION' in self.data['Camera']:
                if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                    self.data['Camera']['Gain'] = 'Not Set'
                    if False:
                        self.data['Camera']['CCD_FRAME'] = {}
                        self.data['Camera']['CCD_FRAME']['HEIGHT'] = self.maximCamera.CameraXSize
                        self.data['Camera']['CCD_FRAME']['WIDTH'] = self.maximCamera.CameraYSize
                        self.data['Camera']['CCD_FRAME']['X'] = 0
                        self.data['Camera']['CCD_FRAME']['Y'] = 0
                    self.data['Camera']['CCD_INFO'] = {}
                    self.data['Camera']['CCD_INFO']['CCD_MAX_X'] = self.maximCamera.CameraXSize
                    self.data['Camera']['CCD_INFO']['CCD_MAX_Y'] = self.maximCamera.CameraYSize

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLEPROPS, self.setCameraProps)

    def getImage(self, imageParams):
        suc = False
        mes = ''
        if self.maximCamera:
            try:
                self.maximCamera.BinX = int(imageParams['Binning'])
                self.maximCamera.BinY = int(imageParams['Binning'])
                self.maximCamera.NumX = int(imageParams['SizeX'])
                self.maximCamera.NumY = int(imageParams['SizeY'])
                self.maximCamera.StartX = int(imageParams['OffX'])
                self.maximCamera.StartY = int(imageParams['OffY'])
                if imageParams['Speed'] == 'HiSpeed':
                    self.maximCamera.FastReadout = True
                else:
                    self.maximCamera.FastReadout = False
                suc = self.maximCamera.Expose(imageParams['Exposure'], 1)
                if not suc:
                    self.logger.error('could not start exposure')
                while not self.maximCamera.ImageReady:
                    time.sleep(0.1)
                    PyQt5.QtWidgets.QApplication.processEvents()
                imageParams['Imagepath'] = imageParams['BaseDirImages'] + '/' + imageParams['File']
                self.maximCamera.SaveImage(imageParams['Imagepath'])
                suc = True
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
                suc = False
            finally:
                imageParams['Success'] = suc
                imageParams['Message'] = mes
        else:
            imageParams['Success'] = False
            imageParams['Message'] = 'Camera not Connected'
        return imageParams

    def solveImage(self, imageParams):
        startTime = time.time()
        self.maximDocument.OpenFile(imageParams['Imagepath'].replace('/', '\\'))
        ra = self.app.mount.transform.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTRA'), ' ')
        dec = self.app.mount.transform.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTDEC'), ' ')
        hint = self.maximDocument.GetFITSKey('CDELT1')
        if not hint:
            xpixsz = self.maximDocument.GetFITSKey('XPIXSZ')
            focallen = self.maximDocument.GetFITSKey('FOCALLEN')
            hint = float(xpixsz) * 206.6 / float(focallen)
        else:
            hint = float(hint)
        self.logger.info('solving pinpoint with ra:{0}, dec:{1}, hint:{2}'.format(ra, dec, hint))
        self.maximDocument.PinPointSolve(ra, dec, hint, hint)
        while True:
            try:
                status = self.maximDocument.PinPointStatus
                if status != 3:
                    # 3 means solving
                    break
            except Exception as e:
                # the request throws exception for reason of failing plate solve
                if e.excepinfo[2] == 'The time limit for plate solving has expired':
                    self.logger.warning('time limit from pinpoint has expired')
                    self.logger.warning('solving message: {0}'.format(e))
                else:
                    self.logger.error('error: {0}'.format(e))
            finally:
                pass
            time.sleep(0.25)
        stopTime = time.time()
        timeTS = (stopTime - startTime) / 1000
        if status == 1:
            self.logger.info('no start {0}'.format(status))
            success = self.maximDocument.Close
            if not success:
                self.logger.error('document {0} could not be closed'.format(imageParams['Imagepath']))
                imageParams['Success'] = False
                imageParams['Message'] = 'Problem closing document in MaximDL'
            else:
                imageParams['Success'] = False
                imageParams['Message'] = 'The time limit for plate solving has expired'
        elif status == 2:
            imageParams['RaJ2000Solved'] = self.maximDocument.CenterRA
            imageParams['DecJ2000Solved'] = self.maximDocument.CenterDec
            imageParams['Scale'] = self.maximDocument.ImageScale
            imageParams['Angle'] = self.maximDocument.PositionAngle
            imageParams['TimeTS'] = timeTS
            self.logger.info('imageParams {0}'.format(imageParams))
            imageParams['Success'] = True
            imageParams['Message'] = 'Solved'
        return imageParams
