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

import numpy
import pyfits
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch

from baseclasses.camera import MWCamera


class AscomCamera(MWCamera):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(AscomCamera, self).__init__(app)
        self.connected = False
        self.connectedPlateSolver = False
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverNameCamera = ''                                                                                          # driver object name
        self.driverNamePlateSolver = ''
        self.ascomCamera = None                                                                                             # placeholder for ascom driver object
        self.win32PlateSolver = None
        self.cameraStatus = ''

    def checkAppInstall(self):
        self.app.messageQueue.put('Found: ASCOM - actually disabled')
        self.app.ui.rb_cameraASCOM.setVisible(False)
        self.app.ui.rb_cameraASCOM.setCheckable(False)

    def connect(self):
        pass

    def disconnect(self):
        pass

    def checkConnection(self):
        if self.connected:
            if self.connectedPlateSolver:
                return True, 'Camera and Solver OK'
            else:
                return False, 'PlateSolver not available !'
        else:
            return False, 'Camera not available !'

    def getImage(self, modelData):
        suc = False
        mes = ''
        if self.ascomCamera:
            try:
                self.ascomCamera.BinX = int(modelData['binning'])
                self.ascomCamera.BinY = int(modelData['binning'])
                self.ascomCamera.NumX = int(modelData['sizeX'])
                self.ascomCamera.NumY = int(modelData['sizeY'])
                self.ascomCamera.StartX = int(modelData['offX'])
                self.ascomCamera.StartY = int(modelData['offY'])
                # self.ascomCamera.Gains = modelData['gainValue']
                self.ascomCamera.StartExposure(modelData['exposure'], True)
                while not self.ascomCamera.ImageReady:
                    time.sleep(0.2)
                # self.ascomCamera.ReadoutModes = modelData['speed']
                image = numpy.rot90(numpy.array(self.ascomCamera.ImageArray))
                image = numpy.flipud(image)
                hdu = pyfits.PrimaryHDU(image)
                modelData['imagepath'] = modelData['base_dir_images'] + '/' + modelData['file']
                hdu.writeto(modelData['imagepath'])
                if self.app.imagePopup.showStatus:
                    self.app.imagePopup.showImage(image)
                suc = True
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('ASC-getImage    -> error: {0}'.format(e))
                suc = False
                mes = '{0}'.format(e)
                self.logger.debug('ASC-getImage   -> message: {0}'.format(mes))
            finally:
                return suc, mes, modelData
        else:
            return False, 'Camera not Connected', modelData

    def getImageRaw(self, modelData):
        suc = False
        mes = ''
        if self.ascomCamera:
            try:
                self.ascomCamera.BinX = int(modelData['binning'])
                self.ascomCamera.BinY = int(modelData['binning'])
                self.ascomCamera.NumX = int(modelData['sizeX'])
                self.ascomCamera.NumY = int(modelData['sizeY'])
                self.ascomCamera.StartX = int(modelData['offX'])
                self.ascomCamera.StartY = int(modelData['offY'])
                # self.ascomCamera.Gains = modelData['gainValue']
                self.ascomCamera.StartExposure(modelData['exposure'], True)
                while not self.ascomCamera.ImageReady:
                    time.sleep(0.2)
                # self.ascomCamera.ReadoutModes = modelData['speed']
                image = numpy.rot90(numpy.array(self.ascomCamera.ImageArray))
                image = numpy.flipud(image)
                suc = True
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('ASC-getImage    -> error: {0}'.format(e))
                suc = False
                mes = '{0}'.format(e)
                self.logger.debug('ASC-getImage   -> message: {0}'.format(mes))
            finally:
                return suc, mes, image
        else:
            return False, 'Camera not Connected', []

    def solveImage(self, modelData):
        mes = 'started'
        suc = False
        try:
            self.win32PlateSolver.AttachFITS(modelData['imagepath'])
            self.win32PlateSolver.ArcsecPerPixelHoriz = modelData['scaleHint']
            self.win32PlateSolver.ArcsecPerPixelVert = modelData['scaleHint']
            self.win32PlateSolver.RightAscension = self.win32PlateSolver.TargetRightAscension
            self.win32PlateSolver.Declination = self.win32PlateSolver.TargetDeclination
            self.win32PlateSolver.Solve()
            self.win32PlateSolver.DetachFITS()
            suc = True
            mes = 'Solved'
            modelData['dec_sol'] = float(self.win32PlateSolver.Declination)
            modelData['ra_sol'] = float(self.win32PlateSolver.RightAscension)
            modelData['scale'] = float(self.win32PlateSolver.ArcsecPerPixelHoriz)
            modelData['angle'] = float(self.win32PlateSolver.RollAngle)
            modelData['timeTS'] = 2.0
        except Exception as e:
            self.win32PlateSolver.DetachFITS()
            self.logger.error('ASC-solveImage -> error: {0}'.format(e))
            suc = False
            mes = '{0}'.format(e)
        finally:
            return suc, mes, modelData

    def getCameraProps(self):
        suc = True
        mes = 'OK'
        canSubframe = False
        gains = ''
        sizeX = 1
        sizeY = 1
        try:
            sizeX = self.ascomCamera.CameraXSize
            sizeY = self.ascomCamera.CameraYSize
            canSubframe = True
            # gains = self.ascomCamera.Gains
            gains = ['Not Set']
        except Exception as e:
            self.win32PlateSolver.DetachFITS()
            self.logger.error('ASC-getCamProp -> error: {0}'.format(e))
            suc = False
            mes = '{0}'.format(e)
        finally:
            return suc, mes, sizeX, sizeY, canSubframe, gains

    def getCameraStatus(self):
        if self.connected:
            value = self.ascomCamera.CameraState
            if value == 0:
                self.cameraStatus = 'READY'
            elif value == 1:
                self.cameraStatus = 'PREPARATION'
            elif value == 2:
                self.cameraStatus = 'INTEGRATING'
            elif value == 3:
                self.cameraStatus = 'READOUT'
            elif value == 4:
                self.cameraStatus = 'DOWNLOADING'
            else:
                self.cameraStatus = 'ERROR'
        else:
            self.cameraStatus = 'NOT CONNECTED'

    def connectCameraPlateSolver(self):
        try:
            self.ascomCamera = Dispatch(self.driverNameCamera)
            self.ascomCamera.connected = True
            self.connected = True
        except Exception as e:
            self.connected = False
            self.logger.error('connectCameraPl-> error: {0}'.format(e))
        finally:
            pass
        try:
            self.win32PlateSolver = Dispatch('PinPoint.Plate')
            self.win32PlateSolver.Catalog = 11
            self.win32PlateSolver.CatalogPath = 'C:/UCAC4'
            self.connectedPlateSolver = True
        except Exception as e:
            self.connectedPlateSolver = False
            self.logger.error('connectCameraPl-> error: {0}'.format(e))
        finally:
            pass

    def disconnectCameraPlateSolver(self):
        try:
            self.ascomCamera.connected = False
            self.connected = False
            self.ascomCamera = None
        except Exception as e:
            self.connected = False
            self.logger.error('disconnectCamer-> error: {0}'.format(e))
        finally:
            pass
        try:
            self.win32PlateSolver = None
            self.connectedPlateSolver = False
        except Exception as e:
            self.connectedPlateSolver = False
            self.logger.error('connectCameraPl-> error: {0}'.format(e))
        finally:
            pass

    def setupDriverCamera(self):
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'Camera'
            self.driverNameCamera = self.chooser.Choose(self.driverNameCamera)
            self.connected = False                                                                                    # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.logger.error('setupDriverCame-> general exception:{0}'.format(e))                                          # write to log
            self.connected = False                                                                                    # run the driver setup dialog
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary

    def setupDriverPlateSolver(self):
        try:
            self.driverNamePlateSolver = 'PinPoint.Plate'
            self.connectedPlateSolver = False                                                                               # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.logger.error('setupDriverPlat-> general exception:{0}'.format(e))                                          # write to log
            self.connectedPlateSolver = False                                                                               # run the driver setup dialog
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary


if __name__ == "__main__":
    cam = AscomCamera()
    # cam.setupDriverCamera()
    cam.driverNameCamera = 'ASCOM.Simulator.Camera'
    cam.connectCameraPlateSolver()
    # print(cam.ascomCamera.ReadoutModes)
    suc, mes, x, y, can, gains = cam.getCameraProps()
    # print(x, y, gains)
