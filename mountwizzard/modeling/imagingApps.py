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
        # make imaging applications available
        if platform.system() == 'Windows':
            self.workerSGPro = sgpro.SGPro(self.app)
            self.threadSGPro = PyQt5.QtCore.QThread()
            self.threadSGPro.setObjectName("SGPro")
            self.workerSGPro.moveToThread(self.threadSGPro)
            self.threadSGPro.started.connect(self.workerSGPro.run)
            self.workerSGPro.finished.connect(self.workerSGProStop)

            self.workerMaximDL = maximdl.MaximDLCamera(self.app)
            self.threadMaximDL = PyQt5.QtCore.QThread()
            self.threadMaximDL.setObjectName("MaximDL")
            self.workerMaximDL.moveToThread(self.threadMaximDL)
            self.threadMaximDL.started.connect(self.workerMaximDL.run)
            self.workerMaximDL.finished.connect(self.workerMaximDLStop)

        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.TheSkyX = theskyx.TheSkyX(self.app)

        self.workerNoneCam = none.NoneCamera(self.app)
        self.threadNoneCam = PyQt5.QtCore.QThread()
        self.threadNoneCam.setObjectName("NoneCamera")
        self.workerNoneCam.moveToThread(self.threadNoneCam)
        self.threadNoneCam.started.connect(self.workerNoneCam.run)
        self.workerNoneCam.finished.connect(self.workerNoneCamStop)

        self.workerINDICamera = indicamera.INDICamera(self.app)
        self.threadINDICamera = PyQt5.QtCore.QThread()
        self.threadINDICamera.setObjectName("INDICamera")
        self.workerINDICamera.moveToThread(self.threadINDICamera)
        self.threadINDICamera.started.connect(self.workerINDICamera.run)
        self.workerINDICamera.finished.connect(self.workerINDICameraStop)

        # select default application
        self.imagingWorkerCameraAppHandler = self.workerNoneCam
        self.imagingThreadCameraAppHandler = self.threadNoneCam
        self.chooserLock = threading.Lock()

    def initConfig(self):
        # if there was a receiver established, remove it. if not, we will fire the event by changing the list
        if self.app.ui.pd_chooseImaging.receivers(self.app.ui.pd_chooseImaging.currentIndexChanged) > 0:
            self.app.ui.pd_chooseImaging.currentIndexChanged.disconnect()
        # build the drop down menu
        self.app.ui.pd_chooseImaging.clear()
        if self.workerNoneCam.data['AppAvailable']:
            self.app.ui.pd_chooseImaging.addItem('No Cam - ' + self.workerNoneCam.data['AppName'])
        if self.workerINDICamera.data['AppAvailable']:
            self.app.ui.pd_chooseImaging.addItem('INDI Camera')
        if platform.system() == 'Windows':
            if self.workerSGPro.data['AppAvailable']:
                self.app.ui.pd_chooseImaging.addItem('SGPro - ' + self.workerSGPro.data['AppName'])
            if self.workerMaximDL.data['AppAvailable']:
                self.app.ui.pd_chooseImaging.addItem('MaximDL - ' + self.workerMaximDL.data['AppName'])
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            if self.TheSkyX.appAvailable:
                self.app.ui.pd_chooseImaging.addItem('TheSkyX - ' + self.TheSkyX.appName)
        # load the config data
        try:
            if 'ImagingApplication' in self.app.config:
                self.app.ui.pd_chooseImaging.setCurrentIndex(int(self.app.config['ImagingApplication']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        # connect change in imaging app to the subroutine of setting it up
        self.app.ui.pd_chooseImaging.currentIndexChanged.connect(self.chooseImaging)
        self.chooseImaging()

    def storeConfig(self):
        self.app.config['ImagingApplication'] = self.app.ui.pd_chooseImaging.currentIndex()

    def workerNoneCamStop(self):
        self.threadNoneCam.quit()
        self.threadNoneCam.wait()

    def workerSGProStop(self):
        self.threadSGPro.quit()
        self.threadSGPro.wait()

    def workerMaximDLStop(self):
        self.threadMaximDL.quit()
        self.threadMaximDL.wait()

    def workerTheSkyXStop(self):
        self.threadTheSkyX.quit()
        self.threadTheSkyX.wait()

    def workerINDICameraStop(self):
        self.threadINDICamera.quit()
        self.threadINDICamera.wait()

    def chooseImaging(self):
        self.chooserLock.acquire()
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
            self.imagingWorkerCameraAppHandler = self.workerNoneCam
            self.imagingThreadCameraAppHandler = self.threadNoneCam
            self.logger.info('Actual camera / plate solver is TheSkyX')
        self.imagingThreadCameraAppHandler.start()
        self.chooserLock.release()

    def prepareImaging(self):
        imageParams = {}
        directory = time.strftime("%Y-%m-%d", time.gmtime())
        imageParams['Directory'] = directory
        camData = self.imagingWorkerCameraAppHandler.data['Camera']
        if camData['CanSubframe'] and self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            imageParams['SizeX'] = int(float(camData['CameraXSize']) * scaleSubframe)
            imageParams['SizeY'] = int(float(camData['CameraYSize']) * scaleSubframe)
            imageParams['OffX'] = int((float(camData['CameraXSize']) - imageParams['SizeX']) / 2)
            imageParams['OffY'] = int((float(camData['CameraYSize']) - imageParams['SizeY']) / 2)
            imageParams['CanSubframe'] = True
        else:
            imageParams['SizeX'] = 0
            imageParams['SizeY'] = 0
            imageParams['OffX'] = 0
            imageParams['OffY'] = 0
            imageParams['CanSubframe'] = False
            self.logger.warning('Camera does not support subframe.')
        imageParams['GainValue'] = camData['Gains'][camData['Gain']]
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

    def capturingImage(self, imageParams, simulation):
        if self.app.workerModelingDispatcher.modelingRunner.cancel:
            self.logger.info('Modeling cancelled after capturing image')
            return False, 'Cancel modeling pressed', imageParams
        LocalSiderealTimeFitsHeader = imageParams['LocalSiderealTime'][0:10]
        RaJ2000FitsHeader = self.transform.decimalToDegree(imageParams['RaJ2000'], False, False, ' ')
        DecJ2000FitsHeader = self.transform.decimalToDegree(imageParams['DecJ2000'], True, False, ' ')
        RaJNowFitsHeader = self.transform.decimalToDegree(imageParams['RaJNow'], False, True, ' ')
        DecJNowFitsHeader = self.transform.decimalToDegree(imageParams['DecJNow'], True, True, ' ')
        if imageParams['Pierside'] == '1':
            pierside_fits_header = 'E'
        else:
            pierside_fits_header = 'W'
        self.logger.info('imageParams: {0}'.format(imageParams))
        suc, mes, imageParams = self.imagingWorkerCameraAppHandler.getImage(imageParams)
        if suc:
            self.logger.info('suc: {0}, imageParams{1}'.format(suc, imageParams))
            fitsFileHandle = pyfits.open(imageParams['ImagePath'], mode='update')
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
            fitsHeader['MW_MRA'] = RaJNowFitsHeader
            fitsHeader['MW_MDEC'] = DecJNowFitsHeader
            fitsHeader['MW_ST'] = LocalSiderealTimeFitsHeader
            fitsHeader['MW_MSIDE'] = pierside_fits_header
            fitsHeader['MW_EXP'] = imageParams['Exposure']
            fitsHeader['MW_AZ'] = imageParams['Azimuth']
            fitsHeader['MW_ALT'] = imageParams['Altitude']
            self.logger.info('DATE-OBS:{0}, OBJCTRA:{1} OBJTDEC:{2} CDELT1:{3} MW_MRA:{4} '
                             'MW_MDEC:{5} MW_ST:{6} MW_PIER:{7} MW_EXP:{8} MW_AZ:{9} MW_ALT:{10}'
                             .format(fitsHeader['DATE-OBS'], fitsHeader['OBJCTRA'], fitsHeader['OBJCTDEC'],
                                     fitsHeader['CDELT1'], fitsHeader['MW_MRA'], fitsHeader['MW_MDEC'],
                                     fitsHeader['MW_ST'], fitsHeader['MW_MSIDE'], fitsHeader['MW_EXP'],
                                     fitsHeader['MW_AZ'], fitsHeader['MW_ALT']))
            fitsFileHandle.flush()
            fitsFileHandle.close()
            self.app.imageQueue.put(imageParams['ImagePath'])
            return True, 'OK', imageParams
        else:
            return False, mes, imageParams

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

    def solveImage(self, imageParams, simulation):
        imageParams['UseFitsHeaders'] = True
        suc, mes, imageParams = self.imagingWorkerCameraAppHandler.solveImage(imageParams)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            ra_sol_Jnow, dec_sol_Jnow = self.transform.transformERFA(imageParams['RaJ2000Solved'], imageParams['DecJ2000Solved'], 3)
            imageParams['RaJNowSolved'] = ra_sol_Jnow
            imageParams['DecJNowSolved'] = dec_sol_Jnow
            imageParams['RaError'] = (imageParams['RaJ2000Solved'] - imageParams['RaJ2000']) * 3600
            imageParams['DecError'] = (imageParams['DecJ2000Solved'] - imageParams['DecJ2000']) * 3600
            imageParams['ModelError'] = math.sqrt(imageParams['RaError'] * imageParams['RaError'] + imageParams['DecError'] * imageParams['DecError'])
            fitsFileHandle = pyfits.open(imageParams['ImagePath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            fitsHeader['MW_PRA'] = imageParams['RaJNowSolved']
            fitsHeader['MW_PDEC'] = imageParams['DecJNowSolved']
            fitsHeader['MW_SRA'] = imageParams['RaJ2000Solved']
            fitsHeader['MW_SDEC'] = imageParams['DecJ2000Solved']
            fitsHeader['MW_PSCAL'] = imageParams['Scale']
            fitsHeader['MW_PANGL'] = imageParams['Angle']
            fitsHeader['MW_PTS'] = imageParams['TimeTS']
            self.logger.info('MW_PRA:{0} MW_PDEC:{1} MW_PSCAL:{2} MW_PANGL:{3} MW_PTS:{4}'.
                             format(fitsHeader['MW_PRA'], fitsHeader['MW_PDEC'], fitsHeader['MW_PSCAL'],
                                    fitsHeader['MW_PANGL'], fitsHeader['MW_PTS']))
            fitsFileHandle.flush()
            fitsFileHandle.close()
            if simulation:
                imageParams = self.addSolveRandomValues(imageParams)
            return True, mes, imageParams
        else:
            return False, mes, imageParams

