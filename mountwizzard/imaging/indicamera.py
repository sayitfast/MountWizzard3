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

        self.app.workerINDI.receivedImage.connect(lambda: self.setReceivedImage())

    def setReceivedImage(self):
        self.mutexReceived.lock()
        self.cancel = True
        self.mutexReceived.unlock()

    def setCancelImaging(self):
        self.mutexCancel.lock()
        self.cancel = True
        self.mutexCancel.unlock()

    def getStatus(self):
        # check if INDIClient is running and camera device is there
        if self.app.workerINDI.isRunning:
            self.application['Available'] = True
            if self.app.workerINDI.cameraDevice != '':
                self.application['Status'] = 'OK'
                self.application['Name'] = self.app.workerINDI.cameraDevice
                # check if data from INDI server already received
                if 'CONNECTION' in self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]:
                    check = self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]
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
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()

        binning = int(float(imageParams['Binning']))
        exposure = int(float(imageParams['Exposure']))
        filename = imageParams['File']
        path = imageParams['BaseDirImages']
        imagePath = path + '/' + filename
        self.app.workerINDI.imagePath = imagePath

        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                # Enable BLOB mode.
                self.app.INDICommandQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.app.workerINDI.cameraDevice}))
                # set to raw - no compression mode
                self.app.INDICommandQueue.put(
                    indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CCD_COMPRESS'})],
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
                    indiXML.newNumberVector([indiXML.oneNumber(imageParams['SizeX'], indi_attr={'name': 'WIDTH'}),
                                             indiXML.oneNumber(imageParams['SizeY'], indi_attr={'name': 'HEIGHT'}),
                                             indiXML.oneNumber(imageParams['OffX'], indi_attr={'name': 'X'}),
                                             indiXML.oneNumber(imageParams['OffY'], indi_attr={'name': 'Y'})],
                                            indi_attr={'name': 'CCD_FRAME', 'device': self.app.workerINDI.cameraDevice}))
                # Request image.
                self.app.INDICommandQueue.put(
                    indiXML.newNumberVector([indiXML.oneNumber(exposure, indi_attr={'name': 'CCD_EXPOSURE_VALUE'})],
                                            indi_attr={'name': 'CCD_EXPOSURE', 'device': self.app.workerINDI.cameraDevice}))

                self.mutexReceived.lock()
                self.receivedImage = False
                self.mutexReceived.unlock()

                while not self.receivedImage and not self.cancel:
                    if 'CONNECTION' and 'CCD_EXPOSURE' in self.data['Camera']:
                        if self.data['CONNECTION']['CONNECT'] == 'On':
                            if self.data['Camera']['CCD_EXPOSURE']['state'] in ['Busy']:
                                if float(self.data['Camera']['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE']):
                                    self.data['Camera']['Status'] = 'INTEGRATING'
                                    self.cameraStatusText.emit('INTEGRATE')
                                else:
                                    self.data['Camera']['Status'] = 'DOWNLOADING'
                                    self.cameraStatusText.emit('DOWNLOAD')
                            elif self.data['Camera']['CCD_EXPOSURE']['state'] in ['Ok', 'Idle']:
                                if not self.receivedImage:
                                    self.data['Camera']['Status'] = 'INTEGRATING'
                                    self.cameraStatusText.emit('INTEGRATE')
                                else:
                                    self.data['Camera']['Status'] = 'IDLE'
                                    self.cameraStatusText.emit('IDLE')
                            elif self.data['Camera']['CCD_EXPOSURE']['state'] == 'Error':
                                self.data['Camera']['Status'] = 'ERROR'
                                self.cameraStatusText.emit('ERROR')
                            self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
                        else:
                            self.app.workerModelingDispatcher.signalStatusCamera.emit(2)
                            self.data['Camera']['Status'] = 'DISCONNECTED'
                            self.cameraStatusText.emit('DISCONN')
                    else:
                        self.data['Camera']['Status'] = 'ERROR'
                        self.cameraStatusText.emit('ERROR')
                    if 'CCD_EXPOSURE' in self.data['Camera']:
                        self.cameraExposureTime.emit('{0:02.0f}'.format(float(self.data['Camera']['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'])))
                else:
                    self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'
                    self.app.workerModelingDispatcher.signalStatusCamera.emit(1)
                    self.cameraStatusText.emit('---')
                    self.cameraExposureTime.emit('---')

                    PyQt5.QtWidgets.QApplication.processEvents()
            imageParams['Imagepath'] = self.app.workerINDI.imagePath
        else:
            imageParams['Imagepath'] = ''

    def connectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'Off':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))

    def disconnectCamera(self):
        if self.app.workerINDI.cameraDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.cameraDevice]['CONNECTION']['CONNECT'] == 'On':
                self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.cameraDevice}))
