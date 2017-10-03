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
import json
import logging
import time
# packages for handling web interface to SGPro
import urllib
from urllib import request

if platform.system() == 'Windows':
    # windows automation
    from pywinauto import Application, findwindows, application

from baseclasses.camera import MWCamera


class SGPro(MWCamera):
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

    def __init__(self, app):
        super(SGPro, self).__init__(app)
        self.ipSGProBase = 'http://localhost:59590'
        self.ipSGPro = 'http://localhost:59590/json/reply/'
        self.captureImagePath = 'SgCaptureImage'
        self.connectDevicePath = 'SgConnectDevicePath'
        self.disconnectDevicePath = 'SgDisconnectDevicePath'
        self.getCameraPropsPath = 'SgGetCameraProps'
        self.getDeviceStatusPath = 'SgGetDeviceStatus'
        self.enumerateDevicePath = 'SgEnumerateDevices'
        self.getImagePath = 'SgGetImagePath'
        self.getSolvedImageDataPath = 'SgGetSolvedImageData'
        self.solveImagePath = 'SgSolveImage'
        self.appExe = 'Sequence Generator.exe'
        self.tryConnectionCounter = 0

    def checkAppInstall(self):
        if platform.system() == 'Windows':
            self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('Sequence Generator')
            if self.appAvailable:
                self.app.messageQueue.put('Found: {0}'.format(self.appName))
                self.logger.info('Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
            else:
                self.logger.info('Application SGPro not found on computer')

    def checkAppStatus(self):
        reply = ''
        try:
            reply = request.urlopen(self.ipSGProBase, None, 2).getcode()
            self.appRunning = True
            self.appConnected = True
            self.tryConnectionCounter = 0
        except urllib.request.URLError:
            self.tryConnectionCounter += 1
            if self.tryConnectionCounter < 5:
                self.logger.info('SGPro is not running')
            elif self.tryConnectionCounter == 10:
                self.logger.info('No connection possible - stop logging this connection error')
            else:
                pass
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            self.appRunning = False
            self.appConnected = False
            self.appCameraConnected = False
        finally:
            if self.appConnected:
                # noinspection PyUnboundLocalVariable
                if str(reply) == '200':
                    success, response = self.SgGetDeviceStatus('Camera')
                    if success and response != 'DISCONNECTED':
                        suc, mes = self.SgGetDeviceStatus('PlateSolver')
                        if suc:
                            self.appCameraConnected = True
                        else:
                            self.appCameraConnected = False
                    else:
                        self.appCameraConnected = False
            else:
                self.appCameraConnected = False

    def connectCamera(self):
        pass

    def disconnectCamera(self):
        pass

    def connectApplication(self):
        if self.appRunning:
            self.appConnected = True

    def disconnectApplication(self):
        if self.appRunning:
            self.appConnected = False

    def getImage(self, modelData):
        suc, mes, guid = self.SgCaptureImage(binningMode=modelData['binning'],
                                             exposureLength=modelData['exposure'],
                                             iso=str(modelData['iso']),
                                             gain=modelData['gainValue'],
                                             speed=modelData['speed'],
                                             frameType='Light',
                                             filename=modelData['file'],
                                             path=modelData['base_dir_images'],
                                             useSubframe=modelData['canSubframe'],
                                             posX=modelData['offX'],
                                             posY=modelData['offY'],
                                             width=modelData['sizeX'],
                                             height=modelData['sizeY'])
        modelData['imagepath'] = ''
        self.logger.info('message: {0}'.format(mes))
        if suc:                                                                                                             # if we successfully starts imaging, we ca move on
            while True:                                                                                                     # waiting for the image download before proceeding
                suc, modelData['imagepath'] = self.SgGetImagePath(guid)                                                     # there is the image path, once the image is downloaded
                if suc:                                                                                                     # until then, the link is only the receipt
                    break                                                                                                   # stopping the loop
                else:                                                                                                       # otherwise
                    time.sleep(0.5)                                                                                         # wait for 0.5 seconds
        return suc, mes, modelData

    def solveImage(self, modelData):
        suc, mes, guid = self.SgSolveImage(modelData['imagepath'],
                                           scaleHint=modelData['scaleHint'],
                                           blindSolve=modelData['blind'],
                                           useFitsHeaders=modelData['usefitsheaders'])
        if not suc:
            self.logger.warning('no start {0}'.format(mes))
            return False, mes, modelData
        while True:                                                                                                         # retrieving solving data in loop
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SgGetSolvedImageData(guid)                               # retrieving the data from solver
            mes = mes.strip('\n')                                                                                           # sometimes there are heading \n in message
            if mes[:7] in ['Matched', 'Solve t', 'Valid s', 'succeed']:                                                     # if there is success, we can move on
                self.logger.info('modelData {0}'.format(modelData))
                solved = True
                modelData['dec_sol'] = float(dec_sol)                                                                       # convert values to float, should be stored in float not string
                modelData['ra_sol'] = float(ra_sol)
                modelData['scale'] = float(scale)
                modelData['angle'] = float(angle)
                modelData['timeTS'] = float(timeTS)
                break
            elif mes != 'Solving':                                                                                          # general error
                solved = False
                break
            # TODO: clarification should we again introduce model run cancel during plate solving -> very complicated solver should cancel if not possible after some time
            # elif app.model.cancel:
            #    solved = False
            #    break
            else:                                                                                                           # otherwise
                if modelData['blind']:                                                                                      # when using blind solve, it takes 30-60 s
                    time.sleep(5)                                                                                           # therefore slow cycle
                else:                                                                                                       # local solver takes 1-2 s
                    time.sleep(.25)                                                                                         # therefore quicker cycle
        return solved, mes, modelData

    def getCameraProps(self):
        return self.SgGetCameraProps()

    def getCameraStatus(self):
        if self.appConnected:
            suc, mes = self.SgGetDeviceStatus('Camera')
            if suc:
                self.cameraStatus = mes
            else:
                self.cameraStatus = 'Error'

    def SgCaptureImage(self, binningMode=1, exposureLength=1,
                       gain=None, iso=None, speed=None, frameType=None, filename=None,
                       path=None, useSubframe=False, posX=0, posY=0,
                       width=1, height=1):
        # reference {"BinningMode":0,"ExposureLength":0,"Gain":"String","Speed":"Normal","FrameType":"Light",
        # reference "Path":"String","UseSubframe":false,"X":0,"Y":0,"Width":0,"Height":0}
        data = {"BinningMode": binningMode, "ExposureLength": exposureLength, "UseSubframe": useSubframe, "X": posX, "Y": posY,
                "Width": width, "Height": height}
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
            req = request.Request(self.ipSGPro + self.captureImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Receipt']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''

    def SgGetCameraProps(self):
        # reference {}
        data = {}
        try:
            req = request.Request(self.ipSGPro + self.getCameraPropsPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","NumPixelsX":0,"NumPixelsY":0,"SupportsSubframe":false}
            if 'GainValues' not in captureResponse:
                captureResponse['GainValues'] = ['High']
            return captureResponse['Success'], captureResponse['Message'], int(captureResponse['NumPixelsX']), int(captureResponse['NumPixelsY']), captureResponse['SupportsSubframe'], captureResponse['GainValues'][0]
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
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
            self.logger.error('error: {0}'.format(e))
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
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed'

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
            self.logger.error('error: {0}'.format(e))
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
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''


if __name__ == "__main__":
    from baseclasses.camera import MWCamera
    import time
    max = 20
    cam = SGPro(MWCamera)
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
