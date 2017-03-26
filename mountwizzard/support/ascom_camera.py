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
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch


class AscomCamera:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.connectedCamera = False
        self.connectedPlateSolver = False
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverNameCamera = ''                                                                                          # driver object name
        self.driverNamePlateSolver = ''
        self.ascomCamera = None                                                                                             # placeholder for ascom driver object
        self.win32PlateSolver = None

    def checkConnection(self):
        if self.connectedCamera:
            if self.connectedPlateSolver:
                return True, 'Camera and Solver OK'
            else:
                return False, 'PlateSolver not available !'
        else:
            return False, 'Camera not available !'

    def getImage(self, modelData):
        return suc, mes, modelData

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
        try:
            sizeX = self.ascomCamera.CameraXSize
            sizeY = self.ascomCamera.CameraYSize
            canSubframe = True
            # gains = self.ascomCamera.Gains
            gains = ['HighSpeed']
        except Exception as e:
            self.win32PlateSolver.DetachFITS()
            self.logger.error('ASC-getCamProp -> error: {0}'.format(e))
            suc = False
            mes = '{0}'.format(e)
        finally:
            return suc, mes, sizeX, sizeY, canSubframe, gains

    def getCameraStatus(self):
        return status

    def connectCameraPlateSolver(self):
        try:
            self.ascomCamera = Dispatch(self.driverNameCamera)
            self.ascomCamera.connected = True
            self.connectedCamera = True
        except Exception as e:
            self.connectedCamera = False
            self.logger.error('connectCameraPl-> error: {0}'.format(e))
        finally:
            self.connectedPlateSolver = True
            return
        try:
            self.win32PlateSolver = Dispatch('PinPoint.Plate')
            self.win32PlateSolver.Catalog = 3
            self.win32PlateSolver.CatalogPath = 'C:\GSC11'
            self.connectedPlateSolver = True
        except Exception as e:
            self.connectedPlateSolver = False
            self.logger.error('connectCameraPl-> error: {0}'.format(e))
        finally:
            pass

    def disconnectCameraPlateSolver(self):
        try:
            self.ascomCamera.connected = False
            self.connectedCamera = False
            self.ascomCamera = None
        except Exception as e:
            self.connectedCamera = False
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
            self.connectedCamera = False                                                                                    # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.logger.error('setupDriverCame-> general exception:{0}'.format(e))                                          # write to log
            self.connectedCamera = False                                                                                    # run the driver setup dialog
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
    cam.driverNameCamera = 'ASCOM.Simulator.Camera'
    cam.connectCameraPlateSolver()
    suc, mes, x, y, can, gains = cam.getCamProps()
    print(x, y, gains)
