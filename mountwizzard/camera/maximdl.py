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

    CYCLESTATUS = 200
    SOLVERSTATUS = {'ERROR': 'Error', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'BUSY', }
    CAMERASTATUS = {'1': 'Error', '0': 'DISCONNECTED', '5': 'DOWNLOADING', '2': 'IDLE', '3': 'INTEGRATING'}

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {}

        self.driverNameCamera = 'MaxIm.CCDCamera'
        self.driverNameDocument = 'MaxIm.Document'
        self.maximCamera = None
        self.maximDocument = None
        self.cameraConnected = False
        self.data['CameraStatus'] = 'DISCONNECTED'
        self.solverConnected = False
        self.data['SolverStatus'] = 'DISCONNECTED'
        self.appExe = 'MaxIm_DL.exe'
        self.checkAppInstall()

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
                self.cameraConnected = True
                self.solverConnected = True
                # self.getCameraProps()
            except Exception as e:
                self.cameraConnected = False
                self.solverConnected = False
                self.logger.error('error: {0}'.format(e))
                self.isRunning = False
            finally:
                if self.isRunning:
                    self.getStatus()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        while self.isRunning:
            # time.sleep(0.2)
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

    def checkAppInstall(self):
        self.data['AppAvailable'], self.data['AppName'], self.data['AppInstallPath'] = self.app.checkRegistrationKeys('MaxIm DL')
        if self.data['AppAvailable']:
            self.app.messageQueue.put('Found: {0}\n'.format(self.data['AppName']))
            self.logger.info('Name: {0}, Path: {1}'.format(self.data['AppName'], self.data['AppInstallPath']))
        else:
            self.logger.info('Application MaxIm DL not found on computer')

    def getStatus(self):
        if self.isRunning:
            mes = str(self.maximCamera.CameraStatus)
            if mes in self.CAMERASTATUS:
                self.cameraConnected = True
                self.solverConnected = True
                self.data['CameraStatus'] = self.CAMERASTATUS[mes]
                if self.data['CameraStatus'] == 'DISCONNECTED':
                    self.cameraConnected = False
                    self.solverConnected = False
            else:
                print('Error missing key {0} ind {1}'.format(mes, self.CAMERASTATUS))

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
        suc = True
        mes = 'OK'
        canSubframe = False
        gains = ''
        sizeX = 1
        sizeY = 1
        try:
            sizeX = self.maximCamera.CameraXSize
            sizeY = self.maximCamera.CameraYSize
            canSubframe = True
            gains = ['Not Set']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            suc = False
            mes = '{0}'.format(e)
        finally:
            return suc, mes, sizeX, sizeY, canSubframe, gains

    def getImage(self, modelData):
        suc = False
        mes = ''
        if self.maximCamera:
            try:
                self.maximCamera.BinX = int(modelData['Binning'])
                self.maximCamera.BinY = int(modelData['Binning'])
                self.maximCamera.NumX = int(modelData['SizeX'])
                self.maximCamera.NumY = int(modelData['SizeY'])
                self.maximCamera.StartX = int(modelData['OffX'])
                self.maximCamera.StartY = int(modelData['OffY'])
                if modelData['Speed'] == 'HiSpeed':
                    self.maximCamera.FastReadout = True
                else:
                    self.maximCamera.FastReadout = False
                suc = self.maximCamera.Expose(modelData['Exposure'], 1)
                if not suc:
                    self.logger.error('could not start exposure')
                while not self.maximCamera.ImageReady:
                    time.sleep(0.5)
                modelData['ImagePath'] = modelData['BaseDirImages'] + '/' + modelData['File']
                self.maximCamera.SaveImage(modelData['ImagePath'])
                suc = True
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
                suc = False
            finally:
                return suc, mes, modelData
        else:
            return False, 'Camera not Connected', modelData

    def solveImage(self, modelData):
        startTime = time.time()                                                                                             # start timer for plate solve
        mes = ''
        self.maximDocument.OpenFile(modelData['ImagePath'].replace('/', '\\'))                                              # open the fits file
        ra = self.app.mount.transform.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTRA'), ' ')                     # get ra
        dec = self.app.mount.transform.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTDEC'), ' ')                   # get dec
        hint = self.maximDocument.GetFITSKey('CDELT1')
        if not hint:
            xpixsz = self.maximDocument.GetFITSKey('XPIXSZ')
            focallen = self.maximDocument.GetFITSKey('FOCALLEN')
            hint = float(xpixsz) * 206.6 / float(focallen)
        else:
            hint = float(hint)
        self.logger.info('solving pinpoint with ra:{0}, dec:{1}, hint:{2}'.format(ra, dec, hint))
        self.maximDocument.PinPointSolve(ra, dec, hint, hint)                                                               # start solving with FITS Header data
        while True:
            try:
                status = self.maximDocument.PinPointStatus
                if status != 3:                                                                                             # 3 means solving
                    break
            except Exception as e:                                                                                          # the request throws exception for reason of failing plate solve
                if e.excepinfo[2] == 'The time limit for plate solving has expired':
                    self.logger.warning('time limit from pinpoint has expired')
                    mes = 'The time limit for plate solving has expired'
                    self.logger.warning('solving message: {0}'.format(e))
                else:
                    self.logger.error('error: {0}'.format(e))
            finally:
                pass
            time.sleep(0.25)
        if status == 1:
            self.logger.info('no start {0}'.format(status))
            suc = self.maximDocument.Close
            if not suc:
                self.logger.error('document {0} could not be closed'.format(modelData['ImagePath']))
                return False, 'Problem closing document in MaximDL', modelData
            else:
                return False, mes, modelData

        stopTime = time.time()
        timeTS = (stopTime - startTime) / 1000
        if status == 2:
            modelData['RaJ2000Solved'] = self.maximDocument.CenterRA
            modelData['DecJ2000Solved'] = self.maximDocument.CenterDec
            modelData['Scale'] = self.maximDocument.ImageScale
            modelData['Angle'] = self.maximDocument.PositionAngle
            modelData['TimeTS'] = timeTS
            self.logger.info('modelData {0}'.format(modelData))
            return True, 'Solved', modelData
