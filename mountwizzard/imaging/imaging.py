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
import logging
import os
import time
import platform
import datetime
import math
import random
import shutil
import sys
import PyQt5
import queue
from astrometry import transform
import astropy.io.fits as pyfits
from imaging import none_camera
from imaging import indi_camera
if platform.system() == 'Windows':
    from imaging import maximdl_camera
    from imaging import sgpro_camera
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    from imaging import theskyx_camera


class Imaging(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    # signals to be used for others
    # putting status to gui
    cameraStatusText = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)
    imagingCancel = PyQt5.QtCore.pyqtSignal()

    # putting status to processing
    imageIntegrated = PyQt5.QtCore.pyqtSignal()
    imageDownloaded = PyQt5.QtCore.pyqtSignal()
    imageSaved = PyQt5.QtCore.pyqtSignal()

    # where to place the images
    IMAGEDIR = os.getcwd().replace('\\', '/') + '/images'
    CYCLE_STATUS = 1000
    CYCLE_COMMAND = 200

    def __init__(self, app, thread):
        super().__init__()
        # make main sources available
        self.app = app
        self.thread = thread
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.imagingCommandQueue = queue.Queue()
        self.mutexChooser = PyQt5.QtCore.QMutex()
        self.mutexData = PyQt5.QtCore.QMutex()

        # class data
        self.data = dict()
        self.data['CONNECTION'] = {'CONNECT': 'Off'}

        # external classes
        self.transform = transform.Transform(self.app)
        if platform.system() == 'Windows':
            self.SGPro = sgpro_camera.SGPro(self, self.app, self.data)
            self.MaximDL = maximdl_camera.MaximDL(self, self.app, self.data)
        self.INDICamera = indi_camera.INDICamera(self, self.app, self.data)
        self.NoneCam = none_camera.NoneCamera(self, self.app, self.data)

        # set the camera handler to default position
        self.cameraHandler = self.NoneCam

        # signal slot links
        self.imagingCancel.connect(self.setCancelImaging)
        self.app.ui.pd_chooseImaging.activated.connect(self.chooseImaging)

    def initConfig(self):
        # build the drop down menu
        self.app.ui.pd_chooseImaging.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseImaging.setView(view)
        if self.NoneCam.application['Available']:
            self.app.ui.pd_chooseImaging.addItem('No Camera - ' + self.NoneCam.application['Name'])
        if self.INDICamera.application['Available']:
            self.app.ui.pd_chooseImaging.addItem('INDI Camera - ' + self.INDICamera.application['Name'])
        if platform.system() == 'Windows':
            if self.SGPro.application['Available']:
                self.app.ui.pd_chooseImaging.addItem('SGPro - ' + self.SGPro.application['Name'])
            if self.MaximDL.application['Available']:
                self.app.ui.pd_chooseImaging.addItem('MaximDL - ' + self.MaximDL.application['Name'])
        # if platform.system() == 'Windows' or platform.system() == 'Darwin':
        #    if self.workerTheSkyX.data['AppAvailable']:
        #        self.app.ui.pd_chooseImaging.addItem('TheSkyX - ' + self.workerTheSkyX.data['AppName'])
        # load the config data
        try:
            if 'ImagingApplication' in self.app.config:
                self.app.ui.pd_chooseImaging.setCurrentIndex(int(self.app.config['ImagingApplication']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.chooseImaging()

    def storeConfig(self):
        self.app.config['ImagingApplication'] = self.app.ui.pd_chooseImaging.currentIndex()

    def setCancelImaging(self):
        self.cameraHandler.mutexCancel.lock()
        self.cameraHandler.cancel = True
        self.cameraHandler.mutexCancel.unlock()

    def chooseImaging(self):
        self.mutexChooser.lock()
        self.stop()
        if self.app.ui.pd_chooseImaging.currentText().startswith('No Camera'):
            self.cameraHandler = self.NoneCam
            self.logger.info('Actual camera is None')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('SGPro'):
            self.cameraHandler = self.SGPro
            self.logger.info('Actual camera is SGPro')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('MaximDL'):
            self.cameraHandler = self.MaximDL
            self.logger.info('Actual camera is MaximDL')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('INDI'):
            self.cameraHandler = self.INDICamera
            self.logger.info('Actual camera is INDI Camera')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('TheSkyX'):
            self.cameraHandler = self.TheSkyX
            self.logger.info('Actual camera is TheSkyX')
        self.cameraStatusText.emit('')
        self.thread.start()
        self.mutexChooser.unlock()

    def run(self):
        self.logger.info('imaging started')
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.cameraHandler.start()
        self.getDeviceStatus()
        self.doCommandQueue()

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()
        self.logger.info('imaging stopped')

    def destruct(self):
        self.cameraHandler.stop()

    def doCommandQueue(self):
        if not self.imagingCommandQueue.empty():
            imageParams = self.imagingCommandQueue.get()
            self.captureImage(imageParams)
        # loop
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_COMMAND, self.doCommandQueue)

    def captureImage(self, imageParams):
        imageParams['Imagepath'] = ''
        if self.cameraHandler.application['Status'] != 'OK':
            imageParams['Imagepath'] = 'False'
            return
        # preparation for imaging: gathering all the informations for taking a picture from gui
        imageParams['Imagepath'] = ''
        if self.data['CONNECTION']['CONNECT'] == 'Off':
            imageParams['Imagepath'] = 'False'
            return
        self.cameraHandler.getCameraProps()
        imageParams['BaseDirImages'] = self.IMAGEDIR + '/' + imageParams['Directory']
        if not os.path.isdir(imageParams['BaseDirImages']):
            os.makedirs(imageParams['BaseDirImages'])
        imageParams['Binning'] = int(float(self.app.ui.cameraBin.value()))
        imageParams['Exposure'] = int(float(self.app.ui.cameraExposure.value()))
        imageParams['Iso'] = int(float(self.app.ui.isoSetting.value()))
        if self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            imageParams['SizeX'] = int(float(self.data['CCD_INFO']['CCD_MAX_X']) * scaleSubframe)
            imageParams['SizeY'] = int(float(self.data['CCD_INFO']['CCD_MAX_Y']) * scaleSubframe)
            imageParams['OffX'] = int((float(self.data['CCD_INFO']['CCD_MAX_X']) - imageParams['SizeX']) / 2)
            imageParams['OffY'] = int((float(self.data['CCD_INFO']['CCD_MAX_Y']) - imageParams['SizeY']) / 2)
            imageParams['CanSubframe'] = True
        else:
            imageParams['SizeX'] = int(float(self.data['CCD_INFO']['CCD_MAX_X']))
            imageParams['SizeY'] = int(float(self.data['CCD_INFO']['CCD_MAX_Y']))
            imageParams['OffX'] = 0
            imageParams['OffY'] = 0
            imageParams['CanSubframe'] = False
        if 'Gain' in self.data:
            imageParams['Gain'] = self.data['Gain']
        else:
            imageParams['Gain'] = 'NotSet'
        if self.app.ui.checkFastDownload.isChecked():
            imageParams['Speed'] = 'HiSpeed'
        else:
            imageParams['Speed'] = 'Normal'
        self.cameraHandler.getImage(imageParams)
        # if we got an image, than show it
        self.app.imageWindow.signalShowFitsImage.emit(imageParams['Imagepath'])

    def getDeviceStatus(self):
        self.cameraHandler.getStatus()
        # get status to gui
        if not self.cameraHandler.application['Available']:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'gray')
        elif self.cameraHandler.application['Status'] == 'ERROR':
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'red')
        elif self.cameraHandler.application['Status'] == 'OK':
            if self.data['CONNECTION']['CONNECT'] == 'Off':
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'yellow')
            else:
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'green')
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS, self.getDeviceStatus)

    def updateApplicationName(self):
        # updating camera name if possible
        for i in range(0, self.app.ui.pd_chooseImaging.count()):
            if self.app.ui.pd_chooseImaging.itemText(i).startswith('No Camera'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('SGPro'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('MaximDL'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('INDI'):
                self.app.ui.pd_chooseImaging.setItemText(i, 'INDI Camera - ' + self.INDICamera.application['Name'])
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('TheSkyX'):
                pass
