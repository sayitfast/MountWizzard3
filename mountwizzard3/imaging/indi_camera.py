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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import PyQt5
import time
import indi.indi_xml as indiXML


class INDICamera:
    logger = logging.getLogger(__name__)

    # timeout for getting an download is 30 seconds
    MAX_DOWNLOAD_TIMEOUT = 30
    START_CAMERA_TIMEOUT = 3

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.cancel = False
        self.mutexCancel = PyQt5.QtCore.QMutex()
        self.mutexReceived = PyQt5.QtCore.QMutex()

        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = ''
        self.application['InstallPath'] = ''
        self.application['Status'] = ''
        self.application['Runtime'] = 'Sequence Generator.exe'

        self.counter = 0
        self.receivedImage = True

        self.application['Status'] = ''
        self.application['CONNECTION'] = {'CONNECT': 'Off'}
        self.application['Available'] = True
        self.application['Name'] = 'INDICamera'
        self.application['InstallPath'] = ''

        self.app.workerINDI.receivedImage.connect(self.setReceivedImage)

    def start(self):
        # connect the camera if not present
        timeStart = time.time()
        while True:
            if time.time() - timeStart > self.START_CAMERA_TIMEOUT:
                self.app.messageQueue.put('Timeout connect camera\n')
                break
            if self.app.workerINDI.cameraDevice:
                if 'CONNECTION' in self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]:
                    # Enable BLOB mode it also enables listen to send images
                    self.app.INDICommandQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.app.workerINDI.cameraDevice}))
                    break
            time.sleep(0.1)
        self.connect()

    def stop(self):
        pass

    def setReceivedImage(self, status):
        self.mutexReceived.lock()
        if status:
            self.receivedImage = True
        else:
            self.receivedImage = False
        self.mutexReceived.unlock()

    def getStatus(self):
        # check if INDIClient is running and camera device is there
        if self.app.workerINDI.isRunning:
            self.application['Available'] = True
            if self.app.workerINDI.cameraDevice != '':
                self.application['Status'] = 'OK'
                self.application['Name'] = self.app.workerINDI.cameraDevice
                # check if data from INDI server already received
                if 'CONNECTION' in self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]:
                    self.data['CONNECTION']['CONNECT'] = self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT']
                else:
                    self.logger.error('Unknown camera status')
            else:
                self.application['Status'] = 'ERROR'
        else:
            self.application['Available'] = False

    def getCameraProps(self):
        self.data['Gain'] = 'High'
        self.data['Speed'] = 'High'
        self.data['CCD_INFO'] = {}
        self.data['CCD_INFO']['CCD_MAX_X'] = self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CCD_INFO']['CCD_MAX_X']
        self.data['CCD_INFO']['CCD_MAX_Y'] = self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CCD_INFO']['CCD_MAX_Y']

    def getImage(self, imageParams):
        if self.application['Status'] != 'OK':
            return
        self.data['Imaging'] = True
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()

        binning = int(imageParams['Binning'])
        exposure = int(imageParams['Exposure'])
        filename = imageParams['File']
        path = imageParams['BaseDirImages']
        imagePath = path + '/' + filename
        # setting image path in INDI client to know where to store the image
        self.app.workerINDI.imagePath = imagePath

        cam = self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]
        if self.app.workerINDI.cameraDevice != '' and cam['CONNECTION']['CONNECT'] == 'On':
            # Enable BLOB mode.
            self.app.INDICommandQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.app.workerINDI.cameraDevice}))
            # set to raw - no compression mode
            self.app.INDICommandQueue.put(
                indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CCD_COMPRESS'})],
                                        indi_attr={'name': 'CCD_COMPRESSION', 'device': self.app.workerINDI.cameraDevice}))
            # set frame type
            self.app.INDICommandQueue.put(
                indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'FRAME_LIGHT'})],
                                        indi_attr={'name': 'CCD_FRAME_TYPE', 'device': self.app.workerINDI.cameraDevice}))
            # set binning
            self.app.INDICommandQueue.put(
                indiXML.newNumberVector([indiXML.oneNumber(binning, indi_attr={'name': 'HOR_BIN'}),
                                         indiXML.oneNumber(binning, indi_attr={'name': 'VER_BIN'})],
                                        indi_attr={'name': 'CCD_BINNING', 'device': self.app.workerINDI.cameraDevice}))
            # set subframe
            self.app.INDICommandQueue.put(
                indiXML.newNumberVector([indiXML.oneNumber(imageParams['OffX'], indi_attr={'name': 'X'}),
                                         indiXML.oneNumber(imageParams['OffY'], indi_attr={'name': 'Y'}),
                                         indiXML.oneNumber(imageParams['SizeX'], indi_attr={'name': 'WIDTH'}),
                                         indiXML.oneNumber(imageParams['SizeY'], indi_attr={'name': 'HEIGHT'})],
                                        indi_attr={'name': 'CCD_FRAME', 'device': self.app.workerINDI.cameraDevice}))
            # Request image.
            self.app.INDICommandQueue.put(
                indiXML.newNumberVector([indiXML.oneNumber(exposure, indi_attr={'name': 'CCD_EXPOSURE_VALUE'})],
                                        indi_attr={'name': 'CCD_EXPOSURE', 'device': self.app.workerINDI.cameraDevice}))
        else:
            self.mutexCancel.lock()
            self.cancel = True
            self.mutexCancel.unlock()

        self.mutexReceived.lock()
        self.receivedImage = False
        self.mutexReceived.unlock()

        # waiting for start integrating
        self.main.cameraStatusText.emit('START')
        while not self.cancel:
            if 'CONNECTION' and 'CCD_EXPOSURE' in cam:
                if cam['CONNECTION']['CONNECT'] == 'On':
                    if cam['CCD_EXPOSURE']['state'] in ['Busy']:
                        break
                else:
                    self.main.cameraStatusText.emit('DISCONN')
            else:
                self.main.cameraStatusText.emit('ERROR')
            time.sleep(0.1)

        # loop for integrating
        self.main.cameraStatusText.emit('INTEGRATE')
        while not self.cancel:
            if 'CONNECTION' and 'CCD_EXPOSURE' in cam:
                if cam['CONNECTION']['CONNECT'] == 'On':
                    if not float(cam['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE']):
                        break
                else:
                    self.main.cameraStatusText.emit('DISCONN')
            else:
                self.main.cameraStatusText.emit('ERROR')
            if 'CCD_EXPOSURE' in cam:
                self.main.cameraExposureTime.emit('{0:02.0f}'.format(float(cam['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'])))
            else:
                self.main.cameraExposureTime.emit('')
            time.sleep(0.1)

        # loop for download
        self.main.imageIntegrated.emit()
        self.main.cameraStatusText.emit('DOWNLOAD')
        while not self.cancel:
            if 'CCD_EXPOSURE' in cam:
                if cam['CONNECTION']['CONNECT'] == 'On':
                    if cam['CCD_EXPOSURE']['state'] in ['Ok', 'Idle']:
                        break
                    elif cam['CCD_EXPOSURE']['state'] == 'Error':
                        self.main.cameraStatusText.emit('ERROR')
                else:
                    self.main.cameraStatusText.emit('DISCONN')
            else:
                self.main.cameraStatusText.emit('ERROR')
            if 'CCD_EXPOSURE' in cam:
                self.main.cameraExposureTime.emit('{0:02.0f}'.format(float(cam['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'])))
            else:
                self.main.cameraExposureTime.emit('')
            time.sleep(0.1)

        # loop for saving
        self.main.imageDownloaded.emit()
        self.main.cameraStatusText.emit('SAVING')
        while not self.cancel:
            if self.receivedImage:
                break
            time.sleep(0.1)

        # finally idle
        self.main.cameraStatusText.emit('IDLE')
        self.main.cameraExposureTime.emit('')
        imageParams['Imagepath'] = self.app.workerINDI.imagePath
        self.app.workerINDI.imagePath = ''

    def connect(self):
        # connect the camera
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'Off':
                self.app.INDICommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))

    def disconnect(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                self.app.INDICommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))
