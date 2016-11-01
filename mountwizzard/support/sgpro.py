############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016
#
# Licence APL2.0
#
############################################################

import logging
# packages for handling web interface to SGPro
from urllib import request
import json


class SGPro:
    logger = logging.getLogger('SGPro')                                         # logging enabling

    def __init__(self):
        self.ipSGProBase = 'http://localhost:59590'
        self.ipSGPro = 'http://localhost:59590/json/reply/'
        self.abortImagePath = 'SgAbortImage'
        self.abortSolvePath = 'SgAbortSolve'
        self.captureGuiderImagePath = 'SgCaptureGuiderImagePath'
        self.captureImagePath = 'SgCaptureImage'
        self.connectDevicePath = 'SgConnectDevicePath'
        self.disconnectDevicePath = 'SgDisconnectDevicePath'
        self.enumerateDevicePath = 'SgEnumerateDevicePath'
        self.getCameraPropsPath = 'SgGetCameraProps'
        self.getCameraTempPath = ''                                     # not needed
        self.getDeviceStatusPath = 'SgGetDeviceStatus'
        self.getFilterPositionPath = ''                                 # not needed
        self.getFocuserPositionPath = ''                                # not needed
        self.getFocuserTempPath = ''                                    # not needed
        self.getGuiderImagePath = ''                                    # not needed
        self.getGuiderInfoPath = ''                                     # not needed
        self.getImagePath = 'SgGetImagePath'
        self.getSolvedImageDataPath = 'SgGetSolvedImageData'
        self.getTelescopeIsSlewingPath = ''                             # not needed
        self.getTelescopePositionPath = 'SgGetTelescopePosition'        # not needed
        self.parkTelescopePath = ''                                     # not needed
        self.sendGuidePulsePath = ''                                    # not needed
        self.setCameraTempPath = ''                                     # not needed
        self.setFilterPositionPath = ''                                 # not needed
        self.setFocuserPositionPath = ''                                # not needed
        self.slewTelescopePath = ''                                     # not needed
        self.solveImagePath = 'SgSolveImage'

    def checkConnection(self):
        try:
            reply = request.urlopen(self.ipSGProBase, None, .5).getcode()
        except:
            reply = ''
        finally:
            if str(reply) == '200':
                if self.SgGetDeviceStatus('Camera'):
                    if self.SgGetDeviceStatus('PlateSolver'):
                        return True, 'Camera and Solver OK'
                    else:
                        return False, 'PlateSolver not available !'
                else:
                    return False, 'Camera not available !'
            else:
                return False, 'Timeout !'

    def SgCaptureImage(self, binningMode=1, isoMode=None, exposureLength=1,
                       gain=None, speed=None, frameType=None,
                       path=None, useSubframe=False, posX=0, posY=0,
                       width=1, height=1):
        # reference {"BinningMode":0,"IsoMode":0,"ExposureLength":0,"Gain":"String","Speed":"Normal","FrameType":"Light",
        # reference "Path":"String","UseSubframe":false,"X":0,"Y":0,"Width":0,"Height":0}
        data = {"BinningMode": binningMode, "ExposureLength": exposureLength, "UseSubframe": useSubframe, "X": posX, "Y ": posY,
                "Width": width, "Height": height}
        if isoMode:
            data['IsoMode'] = isoMode
        if gain:
            data['Gain'] = gain
        if speed:
            data['Speed'] = speed
        if frameType:
            data['FrameType'] = frameType
        if path:
            data['Path'] = path
        try:
            req = request.Request(self.ipSGPro + self.captureImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Receipt']
        except Exception as e:
            return False, 'Request failed', ''

    def SgAbortImage(self):
        # reference {}
        data = {}
        try:
            req = request.Request(self.ipSGPro + self.abortImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['Message']
        except Exception as e:
            return False, 'Request failed'

    def SgAbortSolve(self, receipt):
        # reference {"Receipt":"00000000000000000000000000000000"}
        # The receipt (GUID) returned from the "/solve" (SgSolveImage) call
        data = {'Receipt': receipt}
        try:
            req = request.Request(self.ipSGPro + self.abortImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message']
        except Exception as e:
            return False, 'Request failed'

    def SgGetCameraProps(self):
        # reference {}
        data = {}
        try:
            req = request.Request(self.ipSGPro + self.getCameraPropsPath, data=bytes(json.dumps(data).encode('utf-8')),
                                         method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","NumPixelsX":0,"NumPixelsY":0,"SupportsSubframe":false}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['NumPixelsX'], captureResponse[
                'NumPixelsY'], captureResponse['SupportsSubframe']
        except Exception as e:
            return False, 'Request failed', '', '', ''

    def SgGetDeviceStatus(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        data = {'Device': device}
        try:
            req = request.Request(self.ipSGPro + self.getDeviceStatusPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # states are  "IDLE", "CAPTURING", "BUSY", "MOVING", "DISCONNECTED", "PARKED"
            # {"State":"IDLE","Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['State']
        except Exception as e:
            return False, 'Request failed'

    def SgGetImagePath(self, receipt):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': receipt}
        try:
            req = request.Request(self.ipSGPro + self.getImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['Message']
        except Exception as e:
            return False, 'Request failed'

    def SgGetTelescopePosition(self):
        # reference {}
        data = {}
        try:
            req = request.Request(self.ipSGPro + self.getTelescopePositionPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Ra":0,"Dec":0}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Ra'], captureResponse['Dec']
        except Exception as e:
            return False, 'Request failed', '', ''

    def SgGetSolvedImageData(self, receipt):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': receipt}
        try:
            req = request.Request(self.ipSGPro + self.getSolvedImageDataPath, data=bytes(json.dumps(data).encode('utf-8')),
                                         method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Ra":0,"Dec":0,"Scale":0,"Angle":0,"TimeToSolve":0}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Ra'], captureResponse['Dec'], \
                   captureResponse['Scale'], captureResponse['Angle'], captureResponse['TimeToSolve']
        except Exception as e:
            return False, 'Request failed', '', '', '', '', ''

    def SgSolveImage(self, imagepath, raHint=None, decHint=None, scaleHint=None,
                     blindSolve=False, useFitsHeaders=False):
        # reference {"ImagePath":"String","RaHint":0,"DecHint":0,"ScaleHint":0,"BlindSolve":false,"UseFitsHeadersForHints":false}
        data = {"ImagePath": imagepath,
                "BlindSolve": blindSolve, "UseFitsHeadersForHints": useFitsHeaders}
        if raHint:
            data['RaHint'] = raHint
        if decHint:
            data['DecHint'] = decHint
        if scaleHint:
            data['ScaleHint'] = scaleHint
        try:
            req = request.Request(self.ipSGPro + self.solveImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Receipt']
        except Exception as e:
            return False, 'Request failed', ''

if __name__ == "__main__":
    import time
    cam = SGPro()
    print(cam.SgGetDeviceStatus('Camera'))
    print(cam.SgGetDeviceStatus('PlateSolver'))
    print(cam.SgGetCameraProps())
    print(time.ctime())
    success, message, receipt = cam.SgCaptureImage(binningMode = 1, exposureLength = 1, speed= 'Normal', path = 'c:\\temp\\test.fits')
    print(success,message,receipt)
    while True:  # waiting for the image download before proceeding
        success, imagepath = cam.SgGetImagePath(receipt)
        if success:
            break
        else:
            time.sleep(0.1)
    print(success, imagepath)
    print(time.ctime())
    success, message, receipt = cam.SgCaptureImage(binningMode=1, exposureLength=1, speed='HiSpeed',
                                                   path='c:\\temp\\test.fits')
    print(success, message, receipt)
    while True:  # waiting for the image download before proceeding
        success, imagepath = cam.SgGetImagePath(receipt)
        if success:
            break
        else:
            time.sleep(0.1)
    print(success, imagepath)
    print(time.ctime())
