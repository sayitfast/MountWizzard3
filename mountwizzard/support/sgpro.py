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

import logging
# packages for handling web interface to SGPro
from urllib import request
import json


class SGPro:
    logger = logging.getLogger(__name__)                                         # logging enabling

    def __init__(self):
        self.ipSGProBase = 'http://localhost:59590'
        self.ipSGPro = 'http://localhost:59590/json/reply/'
        self.abortImagePath = 'SgAbortImage'
        self.abortSolvePath = 'SgAbortSolve'
        self.captureGuiderImagePath = 'SgCaptureGuiderImagePath'
        self.captureImagePath = 'SgCaptureImage'
        self.connectDevicePath = 'SgConnectDevicePath'
        self.disconnectDevicePath = 'SgDisconnectDevicePath'
        self.enumerateDevicePath = 'SgEnumerateDevices'
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
        reply = ''
        try:
            reply = request.urlopen(self.ipSGProBase, None, .5).getcode()
        except Exception as e:
            self.logger.error('checkConnection-> error: {0}'.format(e))
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

    def SgEnumerateDevice(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        data = {'Device': device}
        try:
            req = request.Request(self.ipSGPro + self.enumerateDevicePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Devices":["String"],"Success":false,"Message":"String"}
            return captureResponse['Devices'], captureResponse['Success'], 'Request OK'
        except Exception as e:
            self.logger.error('SgEnumerateDevi-> error: {0}'.format(e))
            return '', False, 'Request failed'

    def SgCaptureImage(self, binningMode=1, isoMode=None, exposureLength=1,
                       gain=None, iso=None, speed=None, frameType=None,
                       path=None, useSubframe=False, posX=0, posY=0,
                       width=1, height=1):
        # reference {"BinningMode":0,"IsoMode":0,"ExposureLength":0,"Gain":"String","Speed":"Normal","FrameType":"Light",
        # reference "Path":"String","UseSubframe":false,"X":0,"Y":0,"Width":0,"Height":0}
        data = {"BinningMode": binningMode, "ExposureLength": exposureLength, "UseSubframe": useSubframe, "X": posX, "Y ": posY,
                "Width": width, "Height": height}
        # if isoMode:
        #    data['IsoMode'] = isoMode
        if gain:
            data['Gain'] = gain
        if iso:
            data['Iso'] = iso
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
            self.logger.error('SgCaptureImage -> error: {0}'.format(e))
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
            self.logger.error('SgAbortImage   -> error: {0}'.format(e))
            return False, 'Request failed'

    def SgAbortSolve(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        # The guid (GUID) returned from the "/solve" (SgSolveImage) call
        data = {'Receipt': _guid}
        try:
            req = request.Request(self.ipSGPro + self.abortImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message']
        except Exception as e:
            self.logger.error('SgAbortSolve   -> error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetCameraProps(self):
        # reference {}
        data = {}
        try:
            req = request.Request(self.ipSGPro + self.getCameraPropsPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","NumPixelsX":0,"NumPixelsY":0,"SupportsSubframe":false}
            return captureResponse['Success'], captureResponse['Message'], int(captureResponse['NumPixelsX']), int(captureResponse[
                'NumPixelsY']), captureResponse['SupportsSubframe']
        except Exception as e:
            self.logger.error('SgGetCameraProp-> error: {0}'.format(e))
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
            self.logger.error('SgGetDeviceStat-> error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetImagePath(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            req = request.Request(self.ipSGPro + self.getImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['Message']
        except Exception as e:
            self.logger.error('SgGetImagePath -> error: {0}'.format(e))
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
            self.logger.error('SgGetTelescopePo-> error: {0}'.format(e))
            return False, 'Request failed', '', ''

    def SgGetSolvedImageData(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            req = request.Request(self.ipSGPro + self.getSolvedImageDataPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Ra":0,"Dec":0,"Scale":0,"Angle":0,"TimeToSolve":0}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Ra'], captureResponse['Dec'], captureResponse['Scale'], captureResponse['Angle'], captureResponse['TimeToSolve']
        except Exception as e:
            self.logger.error('SgGetSolvedImag-> error: {0}'.format(e))
            return False, 'Request failed', '', '', '', '', ''

    def SgSolveImage(self, path, raHint=None, decHint=None, scaleHint=None, blindSolve=False, useFitsHeaders=False):
        # reference {"ImagePath":"String","RaHint":0,"DecHint":0,"ScaleHint":0,"BlindSolve":false,"UseFitsHeadersForHints":false}
        data = {"ImagePath": path, "BlindSolve": blindSolve, "UseFitsHeadersForHints": useFitsHeaders}
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
                captureResponse = json.loads(f.read().decode('utf-8'))                                                      # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Receipt']
        except Exception as e:
            self.logger.error('SgSolveImage   -> error: {0}'.format(e))
            return False, 'Request failed', ''

if __name__ == "__main__":

    import os
    cam = SGPro()
    dev, suc, mes = cam.SgCaptureImage(exposureLength=1, gain='50', path= os.getcwd()+'/test.fit')
    print(dev, suc, mes)
