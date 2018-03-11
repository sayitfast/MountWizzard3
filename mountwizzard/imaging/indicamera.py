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
import logging
import PyQt5
import time
import indi.indi_xml as indiXML


class INDICamera:
    logger = logging.getLogger(__name__)

    # timeout is 40 seconds
    MAX_TIMEOUT = 40

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

    def setReceivedImage(self, status):
        self.mutexReceived.lock()
        if status:
            self.receivedImage = True
        else:
            self.setCancelImaging()
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
            self.main.cameraStatusText.emit('Not OK')

    def getCameraProps(self):
        if self.application['Status'] != 'OK':
            return
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

        binning = int(float(imageParams['Binning']))
        exposure = int(float(imageParams['Exposure']))
        filename = imageParams['File']
        path = imageParams['BaseDirImages']
        imagePath = path + '/' + filename
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
            #self.app.INDICommandQueue.put(
            #    indiXML.newNumberVector([indiXML.oneNumber(imageParams['SizeX'], indi_attr={'name': 'WIDTH'}),
            #                             indiXML.oneNumber(imageParams['SizeY'], indi_attr={'name': 'HEIGHT'}),
            #                             indiXML.oneNumber(imageParams['OffX'], indi_attr={'name': 'X'}),
            #                             indiXML.oneNumber(imageParams['OffY'], indi_attr={'name': 'Y'})],
            #                            indi_attr={'name': 'CCD_FRAME', 'device': self.app.workerINDI.cameraDevice}))
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
        timeStart = time.time()

        # waiting for start integrating
        self.main.cameraStatusText.emit('START')
        while not self.cancel:
            if time.time() - timeStart > self.MAX_TIMEOUT:
                self.main.cameraStatusText.emit('TIMEOUT')
                break
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
            if time.time() - timeStart > self.MAX_TIMEOUT:
                self.main.cameraStatusText.emit('TIMEOUT')
                break
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
            if time.time() - timeStart > self.MAX_TIMEOUT:
                self.main.cameraStatusText.emit('TIMEOUT')
                break
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
            if time.time() - timeStart > self.MAX_TIMEOUT:
                self.main.cameraStatusText.emit('TIMEOUT')
                break
            if self.receivedImage:
                break
            time.sleep(0.1)

        # finally idle
        self.main.imageSaved.emit()
        self.main.cameraStatusText.emit('IDLE')
        self.main.cameraExposureTime.emit('')
        imageParams['Imagepath'] = self.app.workerINDI.imagePath
        self.data['Imaging'] = False

    def connectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'Off':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))

    def disconnectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))
