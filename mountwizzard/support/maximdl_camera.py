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
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch


class MaximDLCamera:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        self.app = app
        self.connected = False
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverNameCamera = 'MaxIm.CCDCamera'                                                                           # driver object name
        self.driverNameDocument = 'MaxIm.Document'                                                                          # driver object name
        self.maximCamera = None                                                                                             # placeholder for ascom driver object
        self.maximDocument = None                                                                                           # placeholder for ascom driver object
        self.cameraStatus = ''

    def connect(self):
        try:
            self.maximCamera = Dispatch(self.driverNameCamera)
            self.maximCamera.LinkEnabled = True
            self.connected = True
        except Exception as e:
            self.connected = False
            self.logger.error('connect        -> error: {0}'.format(e))
        finally:
            pass
        try:
            self.maximDocument = Dispatch(self.driverNameDocument)
            self.connected = True
        except Exception as e:
            self.connected = False
            self.logger.error('connect        -> error: {0}'.format(e))
        finally:
            pass

    def disconnect(self):
        try:
            self.maximCamera.LinkEnabled = False
            self.connected = False
            self.maximCamera = None
        except Exception as e:
            self.connected = False
            self.logger.error('disconnect     -> error: {0}'.format(e))
        finally:
            pass
        try:
            self.connected = False
            self.maximDocument = None
        except Exception as e:
            self.connected = False
            self.logger.error('disconnect     -> error: {0}'.format(e))
        finally:
            pass

    def checkConnection(self):
        if self.connected:
            if self.maximCamera.LinkEnabled:
                # if not self.cameraStatus == 'ERROR':
                return True, 'Camera OK'
            else:
                return False, 'Camera not available !'
        else:
            return False, 'Camera not available !'

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
        if self.connected:
            value = self.maximCamera.CameraStatus
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
        print(ra,dec,hint)
        self.maximDocument.PinPointSolve(ra, dec, hint, hint)                                                               # start solving with FITS Header data
        while self.maximDocument.PinPointStatus == 3:                                                                       # means solving
            time.sleep(0.1)
        stat = self.maximDocument.PinPointStatus
        if stat == 1:
            self.logger.warning('MAX-solveImage -> no start {0}'.format(stat))                                               # debug output
            self.maximDocument.Close
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
            self.maximDocument.Close
            return True, 'OK', modelData


if __name__ == "__main__":
    modelData = dict()
    modelData['exposure'] = 1
    modelData['binning'] = 1
    modelData['binning'] = 1
    modelData['sizeX'] = 800
    modelData['sizeY'] = 600
    modelData['offX'] = 0
    modelData['offY'] = 0
    modelData['offX'] = 0
    modelData['base_dir_images'] = 'c:/temp'
    modelData['file'] = 'test1.fit'
    cam = MaximDLCamera(1)
    cam.connect()
    print(cam.getCameraProps())
    cam.getImage(modelData)
    cam.disconnect()
