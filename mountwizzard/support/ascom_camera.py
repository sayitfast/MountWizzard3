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

    def connectCameraPlateSolver(self):
        try:
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
            self.win32PlateSolver.Catalog = 3                                                                               # Corrected GSC
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

    def SgEnumerateDevice(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        data = {'Device': device}
        try:
            req = request.Request(self.ipSGPro + self.enumerateDevicePath,
                                  data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Devices":["String"],"Success":false,"Message":"String"}
            return captureResponse['Devices'], captureResponse['Success'], 'Request OK'
        except Exception as e:
            self.logger.error('SgEnumerateDevi-> error: {0}'.format(e))
            return '', False, 'Request failed'

    def SgCaptureImage(self, binningMode=1, exposureLength=1,
                       gain=None, iso=None, speed=None, frameType=None, filename=None,
                       path=None, useSubframe=False, posX=0, posY=0,
                       width=1, height=1):
        # reference {"BinningMode":0,"ExposureLength":0,"Gain":"String","Speed":"Normal","FrameType":"Light",
        # reference "Path":"String","UseSubframe":false,"X":0,"Y":0,"Width":0,"Height":0}
        data = {
            "BinningMode": binningMode, "ExposureLength": exposureLength, "UseSubframe": useSubframe, "X": posX,
            "Y ": posY,
            "Width": width, "Height": height
            }
        if gain:
            data['Gain'] = gain
        if iso:
            data['Iso'] = iso
        if speed:
            data['Speed'] = speed
        if frameType:
            data['FrameType'] = frameType
        if path and filename:
            data['Path'] = path + '/' + filename
        try:
            req = request.Request(self.ipSGPro + self.captureImagePath,
                                  data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Receipt']
        except Exception as e:
            self.logger.error('SgCaptureImage -> error: {0}'.format(e))
            return False, 'Request failed', ''

    def SgGetCameraProps(self):
        # reference {}
        data = {}
        try:
            req = request.Request(self.ipSGPro + self.getCameraPropsPath,
                                  data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","NumPixelsX":0,"NumPixelsY":0,"SupportsSubframe":false}
            if 'GainValues' not in captureResponse:
                captureResponse['GainValues'] = ['High']
            return captureResponse['Success'], captureResponse['Message'], int(captureResponse['NumPixelsX']), int(
                captureResponse['NumPixelsY']), captureResponse['SupportsSubframe'], captureResponse['GainValues'][
                       0]
        except Exception as e:
            self.logger.error('SgGetCameraProp-> error: {0}'.format(e))
            return False, 'Request failed', '', '', ''

    def SgGetDeviceStatus(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        data = {'Device': device}
        try:
            req = request.Request(self.ipSGPro + self.getDeviceStatusPath,
                                  data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # states are  "IDLE", "CAPTURING", "BUSY", "MOVING", "DISCONNECTED", "PARKED"
            # {"State":"IDLE","Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['State']
        except Exception as e:
            self.logger.error('SgGetDeviceStat-> error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetImagePath(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            req = request.Request(self.ipSGPro + self.getImagePath, data=bytes(json.dumps(data).encode('utf-8')),
                                  method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['Message']
        except Exception as e:
            self.logger.error('SgGetImagePath -> error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetSolvedImageData(self, guid):
        if guid:
            try:
                self.win32PlateSolver.Solve()
                # {"Success":false,"Message":"String","Ra":0,"Dec":0,"Scale":0,"Angle":0,"TimeToSolve":0}
                return captureResponse['Success'], captureResponse['Message'], captureResponse['Ra'], captureResponse[
                    'Dec'], captureResponse['Scale'], captureResponse['Angle'], captureResponse['TimeToSolve']
            except Exception as e:
                self.logger.error('SgGetSolvedImag-> error: {0}'.format(e))
                return False, 'Request failed', '', '', '', '', ''

    def SgSolveImage(self, path, raHint=None, decHint=None, scaleHint=None, blindSolve=False, useFitsHeaders=False):
        try:
            self.win32PlateSolver.AttachFITS(path)
        except Exception as e:
            pass
        self.win32PlateSolver.ArcsecPerPixelHoriz = scaleHint
        self.win32PlateSolver.ArcsecPerPixelVert = scaleHint
        self.win32PlateSolver.RightAscension = self.win32PlateSolver.TargetRightAscension
        self.win32PlateSolver.Declination = self.win32PlateSolver.TargetDeclination
        try:
            self.win32PlateSolver.Solve()
            self.win32PlateSolver.DetachFITS()
            return 'True', 'Solving started', '00000000000000000000000000000000'
        except Exception as e:
            self.win32PlateSolver.DetachFITS()
            self.logger.error('SgSolveImage   -> error: {0}'.format(e))
            return False, 'Request failed', ''

    def setupDriverCamera(self):
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'Camera'
            self.driverNameCamera = self.chooser.Choose(self.driverNameCamera)
            self.connectedCamera = False                                                                                    # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setup Camera')                                                       # write to gui
            self.logger.error('setupDriverCame-> general exception:{0}'.format(e))                                          # write to log
            self.connectedCamera = False                                                                                    # run the driver setup dialog
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary

    def setupDriverPlateSolver(self):
        try:
            self.driverNameCamera = Dispatch('PinPoint.Plate')
            self.connectedPlateSolver = False                                                                               # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setup PlateSolver')                                                  # write to gui
            self.logger.error('setupDriverPlat-> general exception:{0}'.format(e))                                          # write to log
            self.connectedPlateSolver = False                                                                               # run the driver setup dialog
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary


if __name__ == "__main__":
    cam = AscomCamera()
    suc, mes, x, y, can = cam.SgGetCameraProps()
    print(x, y, can)
