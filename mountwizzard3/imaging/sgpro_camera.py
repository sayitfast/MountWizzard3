############################################################
# -*- coding: utf-8 -*-
#
#       #   #  #   #   #  ####
#      ##  ##  #  ##  #     #
#     # # # #  # # # #     ###
#    #  ##  #  ##  ##        #
#   #   #   #  #   #     ####
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.6.4
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import json
import logging
import platform
import time
import PyQt5
import requests
from baseclasses import checkIP


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
        self.cancel = False
        self.checkIP = checkIP.CheckIP()
        self.mutexCancel = PyQt5.QtCore.QMutex()

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
                self.app.messageQueue.put('Found Imaging: {0}\n'.format(self.application['Name']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.application['Name'], self.application['InstallPath']))
            else:
                self.logger.info('Application SGPro not found on computer')

    def start(self):
        pass

    def stop(self):
        pass

    def getStatus(self):
        if self.checkIP.checkIPAvailable(self.host, self.port):
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
            self.data['CCD_INFO'] = {}
            self.data['CCD_INFO']['CCD_MAX_X'] = value['NumPixelsX']
            self.data['CCD_INFO']['CCD_MAX_Y'] = value['NumPixelsY']

    def getImage(self, imageParams):
        path = ''
        self.data['Imaging'] = True
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()

        # waiting for start integrating
        self.main.cameraStatusText.emit('START')
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
        if not suc:
            self.logger.warning('Imaging no start, message: {0}'.format(mes))
            self.main.cameraStatusText.emit('ERROR')
            imageParams['Imagepath'] = ''
            self.mutexCancel.lock()
            self.cancel = True
            self.mutexCancel.unlock()

        # loop for integrating
        self.main.cameraStatusText.emit('INTEGRATE')
        # wait for start integrating
        while not self.cancel:
            suc, state, message = self.SgGetDeviceStatus('Camera')
            if 'integrating' in message:
                break
            time.sleep(0.1)
        # bow for the duration
        while not self.cancel:
            suc, state, message = self.SgGetDeviceStatus('Camera')
            if 'downloading' in message or 'ready' in message or 'idle' in message:
                break
            time.sleep(0.1)

        # Loop for downloading
        self.main.imageIntegrated.emit()
        self.main.cameraStatusText.emit('DOWNLOAD')
        while not self.cancel:
            suc, path = self.SgGetImagePath(guid)
            if suc:
                break
            time.sleep(0.1)

        # Loop for saving
        self.main.imageDownloaded.emit()
        self.main.cameraStatusText.emit('SAVING')
        while not self.cancel:
            suc, state, message = self.SgGetDeviceStatus('Camera')
            if 'ready' in message or 'idle' in message:
                break
            time.sleep(0.1)

        # finally idle
        self.main.cameraStatusText.emit('IDLE')
        self.main.cameraExposureTime.emit('')
        imageParams['Imagepath'] = path.replace('\\', '/')

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
