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
            if self.maximCamera.LinkEnabled:
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
        path = ''
        self.data['Imaging'] = True
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()

        # waiting for start integrating
        self.main.cameraStatusText.emit('START')
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
                self.logger.warning('Imaging no start, message: {0}'.format(mes))
                self.main.cameraStatusText.emit('ERROR')
                imageParams['Imagepath'] = ''
                self.mutexCancel.lock()
                self.cancel = True
                self.mutexCancel.unlock()
        except Exception as e:
            self.logger.error('Could not start imaging, error: {0}'.format(e))
        finally:
            pass

        # loop for integrating
        self.main.cameraStatusText.emit('INTEGRATE')
        # wait for start integrating
        while not self.cancel:
            status = self.maximCamera.CameraStatus
            print('loop integrating', status)
            if status in [4, 5, 6, 8]:
                break
            time.sleep(0.1)

        # Loop for downloading
        self.main.imageIntegrated.emit()
        self.main.cameraStatusText.emit('DOWNLOAD')
        while not self.cancel:
            status = self.maximCamera.CameraStatus
            print('loop download', status)
            if status in [2]:
                break
            time.sleep(0.1)

        # Loop for saving
        self.main.imageDownloaded.emit()
        self.main.cameraStatusText.emit('SAVING')
        while not self.cancel:
            print('loop save', status)
            self.maximCamera.SaveImage(path)
            time.sleep(0.1)
            break

        # finally idle
        self.main.imageSaved.emit()
        self.main.cameraStatusText.emit('IDLE')
        self.main.cameraExposureTime.emit('')
        imageParams['Imagepath'] = path.replace('\\', '/')
        self.data['Imaging'] = False

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
