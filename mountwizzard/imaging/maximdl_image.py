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
import time
import PyQt5
import platform
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch
import pythoncom


class MaximDL:
    logger = logging.getLogger(__name__)

    def __init__(self, main, app, data):
        self.main = main
        self.app = app
        self.data = data
        self.cancel = False
        self.mutexCancel = PyQt5.QtCore.QMutex()

        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = ''
        self.application['InstallPath'] = ''
        self.application['Status'] = ''
        self.application['Runtime'] = 'MaxIm_DL.exe'

        self.driverNameCamera = 'MaxIm.CCDCamera'
        self.maximCamera = None

        if platform.system() == 'Windows':
            # sgpro only supported on local machine
            self.application['Available'], self.application['Name'], self.application['InstallPath'] = self.app.checkRegistrationKeys('MaxIm DL')
            if self.application['Available']:
                self.app.messageQueue.put('Found Imaging: {0}\n'.format(self.application['Name']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.application['Name'], self.application['InstallPath']))
            else:
                self.logger.info('Application MaximDL not found on computer')

    def start(self):
        print('start maxim')
        pythoncom.CoInitialize()
        try:
            self.maximCamera = Dispatch('MaxIm.CCDCamera')
            self.maximCamera.LinkEnabled = True
            self.data['CONNECTION']['CONNECT'] = 'On'
            self.logger.info('Maxim started')
            self.application['Status'] = 'OK'
        except Exception as e:
            self.logger.info('Maxim could not be started, error:{0}'.format(e))
            self.application['Status'] = 'ERROR'
        finally:
            pass

    def stop(self):
        try:
            if self.maximCamera:
                self.data['CONNECTION']['CONNECT'] = 'Off'
                self.maximCamera.LinkEnabled = False
                self.maximCamera = None
                pythoncom.CoUninitialize()
        except Exception as e:
            self.logger.error('Could not stop maxim')
        finally:
            self.data['CONNECTION']['CONNECT'] = 'Off'
            self.maximCamera = None

    def getStatus(self):
        if self.maximCamera and self.data['CONNECTION']['CONNECT'] == 'On':
            status = self.maximCamera.CameraStatus
            if status in [0, 1]:
                self.data['CONNECTION']['CONNECT'] = 'Off'
            elif status in [2, 3, 5]:
                self.data['CONNECTION']['CONNECT'] = 'On'
            else:
                self.logger.error('Unknown camera status: {0}'.format(status))
        else:
            self.application['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'

    def getCameraProps(self):
        if self.maximCamera and self.data['CONNECTION']['CONNECT'] == 'On':
            self.data['Gain'] = ['High']
            self.data['CCD_INFO'] = {}
            self.data['CCD_INFO']['CCD_MAX_X'] = self.maximCamera.CameraXSize
            self.data['CCD_INFO']['CCD_MAX_Y'] = self.maximCamera.CameraYSize
        else:
            self.application['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'

    def getImage(self, imageParams):
        if not self.maximCamera or self.data['CONNECTION']['CONNECT'] == 'Off':
            return
        path = ''
        self.data['Imaging'] = True
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()

        # waiting for start integrating
        self.main.cameraStatusText.emit('START')
        suc, mes, guid = self.SgCaptureImage(binningMode=imageParams['Binning'],
                                             exposureLength=imageParams['Exposure'],
                                             iso=str(imageParams['Iso']),
                                             gain=imageParams['Gain'],
                                             speed=imageParams['Speed'],
                                             frameType='Light',
                                             filename=imageParams['File'],
                                             path=imageParams['BaseDirImages'],
                                             useSubframe=imageParams['CanSubframe'],
                                             posX=imageParams['OffX'],
                                             posY=imageParams['OffY'],
                                             width=imageParams['SizeX'],
                                             height=imageParams['SizeY'])
        self.logger.info('SgCaptureImage: {0}'.format(mes))
        if not suc:
            self.logger.warning('Imaging no start, message: {0}'.format(mes))
            self.main.cameraStatusText.emit('ERROR')
            imageParams['Imagepath'] = ''
            self.mutexCancel.lock()
            self.cancel = True
            self.mutexCancel.unlock()

        # loop for integrating
        self.main.cameraStatusText.emit('INTEGRATE')
        # wait for start integrating
        while not self.cancel:
            suc, state, message = self.SgGetDeviceStatus('Camera')
            if 'integrating' in message:
                break
            time.sleep(0.1)
        # bow for the duration
        while not self.cancel:
            suc, state, message = self.SgGetDeviceStatus('Camera')
            if 'downloading' in message or 'ready' in message or 'idle' in message:
                break
            time.sleep(0.1)

        # Loop for downloading
        self.main.imageIntegrated.emit()
        self.main.cameraStatusText.emit('DOWNLOAD')
        while not self.cancel:
            suc, path = self.SgGetImagePath(guid)
            if suc:
                break
            time.sleep(0.1)

        # Loop for saving
        self.main.imageDownloaded.emit()
        self.main.cameraStatusText.emit('SAVING')
        while not self.cancel:
            suc, state, message = self.SgGetDeviceStatus('Camera')
            if 'ready' in message or 'idle' in message:
                break
            time.sleep(0.1)

        # finally idle
        self.main.imageSaved.emit()
        self.main.cameraStatusText.emit('IDLE')
        self.main.cameraExposureTime.emit('')
        imageParams['Imagepath'] = path.replace('\\', '/')
        self.data['Imaging'] = False

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
