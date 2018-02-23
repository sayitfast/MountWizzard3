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
    cameraStatusText = PyQt5.QtCore.pyqtSignal(str)
    solverStatusText = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 200
    CYCLEPROPS = 3000
    CYCLE_MAIN_LOOP = 200

    SOLVERSTATUS = {'2': 'SOLVED', '3': 'SOLVING', '1': 'BUSY', }
    CAMERASTATUS = {'1': 'DISCONN', '0': 'DISCONN', '5': 'DOWNLOAD', '2': 'IDLE', '3': 'INTEGRATE'}

    def __init__(self, app, thread, commandQueue):
        super().__init__()
        self.app = app
        self.thread = thread
        self.commandQueue = commandQueue
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
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
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
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
        else:
            self.maximCamera.LinkEnabled = False
            self.maximCamera = None
            self.maximDocument = None
            pythoncom.CoUninitialize()
        self.mutexIsRunning.unlock()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()

        self.thread.quit()
        self.thread.wait()

    def setStatus(self):
        if self.maximCamera:
            mes = str(self.maximCamera.CameraStatus)
            if mes in self.CAMERASTATUS:
                self.data['Camera']['CONNECTION']['CONNECT'] = 'On'
                self.cameraStatusText.emit(self.CAMERASTATUS[mes])
                self.data['Camera']['Status'] = self.CAMERASTATUS[mes]
                if self.data['Camera']['Status'] == 'DISCONN':
                    self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'
                    self.cameraStatusText.emit('DISCONN')
            else:
                self.logger.error('Unknown camera status: {0}'.format(mes))
                self.cameraStatusText.emit(self.data['Camera']['Status'])
                self.cameraExposureTime.emit('---')

        if self.maximDocument:
            mes = str(self.maximDocument.PinPointStatus)
            if mes in self.SOLVERSTATUS:
                self.data['Solver']['CONNECTION']['CONNECT'] = 'On'
                self.solverStatusText.emit(self.SOLVERSTATUS[mes])
                self.data['Solver']['Status'] = self.SOLVERSTATUS[mes]
                if self.data['Camera']['Status'] == 'DISCONN':
                    self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'
                    self.solverStatusText.emit('DISCONN')
            else:
                self.logger.error('Unknown camera status: {0}'.format(mes))
                self.solverStatusText.emit(self.data['Solver']['Status'])

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
                path = imageParams['BaseDirImages'] + '/' + imageParams['File']
                self.maximCamera.SaveImage(path)
                imageParams['Imagepath'] = path
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
            finally:
                imageParams['Message'] = mes
        else:
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
                imageParams['Message'] = 'Problem closing document in MaximDL'
            else:
                imageParams['Message'] = 'The time limit for plate solving has expired'
        elif status == 2:
            imageParams['RaJ2000Solved'] = self.maximDocument.CenterRA
            imageParams['DecJ2000Solved'] = self.maximDocument.CenterDec
            imageParams['Scale'] = self.maximDocument.ImageScale
            imageParams['Angle'] = self.maximDocument.PositionAngle
            imageParams['TimeTS'] = timeTS
            self.logger.info('imageParams {0}'.format(imageParams))
            imageParams['Message'] = 'Solved'
        return imageParams
