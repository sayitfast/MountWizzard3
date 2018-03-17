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
from imaging import noneCamera
from imaging import indicamera
if platform.system() == 'Windows':
    from imaging import maximdl_image
    from imaging import sgpro_image
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    from imaging import theskyx_image


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

    def __init__(self, app, thread):
        super().__init__()
        # make main sources available
        self.app = app
        self.thread = thread
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.imagingCommandQueue = queue.Queue()
        self.mutexChooser = PyQt5.QtCore.QMutex()

        # class data
        self.data = dict()
        self.data['CONNECTION'] = {'CONNECT': 'Off'}

        # external classes
        self.transform = transform.Transform(self.app)
        if platform.system() == 'Windows':
            self.SGPro = sgpro_image.SGPro(self, self.app, self.data)
        self.INDICamera = indicamera.INDICamera(self, self.app, self.data)
        self.NoneCam = noneCamera.NoneCamera(self, self.app, self.data)

        # shortcuts for better usage
        self.cameraHandler = self.NoneCam

        # signal slot links
        self.imagingCancel.connect(self.setCancelImaging)
        self.app.ui.pd_chooseImaging.currentIndexChanged.connect(self.chooseImaging)

    def initConfig(self):
        # build the drop down menu
        self.app.ui.pd_chooseImaging.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseImaging.setView(view)

        if self.NoneCam.application['Available']:
            self.app.ui.pd_chooseImaging.addItem('No Cam - ' + self.NoneCam.application['Name'])
        if self.INDICamera.application['Available']:
            self.app.ui.pd_chooseImaging.addItem('INDI Camera - ' + self.INDICamera.application['Name'])
        if platform.system() == 'Windows':
            if self.SGPro.application['Available']:
                self.app.ui.pd_chooseImaging.addItem('SGPro - ' + self.SGPro.application['Name'])
        #    if self.workerMaximDL.data['AppAvailable']:
        #        self.app.ui.pd_chooseImaging.addItem('MaximDL - ' + self.workerMaximDL.data['AppName'])
        #if platform.system() == 'Windows' or platform.system() == 'Darwin':
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
        if self.app.ui.pd_chooseImaging.currentText().startswith('No Cam'):
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
        self.mutexChooser.unlock()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.getStatus()
        while self.isRunning:
            if not self.imagingCommandQueue.empty():
                imageParams = self.imagingCommandQueue.get()
                self.captureImage(imageParams)
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

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
        if 'CCD_INFO' not in self.data:
            imageParams['Imagepath'] = 'False'
            return
        self.cameraHandler.getCameraProps()
        imageParams['BaseDirImages'] = self.IMAGEDIR + '/' + imageParams['Directory']
        if not os.path.isdir(imageParams['BaseDirImages']):
            os.makedirs(imageParams['BaseDirImages'])
        imageParams['Binning'] = int(float(self.app.ui.cameraBin.value()))
        imageParams['Exposure'] = int(float(self.app.ui.cameraExposure.value()))
        imageParams['Iso'] = int(float(self.app.ui.isoSetting.value()))
        imageParams['Blind'] = self.app.ui.checkUseBlindSolve.isChecked()
        imageParams['ScaleHint'] = float(self.app.ui.pixelSize.value()) * imageParams['Binning'] * 206.6 / float(self.app.ui.focalLength.value())
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
        if 'Binning' in imageParams:
            imageParams['SizeX'] = int(imageParams['SizeX'] / imageParams['Binning'])
            imageParams['SizeY'] = int(imageParams['SizeY'] / imageParams['Binning'])
        self.cameraHandler.getImage(imageParams)

    def getStatus(self):
        self.cameraHandler.getStatus()
        # get status to gui
        if not self.cameraHandler.application['Available']:
            self.app.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')
        elif self.cameraHandler.application['Status'] == 'ERROR':
            self.app.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: red; color: black;}')
        elif self.cameraHandler.application['Status'] == 'OK':
            if self.data['CONNECTION']['CONNECT'] == 'Off':
                self.app.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')
            else:
                self.app.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: green; color: black;}')

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS, self.getStatus)

    def updateApplicationName(self):
        # updating camera name if possible
        for i in range(0, self.app.ui.pd_chooseImaging.count()):
            if self.app.ui.pd_chooseImaging.itemText(i).startswith('No Cam'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('SGPro'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('MaximDL'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('INDI'):
                self.app.ui.pd_chooseImaging.setItemText(i, 'INDI Camera - ' + self.INDICamera.application['Name'])
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('TheSkyX'):
                pass
