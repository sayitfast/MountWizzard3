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

# import basic stuff
import logging
import time
import os
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch
# windows automation
from pywinauto import Application, timings, findwindows, application


class MaximDLCamera:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        self.app = app
        self.appRunning = False
        self.appConnected = False
        self.appCameraConnected = False
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverNameCamera = 'MaxIm.CCDCamera'                                                                           # driver object name
        self.driverNameDocument = 'MaxIm.Document'                                                                          # driver object name
        self.maximCamera = None                                                                                             # placeholder for ascom driver object
        self.maximDocument = None                                                                                           # placeholder for ascom driver object
        self.cameraStatus = ''
        self.appInstallPath = ''
        self.appAvailable = False
        self.appName = ''
        self.appExe = 'MaxIm_DL.exe'
        self.checkAppInstall()

    def checkAppInstall(self):
        self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('MaxIm DL')
        if self.appAvailable:
            self.app.messageQueue.put('Found: {0}'.format(self.appName))
            self.logger.debug('checkApplicatio-> Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
        else:
            self.logger.error('checkApplicatio-> Application MaxIm DL not found on computer')

    def startApplication(self):
        self.appRunning = True
        try:
            findwindows.find_window(title_re='^(.*?)(\\bMaxIm\\b)(.*)$')
        except findwindows.WindowNotFoundError:
            self.appRunning = False
        except Exception as e:
            self.logger.error('startApplicatio-> error{0}'.format(e))
        finally:
            pass
        if not self.appRunning:
            try:
                app = Application(backend='win32')
                app.start(self.appInstallPath + '\\' + self.appExe)
                self.appRunning = True
                self.logger.error('startApplicatio-> started MaxIm DL')
            except application.AppStartError:
                self.logger.error('startApplicatio-> error starting application')
                self.app.messageQueue.put('Failed to start MaxIm DL!')
                self.appRunning = False
            finally:
                pass

    def checkAppStatus(self):
        try:
            findwindows.find_windows(title_re='^(.*?)(\\bMaxIm\\b)(.*)$')
            self.appRunning = True
        except findwindows.WindowNotFoundError:
            self.appRunning = False
        except Exception as e:
            print('error')
            self.logger.error('checkAppStatus -> error{0}'.format(e))
        finally:
            pass
        if self.maximCamera:
            try:
                self.appConnected = self.maximCamera.LinkEnabled
            except Exception as e:
                self.logger.error('checkAppStatus -> error{0}'.format(e))
                self.appConnected = False
                self.appCameraConnected = False
                self.maximCamera = None
                self.maximDocument = None
            finally:
                pass
        else:
            self.appConnected = False
            self.appCameraConnected = False

    def connectApplication(self):
        if self.appRunning:
            try:
                if not self.maximCamera:
                    print('Camera dispatched')
                    self.maximCamera = Dispatch(self.driverNameCamera)
                if not self.maximDocument:
                    print('Document dispatched')
                    self.maximDocument = Dispatch(self.driverNameDocument)
                self.maximCamera.LinkEnabled = True
                self.appConnected = True
            except Exception as e:
                self.logger.error('connectApplicat-> error: {0}'.format(e))
            finally:
                pass

    def disconnectApplication(self):
        try:
            self.maximCamera.LinkEnabled = False
        except Exception as e:
            self.logger.error('disconnectAppli-> error: {0}'.format(e))
        finally:
            self.appCameraConnected = False
            self.appConnected = False
            self.maximCamera = None
            self.maximDocument = None

    def connectCamera(self):
        if self.appConnected:
            self.maximCamera.LinkEnabled = True
            self.appCameraConnected = True

    def disconnectCamera(self):
        if self.appConnected:
            self.appCameraConnected = False

    def getImage(self, modelData):
        suc = False
        mes = ''
        if self.maximCamera:
            try:
                self.maximCamera.BinX = int(modelData['binning'])
                self.maximCamera.BinY = int(modelData['binning'])
                self.maximCamera.NumX = int(modelData['sizeX'])
                self.maximCamera.NumY = int(modelData['sizeY'])
                self.maximCamera.StartX = int(modelData['offX'])
                self.maximCamera.StartY = int(modelData['offY'])
                self.maximCamera.Expose(modelData['exposure'], 1)
                while not self.maximCamera.ImageReady:
                    time.sleep(0.2)
                modelData['imagepath'] = modelData['base_dir_images'] + '/' + modelData['file']
                self.maximCamera.SaveImage(modelData['imagepath'])
                suc = True
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('maximdl-getImag-> error: {0}'.format(e))
                suc = False
                mes = '{0}'.format(e)
                self.logger.debug('maximdl-getImag-> message: {0}'.format(mes))
            finally:
                return suc, mes, modelData
        else:
            return False, 'Camera not Connected', modelData

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
            self.logger.error('ASC-getCamProp -> error: {0}'.format(e))
            suc = False
            mes = '{0}'.format(e)
        finally:
            return suc, mes, sizeX, sizeY, canSubframe, gains

    def getCameraStatus(self):
        if self.appConnected:
            try:
                value = 0
                value = self.maximCamera.CameraStatus
            except Exception as e:
                self.logger.error('getCameraStatus-> error: {0}'.format(e))
            finally:
                pass
            if value == 2:
                self.cameraStatus = 'READY'
            elif value == 3:
                self.cameraStatus = 'INTEGRATING'
            elif value == 4:
                self.cameraStatus = 'READOUT'
            elif value == 5:
                self.cameraStatus = 'DOWNLOADING'
            else:
                self.cameraStatus = 'ERROR'
        else:
            self.cameraStatus = 'NOT CONNECTED'

    def solveImage(self, modelData):
        start = time.time()                                                                                                 # start timer for plate solve
        self.maximDocument.OpenFile(modelData['imagepath'].replace('/', '\\'))                                              # open the fits file
        ra = self.app.mount.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTRA'), ' ')                               # get ra
        dec = self.app.mount.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTDEC'), ' ')                             # get dec
        hint = self.maximDocument.GetFITSKey('CDELT1')                                                                      # get scale hint
        print(ra, dec, hint)
        self.maximDocument.PinPointSolve(ra, dec, hint, hint)                                                               # start solving with FITS Header data
        while self.maximDocument.PinPointStatus == 3:                                                                       # means solving
            time.sleep(0.1)
        stat = self.maximDocument.PinPointStatus
        if stat == 1:
            self.logger.warning('MAX-solveImage -> no start {0}'.format(stat))                                               # debug output
            self.maximDocument.Close()
            return False, stat, modelData
        stop = time.time()
        timeTS = (stop - start) / 1000
        if stat == 2:
            modelData['dec_sol'] = self.maximDocument.CenterDec
            modelData['ra_sol'] = self.maximDocument.CenterRA
            modelData['scale'] = self.maximDocument.ImageScale
            modelData['angle'] = self.maximDocument.PositionAngle
            modelData['timeTS'] = timeTS
            self.logger.debug('solveImage solv-> modelData {0}'.format(modelData))
            self.maximDocument.Close()
            return True, 'OK', modelData
