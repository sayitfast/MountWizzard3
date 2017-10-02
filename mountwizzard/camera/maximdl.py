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
import platform
import logging
import time
if platform.system() == 'Windows':
    # windows automation
    from pywinauto import Application, findwindows, application
    # import .NET / COM Handling
    from win32com.client.dynamic import Dispatch
# base for cameras
from baseclasses.camera import MWCamera


class MaximDLCamera(MWCamera):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(MaximDLCamera, self).__init__(app)
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverNameCamera = 'MaxIm.CCDCamera'                                                                           # driver object name
        self.driverNameDocument = 'MaxIm.Document'                                                                          # driver object name
        self.maximCamera = None                                                                                             # placeholder for ascom driver object
        self.maximDocument = None                                                                                           # placeholder for ascom driver object
        self.cameraStatus = ''
        self.appExe = 'MaxIm_DL.exe'

    def checkAppInstall(self):
        if platform.system() == 'Windows':
            self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('MaxIm DL')
            if self.appAvailable:
                self.app.messageQueue.put('Found: {0}'.format(self.appName))
                self.logger.info('Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
            else:
                self.app.ui.rb_cameraMaximDL.setVisible(False)
                self.app.ui.rb_cameraMaximDL.setCheckable(False)
                self.logger.info('Application MaxIm DL not found on computer')

    def startApplication(self):
        if platform.system() == 'Windows':
            try:
                a = findwindows.find_window(title_re='^(.*?)(\\bMaxIm DL Pro\\b)(.*)$')
                if len(a) == 0:
                    self.appRunning = False
                else:
                    self.appRunning = True
            except Exception as e:
                self.logger.error('error{0}'.format(e))
            finally:
                pass
            if not self.appRunning:
                try:
                    app = Application(backend='win32')
                    app.start(self.appInstallPath + '\\' + self.appExe)
                    self.appRunning = True
                    self.logger.info('started MaxIm DL')
                except application.AppStartError:
                    self.logger.error('error starting application')
                    self.app.messageQueue.put('Failed to start MaxIm DL!')
                    self.appRunning = False
                finally:
                    pass

    def checkAppStatus(self):
        if platform.system() == 'Windows':
            try:
                a = findwindows.find_windows(title_re='^(.*?)(\\bMaxIm DL Pro\\b)(.*)$')
                if len(a) == 0:
                    self.appRunning = False
                else:
                    self.appRunning = True
            except Exception as e:
                self.logger.error('error{0}'.format(e))
            finally:
                pass
        if self.maximCamera:
            try:
                self.appConnected = self.maximCamera.LinkEnabled
            except Exception as e:
                self.logger.error('error{0}'.format(e))
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
                    self.maximCamera = Dispatch(self.driverNameCamera)
                if not self.maximDocument:
                    self.maximDocument = Dispatch(self.driverNameDocument)
                    pass
                self.maximCamera.LinkEnabled = True
                self.appConnected = True
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
            finally:
                pass

    def disconnectApplication(self):
        try:
            self.maximCamera.LinkEnabled = False
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
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
                suc = self.maximCamera.Expose(modelData['exposure'], 1)
                if not suc:
                    self.logger.error('could not start exposure')
                while not self.maximCamera.ImageReady:
                    time.sleep(0.5)
                modelData['imagepath'] = modelData['base_dir_images'] + '/' + modelData['file']
                self.maximCamera.SaveImage(modelData['imagepath'])
                suc = True
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
                suc = False
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
            self.logger.error('error: {0}'.format(e))
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
                self.logger.error('error: {0}'.format(e))
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
        startTime = time.time()                                                                                             # start timer for plate solve
        mes = ''
        self.maximDocument.OpenFile(modelData['imagepath'].replace('/', '\\'))                                              # open the fits file
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
                self.logger.error('document {0} could not be closed'.format(modelData['imagepath']))
                return False, 'Problem closing document in MaximDL', modelData
            else:
                return False, mes, modelData

        stopTime = time.time()
        timeTS = (stopTime - startTime) / 1000
        if status == 2:
            modelData['dec_sol'] = self.maximDocument.CenterDec
            modelData['ra_sol'] = self.maximDocument.CenterRA
            modelData['scale'] = self.maximDocument.ImageScale
            modelData['angle'] = self.maximDocument.PositionAngle
            modelData['timeTS'] = timeTS
            self.logger.info('modelData {0}'.format(modelData))
            return True, 'Solved', modelData


if __name__ == "__main__":
    from baseclasses.camera import MWCamera
    import time
    max = 10
    cam = MaximDLCamera(MWCamera)
    cam.appRunning = True
    cam.connectApplication()
    print(cam.getCameraProps())
    value = {'binning': 1, 'exposure': 1, 'iso': 100,
             'gainValue': 'Not Set', 'speed': 'HiSpeed',
             'file': 'test.fit', 'base_dir_images': 'c:/temp',
             'canSubframe': True, 'offX': 0, 'offY': 0,
             'sizeX': 3388, 'sizeY': 2712}
    t_start = time.time()
    for i in range(0, max):
        print(i)
        cam.getImage(value)
    t_stop = time.time()
    print((t_stop - t_start - max) / max)
