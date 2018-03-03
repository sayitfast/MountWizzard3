############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import json
import logging
import platform
import time
import PyQt5
# packages for handling web interface to SGPro
from urllib import request
import requests


class SGPro:
    logger = logging.getLogger(__name__)

    CAMERASTATUS = {'ERROR': 'ERROR', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'DOWNLOADING', 'READY': 'DOWNLOADING', 'IDLE': 'IDLE', 'INTEGRATING': 'INTEGRATING'}

    def __init__(self, main, app, data):
        super().__init__()
        self.main = main
        self.app = app
        self.data = data

        self.tryConnectionCounter = 0

        self.host = '127.0.0.1'
        self.port = 59590
        self.ipSGProBase = 'http://' + self.host + ':' + str(self.port)
        self.ipSGPro = 'http://' + self.host + ':' + str(self.port) + '/json/reply/'
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
        if platform.system() == 'Windows':
            # sgpro only supported on local machine
            self.data['AppAvailable'], self.data['AppName'], self.data['AppInstallPath'] = self.app.checkRegistrationKeys('Sequence Generator')
            if self.data['AppAvailable']:
                self.app.messageQueue.put('Found: {0}\n'.format(self.data['AppName']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.data['AppName'], self.data['AppInstallPath']))
            else:
                self.logger.info('Application SGPro not found on computer')

    def getStatus(self):
        suc, state, message = self.SgGetDeviceStatus('Camera')
        if suc:
            self.data['AppStatus'] = 'OK'
            if state in self.CAMERASTATUS:
                if self.CAMERASTATUS[state] == 'DISCONNECTED':
                    self.data['CONNECTION']['CONNECT'] = 'Off'
                else:
                    self.data['CONNECTION']['CONNECT'] = 'On'
            else:
                self.logger.error('Unknown camera status: {0}, message: {1}'.format(state, message))
        else:
            self.data['AppStatus'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'

    def getCameraProps(self):
        value = self.SgGetCameraProps()
        if value['Success']:
            if 'GainValues' not in value:
                self.data['Gain'] = ['High']
            else:
                self.data['Gain'] = value['GainValues'][0]
            if value['SupportsSubframe']:
                self.data['CCD_FRAME'] = {}
                self.data['CCD_FRAME']['HEIGHT'] = value['NumPixelsX']
                self.data['CCD_FRAME']['WIDTH'] = value['NumPixelsY']
                self.data['CCD_FRAME']['X'] = 0
                self.data['CCD_FRAME']['Y'] = 0
            self.data['CCD_INFO'] = {}
            self.data['CCD_INFO']['CCD_MAX_X'] = value['NumPixelsX']
            self.data['CCD_INFO']['CCD_MAX_Y'] = value['NumPixelsY']

    def getImage(self, imageParams):
        suc, mes, guid = self.SgCaptureImage(binningMode=imageParams['Binning'],
                                             exposureLength=imageParams['Exposure'],
                                             iso=str(imageParams['Iso']),
                                             gain=imageParams['Gain'],
                                             speed=imageParams['Speed'],
                                             frameType='Light',
                                             filename=imageParams['File'],
                                             path=imageParams['BaseDirImages'],
                                             useSubframe=imageParams['CanSubframe'],
                                             posX=imageParams['OffX'],
                                             posY=imageParams['OffY'],
                                             width=imageParams['SizeX'],
                                             height=imageParams['SizeY'])
        self.logger.info('SgCaptureImage: {0}'.format(mes))
        if suc:
            while True:
                suc, path = self.SgGetImagePath(guid)
                if suc:
                    break
                else:
                    time.sleep(0.1)
                    PyQt5.QtWidgets.QApplication.processEvents()
            imageParams['Imagepath'] = path.replace('\\', '/')
        else:
            imageParams['Imagepath'] = ''
        imageParams['Message'] = mes
        self.logger.info('SgGetImagePath: {0}'.format(imageParams['Imagepath']))
        return imageParams

    def solveImage(self, imageParams):
        suc, mes, guid = self.SgSolveImage(imageParams['Imagepath'],
                                           RaHint=imageParams['RaJ2000'],
                                           DecHint=imageParams['DecJ2000'],
                                           ScaleHint=imageParams['ScaleHint'],
                                           BlindSolve=imageParams['Blind'],
                                           UseFitsHeaders=False)
        if not suc:
            self.logger.warning('Solver no start, message: {0}'.format(mes))
            imageParams['Message'] = mes
        while True:
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SgGetSolvedImageData(guid)
            mes = mes.strip('\n')
            if mes[:7] in ['Matched', 'Solve t', 'Valid s', 'succeed']:
                self.logger.info('Imaging parameters {0}'.format(imageParams))
                imageParams['RaJ2000Solved'] = float(ra_sol)
                imageParams['DecJ2000Solved'] = float(dec_sol)
                imageParams['Scale'] = float(scale)
                imageParams['Angle'] = float(angle)
                imageParams['TimeTS'] = float(timeTS)
                break
            elif mes != 'Solving':
                break
            else:
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
        imageParams['Message'] = mes
        return imageParams

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
            result = requests.post(self.ipSGPro + self.captureImagePath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            return result['Success'], result['Message'], result['Receipt']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''

    def SgGetCameraProps(self):
        # reference {}
        data = {}
        try:
            result = requests.post(self.ipSGPro + self.getCameraPropsPath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            return result
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', '', '', ''

    def SgGetDeviceStatus(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        data = {'Device': device}
        try:
            result = requests.post(self.ipSGPro + self.getDeviceStatusPath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            if 'Message' not in result:
                result['Message'] = 'None'
            return result['Success'], result['State'], result['Message']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', 'Request failed'

    def SgGetImagePath(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            result = requests.post(self.ipSGPro + self.getImagePath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            return result['Success'], result['Message']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetSolvedImageData(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            result = requests.post(self.ipSGPro + self.getSolvedImageDataPath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            return result['Success'], result['Message'], result['Ra'], result['Dec'], result['Scale'], result['Angle'], result['TimeToSolve']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', '', '', '', '', ''

    def SgSolveImage(self, path, RaHint=None, DecHint=None, ScaleHint=None, BlindSolve=False, UseFitsHeaders=False):
        # reference {"ImagePath":"String","RaHint":0,"DecHint":0,"ScaleHint":0,"BlindSolve":false,"UseFitsHeadersForHints":false}
        data = {"ImagePath": path, "BlindSolve": BlindSolve, "UseFitsHeadersForHints": UseFitsHeaders}
        if RaHint:
            data['RaHint'] = RaHint
        if DecHint:
            data['DecHint'] = DecHint
        if ScaleHint:
            data['ScaleHint'] = ScaleHint
        try:
            result = requests.post(self.ipSGPro + self.solveImagePath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            return result['Success'], result['Message'], result['Receipt']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''
