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

    # base definitions of class
    host = '127.0.0.1'
    port = 59590
    ipSGProBase = 'http://' + host + ':' + str(port)
    ipSGPro = 'http://' + host + ':' + str(port) + '/json/reply/'
    captureImagePath = 'SgCaptureImage'
    getCameraPropsPath = 'SgGetCameraProps'
    getDeviceStatusPath = 'SgGetDeviceStatus'
    getImagePath = 'SgGetImagePath'

    CAMERA_STATUS = {'ERROR': 'ERROR', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'DOWNLOADING', 'READY': 'DOWNLOADING', 'IDLE': 'IDLE', 'INTEGRATING': 'INTEGRATING'}

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data

        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = ''
        self.application['InstallPath'] = ''
        self.application['Status'] = ''
        self.application['Runtime'] = 'Sequence Generator.exe'

        if platform.system() == 'Windows':
            # sgpro only supported on local machine
            self.application['Available'], self.application['Name'], self.application['InstallPath'] = self.app.checkRegistrationKeys('Sequence Generator')
            if self.application['Available']:
                self.app.messageQueue.put('Found: {0}\n'.format(self.application['Name']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.application['Name'], self.application['InstallPath']))
            else:
                self.logger.info('Application SGPro not found on computer')

    def getStatus(self):
        suc, state, message = self.SgGetDeviceStatus('Camera')
        if suc:
            self.application['Status'] = 'OK'
            if state in self.CAMERA_STATUS:
                if self.CAMERA_STATUS[state] == 'DISCONNECTED':
                    self.data['CONNECTION']['CONNECT'] = 'Off'
                else:
                    self.data['CONNECTION']['CONNECT'] = 'On'
            else:
                self.logger.error('Unknown camera status: {0}, message: {1}'.format(state, message))
        else:
            self.application['Status'] = 'ERROR'
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
