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
import threading
import datetime
import math
import random
import shutil
import sys
import PyQt5
import queue
from astrometry import transform
import astropy.io.fits as pyfits
from camera import none
from camera import indicamera
if platform.system() == 'Windows':
    from camera import maximdl
    from camera import sgpro
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    from camera import theskyx


class ImagingApps:
    logger = logging.getLogger(__name__)

    IMAGEDIR = os.getcwd().replace('\\', '/') + '/images'
    CAPTUREFILE = 'modeling'

    def __init__(self, app):
        # make main sources available
        self.app = app
        self.transform = transform.Transform(self.app)
        self.imagingCommandQueue = queue.Queue()
        # make imaging applications available
        if platform.system() == 'Windows':
            self.threadSGPro = PyQt5.QtCore.QThread()
            self.workerSGPro = sgpro.SGPro(self.app, self.threadSGPro, self.imagingCommandQueue)
            self.threadSGPro.setObjectName("SGPro")
            self.workerSGPro.moveToThread(self.threadSGPro)
            self.threadSGPro.started.connect(self.workerSGPro.run)

            self.threadMaximDL = PyQt5.QtCore.QThread()
            self.workerMaximDL = maximdl.MaximDLCamera(self.app, self.threadMaximDL, self.imagingCommandQueue)
            self.threadMaximDL.setObjectName("MaximDL")
            self.workerMaximDL.moveToThread(self.threadMaximDL)
            self.threadMaximDL.started.connect(self.workerMaximDL.run)

        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.threadTheSkyX = PyQt5.QtCore.QThread()
            self.workerTheSkyX = theskyx.TheSkyX(self.app, self.threadTheSkyX, self.imagingCommandQueue)
            self.threadTheSkyX.setObjectName("TheSkyX")
            self.workerTheSkyX.moveToThread(self.threadTheSkyX)
            self.threadTheSkyX.started.connect(self.workerTheSkyX.run)

        self.threadNoneCam = PyQt5.QtCore.QThread()
        self.workerNoneCam = none.NoneCamera(self.app, self.threadNoneCam, self.imagingCommandQueue)
        self.threadNoneCam.setObjectName("NoneCamera")
        self.workerNoneCam.moveToThread(self.threadNoneCam)
        self.threadNoneCam.started.connect(self.workerNoneCam.run)

        self.threadINDICamera = PyQt5.QtCore.QThread()
        self.workerINDICamera = indicamera.INDICamera(self.app, self.threadINDICamera, self.imagingCommandQueue)
        self.threadINDICamera.setObjectName("INDICamera")
        self.workerINDICamera.moveToThread(self.threadINDICamera)
        self.threadINDICamera.started.connect(self.workerINDICamera.run)

        # select default application
        self.imagingWorkerCameraAppHandler = self.workerNoneCam
        self.imagingThreadCameraAppHandler = self.threadNoneCam
        self.imagingWorkerCameraAppHandler.cameraStatus.connect(self.setStatusCamera)
        self.imagingWorkerCameraAppHandler.cameraExposureTime.connect(self.setCameraExposureTime)
        self.chooserLock = threading.Lock()
        # connect change in imaging app to the subroutine of setting it up
        self.app.ui.pd_chooseImaging.currentIndexChanged.connect(self.chooseImaging)

    def initConfig(self):
        # if there was a receiver established, remove it. if not, we will fire the event by changing the list
        if self.app.ui.pd_chooseImaging.receivers(self.app.ui.pd_chooseImaging.currentIndexChanged) > 0:
            self.app.ui.pd_chooseImaging.currentIndexChanged.disconnect()
        # build the drop down menu
        self.app.ui.pd_chooseImaging.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseImaging.setView(view)
        if self.workerNoneCam.data['Camera']['AppAvailable']:
            self.app.ui.pd_chooseImaging.addItem('No Cam - ' + self.workerNoneCam.data['Camera']['AppName'])
        if self.workerINDICamera.data['Camera']['AppAvailable']:
            self.app.ui.pd_chooseImaging.addItem('INDI Camera')
        if platform.system() == 'Windows':
            if self.workerSGPro.data['Camera']['AppAvailable']:
                self.app.ui.pd_chooseImaging.addItem('SGPro - ' + self.workerSGPro.data['Camera']['AppName'])
            if self.workerMaximDL.data['Camera']['AppAvailable']:
                self.app.ui.pd_chooseImaging.addItem('MaximDL - ' + self.workerMaximDL.data['Camera']['AppName'])
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            if self.workerTheSkyX.data['Camera']['AppAvailable']:
                self.app.ui.pd_chooseImaging.addItem('TheSkyX - ' + self.workerTheSkyX.data['Camera']['AppName'])
        # load the config data
        try:
            if 'ImagingApplication' in self.app.config:
                self.app.ui.pd_chooseImaging.setCurrentIndex(int(self.app.config['ImagingApplication']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

        self.chooseImaging()
        self.workerINDICamera.solver.initConfig()

    def storeConfig(self):
        self.app.config['ImagingApplication'] = self.app.ui.pd_chooseImaging.currentIndex()
        self.workerINDICamera.solver.storeConfig()

    def chooseImaging(self):
        self.chooserLock.acquire()
        self.imagingWorkerCameraAppHandler.cameraStatus.disconnect(self.setStatusCamera)
        self.imagingWorkerCameraAppHandler.cameraExposureTime.disconnect(self.setCameraExposureTime)

        if self.imagingWorkerCameraAppHandler.isRunning:
            self.imagingWorkerCameraAppHandler.stop()
        if self.app.ui.pd_chooseImaging.currentText().startswith('No Cam'):
            self.imagingWorkerCameraAppHandler = self.workerNoneCam
            self.imagingThreadCameraAppHandler = self.threadNoneCam
            self.logger.info('Actual camera / plate solver is None')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('SGPro'):
            self.imagingWorkerCameraAppHandler = self.workerSGPro
            self.imagingThreadCameraAppHandler = self.threadSGPro
            self.logger.info('Actual camera / plate solver is SGPro')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('MaximDL'):
            self.imagingWorkerCameraAppHandler = self.workerMaximDL
            self.imagingThreadCameraAppHandler = self.threadMaximDL
            self.logger.info('Actual camera / plate solver is MaximDL')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('INDI'):
            self.imagingWorkerCameraAppHandler = self.workerINDICamera
            self.imagingThreadCameraAppHandler = self.threadINDICamera
            self.logger.info('Actual camera / plate solver is INDI Camera')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('TheSkyX'):
            self.imagingWorkerCameraAppHandler = self.workerTheSkyX
            self.imagingThreadCameraAppHandler = self.threadTheSkyX
            self.logger.info('Actual camera / plate solver is TheSkyX')

        self.imagingWorkerCameraAppHandler.cameraStatus.connect(self.setStatusCamera)
        self.imagingWorkerCameraAppHandler.cameraExposureTime.connect(self.setCameraExposureTime)

        self.imagingThreadCameraAppHandler.start()
        self.chooserLock.release()

    def setStatusCamera(self, status):
        self.app.imageWindow.ui.le_cameraStatus.setText(status)

    def setCameraExposureTime(self, status):
        self.app.imageWindow.ui.le_cameraExposureTime.setText(status)

    def prepareImaging(self):
        camData = self.imagingWorkerCameraAppHandler.data['Camera']
        if camData['CONNECTION']['CONNECT'] == 'Off':
            return
        imageParams = {}
        directory = time.strftime("%Y-%m-%d", time.gmtime())
        imageParams['Directory'] = directory
        # todo: handling of subframes
        if False and self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            imageParams['SizeX'] = int(float(camData['CCD_INFO']['CCD_MAX_X']) * scaleSubframe)
            imageParams['SizeY'] = int(float(camData['CCD_INFO']['CCD_MAX_Y']) * scaleSubframe)
            imageParams['OffX'] = int((float(camData['CCD_INFO']['CCD_MAX_X']) - imageParams['SizeX']) / 2)
            imageParams['OffY'] = int((float(camData['CCD_INFO']['CCD_MAX_Y']) - imageParams['SizeY']) / 2)
            imageParams['CanSubframe'] = True
        else:
            imageParams['SizeX'] = int(float(camData['CCD_INFO']['CCD_MAX_X']))
            imageParams['SizeY'] = int(float(camData['CCD_INFO']['CCD_MAX_X']))
            imageParams['OffX'] = 0
            imageParams['OffY'] = 0
            imageParams['CanSubframe'] = False
        if 'Gain' in camData:
            imageParams['Gain'] = camData['Gain']
        else:
            imageParams['Gain'] = 'NotSet'
        imageParams['BaseDirImages'] = self.IMAGEDIR + '/' + directory
        if self.app.ui.checkFastDownload.isChecked():
            imageParams['Speed'] = 'HiSpeed'
        else:
            imageParams['Speed'] = 'Normal'
        imageParams['Binning'] = int(float(self.app.ui.cameraBin.value()))
        imageParams['Exposure'] = int(float(self.app.ui.cameraExposure.value()))
        imageParams['Iso'] = int(float(self.app.ui.isoSetting.value()))
        imageParams['Blind'] = self.app.ui.checkUseBlindSolve.isChecked()
        imageParams['ScaleHint'] = float(self.app.ui.pixelSize.value()) * imageParams['Binning'] * 206.6 / float(self.app.ui.focalLength.value())
        if 'Binning' in imageParams:
            imageParams['SizeX'] = int(imageParams['SizeX'] / imageParams['Binning'])
            imageParams['SizeY'] = int(imageParams['SizeY'] / imageParams['Binning'])
        return imageParams

    def captureImage(self, imageParams, queue=True):
        camData = self.imagingWorkerCameraAppHandler.data['Camera']
        if camData['CONNECTION']['CONNECT'] == 'Off':
            return
        if self.app.workerModelingDispatcher.modelingRunner.cancel:
            self.logger.info('Modeling cancelled after capturing image')
            imageParams['Success'] = False
            imageParams['Message'] = 'Cancel modeling pressed'
            return False, imageParams
        RaJ2000FitsHeader = self.transform.decimalToDegree(imageParams['RaJ2000'], False, False, ' ')
        DecJ2000FitsHeader = self.transform.decimalToDegree(imageParams['DecJ2000'], True, False, ' ')
        self.logger.info('Imaging parameters: {0}'.format(imageParams))
        # using a queue if the calling thread is gui -> no wait
        # if it is done through modeling -> separate thread which is calling
        if queue:
            self.imagingCommandQueue.put({'Command': 'GetImage', 'ImageParams': imageParams})
        else:
            imageParams = self.imagingWorkerCameraAppHandler.getImage(imageParams)
        imageParams['Message'] = ''
        imageParams['Success'] = False
        while imageParams['Message'] == '' and self.app.workerModelingDispatcher.isRunning:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if imageParams['Success']:
            self.logger.info('Imaging parameters: {0}'.format(imageParams))
            fitsFileHandle = pyfits.open(imageParams['Imagepath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                imageParams['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
            fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()
            fitsHeader['OBJCTRA'] = RaJ2000FitsHeader
            fitsHeader['OBJCTDEC'] = DecJ2000FitsHeader
            fitsHeader['CDELT1'] = str(imageParams['ScaleHint'])
            fitsHeader['CDELT2'] = str(imageParams['ScaleHint'])
            fitsHeader['PIXSCALE'] = str(imageParams['ScaleHint'])
            fitsHeader['SCALE'] = str(imageParams['ScaleHint'])
            fitsFileHandle.flush()
            fitsFileHandle.close()
            # self.app.imageQueue.put(imageParams['Imagepath'])
            imageParams['Success'] = True
            imageParams['Message'] = 'OK'
        else:
            imageParams['Success'] = False
        return imageParams

    def addSolveRandomValues(self, imageParams):
        imageParams['RaJ2000Solved'] = imageParams['RaJ2000'] + (2 * random.random() - 1) / 3600
        imageParams['DecJ2000Solved'] = imageParams['DecJ2000'] + (2 * random.random() - 1) / 360
        imageParams['Scale'] = 1.3
        imageParams['Angle'] = 90
        imageParams['TimeTS'] = 2.5
        ra, dec = self.transform.transformERFA(imageParams['RaJ2000Solved'], imageParams['DecJ2000Solved'], 3)
        imageParams['RaJNowSolved'] = ra
        imageParams['DecJNowSolved'] = dec
        imageParams['RaError'] = (imageParams['RaJ2000Solved'] - imageParams['RaJ2000']) * 3600
        imageParams['DecError'] = (imageParams['DecJ2000Solved'] - imageParams['DecJ2000']) * 3600
        imageParams['ModelError'] = math.sqrt(imageParams['RaError'] * imageParams['RaError'] + imageParams['DecError'] * imageParams['DecError'])
        return imageParams

    def solveImage(self, imageParams, queue=True):
        camData = self.imagingWorkerCameraAppHandler.data['Camera']
        if camData['CONNECTION']['CONNECT'] == 'Off':
            return
        imageParams['UseFitsHeaders'] = True
        # using a queue if the calling thread is gui -> no wait
        # if it is done through modeling -> separate thread which is calling
        if queue:
            self.imagingCommandQueue.put({'Command': 'GetImage', 'ImageParams': imageParams})
        else:
            imageParams = self.imagingWorkerCameraAppHandler.solveImage(imageParams)
        imageParams['Message'] = ''
        imageParams['Success'] = False
        while imageParams['Message'] == '' and self.app.workerModelingDispatcher.isRunning:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()

        imageParams = self.imagingWorkerCameraAppHandler.solveImage(imageParams)
        self.logger.info('Imaging parameters: {0}'.format(imageParams))
        if imageParams['Success']:
            ra_sol_Jnow, dec_sol_Jnow = self.transform.transformERFA(imageParams['RaJ2000Solved'], imageParams['DecJ2000Solved'], 3)
            imageParams['RaJNowSolved'] = ra_sol_Jnow
            imageParams['DecJNowSolved'] = dec_sol_Jnow
            imageParams['RaError'] = (imageParams['RaJ2000Solved'] - imageParams['RaJ2000']) * 3600
            imageParams['DecError'] = (imageParams['DecJ2000Solved'] - imageParams['DecJ2000']) * 3600
            imageParams['ModelError'] = math.sqrt(imageParams['RaError'] * imageParams['RaError'] + imageParams['DecError'] * imageParams['DecError'])
            fitsFileHandle = pyfits.open(imageParams['Imagepath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            fitsHeader['MW_PRA'] = imageParams['RaJNowSolved']
            fitsHeader['MW_PDEC'] = imageParams['DecJNowSolved']
            fitsHeader['MW_SRA'] = imageParams['RaJ2000Solved']
            fitsHeader['MW_SDEC'] = imageParams['DecJ2000Solved']
            fitsHeader['MW_PSCAL'] = imageParams['Scale']
            fitsHeader['MW_PANGL'] = imageParams['Angle']
            fitsHeader['MW_PTS'] = imageParams['TimeTS']
            fitsFileHandle.flush()
            fitsFileHandle.close()
            imageParams['Success'] = True
            imageParams['Message'] = 'OK'
        else:
            imageParams['Success'] = False
        return imageParams
