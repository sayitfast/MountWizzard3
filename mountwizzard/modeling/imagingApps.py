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

    REF_PICTURE = '/model001.fit'
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
            # noinspection PyUnresolvedReferences
            self.threadSGPro.started.connect(self.workerSGPro.run)
            self.workerSGPro.finished.connect(self.workerSGProStop)

            self.workerMaximDL = maximdl.MaximDLCamera(self.app)
            self.threadMaximDL = PyQt5.QtCore.QThread()
            self.threadMaximDL.setObjectName("MaximDL")
            self.workerMaximDL.moveToThread(self.threadMaximDL)
            # noinspection PyUnresolvedReferences
            self.threadMaximDL.started.connect(self.workerMaximDL.run)
            self.workerMaximDL.finished.connect(self.workerMaximDLStop)

        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.TheSkyX = theskyx.TheSkyX(self.app)

        self.workerNoneCam = none.NoneCamera(self.app)
        self.threadNoneCam = PyQt5.QtCore.QThread()
        self.threadNoneCam.setObjectName("NoneCamera")
        self.workerNoneCam.moveToThread(self.threadNoneCam)
        # noinspection PyUnresolvedReferences
        self.threadNoneCam.started.connect(self.workerNoneCam.run)
        self.workerNoneCam.finished.connect(self.workerNoneCamStop)

        self.INDICamera = indicamera.INDICamera(self.app)

        # select default application
        self.imagingWorkerAppHandler = self.workerNoneCam
        self.imagingThreadAppHandler = self.threadNoneCam
        self.chooserLock = threading.Lock()

    def initConfig(self):
        # if there was a receiver established, remove it. if not, we will fire the event by changing the list
        if self.app.ui.pd_chooseImaging.receivers(self.app.ui.pd_chooseImaging.currentIndexChanged) > 0:
            self.app.ui.pd_chooseImaging.currentIndexChanged.disconnect()
        # build the drop down menu
        self.app.ui.pd_chooseImaging.clear()
        if self.workerNoneCam.data['AppAvailable']:
            self.app.ui.pd_chooseImaging.addItem('No Cam - ' + self.workerNoneCam.data['AppName'])
        if self.INDICamera.appAvailable:
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
        if self.imagingWorkerAppHandler.isRunning:
            self.imagingWorkerAppHandler.stop()
        if self.app.ui.pd_chooseImaging.currentText().startswith('No Cam'):
            self.imagingWorkerAppHandler = self.workerNoneCam
            self.imagingThreadAppHandler = self.threadNoneCam
            self.logger.info('Actual camera / plate solver is None')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('SGPro'):
            self.imagingWorkerAppHandler = self.workerSGPro
            self.imagingThreadAppHandler = self.threadSGPro
            self.logger.info('Actual camera / plate solver is SGPro')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('MaximDL'):
            self.imagingWorkerAppHandler = self.workerMaximDL
            self.imagingThreadAppHandler = self.threadMaximDL
            self.logger.info('Actual camera / plate solver is MaximDL')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('INDI Camera'):
            self.imagingWorkerAppHandler = self.workerNoneCam
            self.imagingThreadAppHandler = self.threadNoneCam
            self.logger.info('Actual camera / plate solver is INDI Camera')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('TheSkyX'):
            self.imagingWorkerAppHandler = self.workerNoneCam
            self.imagingThreadAppHandler = self.threadNoneCam
            self.logger.info('Actual camera / plate solver is TheSkyX')
        self.imagingThreadAppHandler.start()
        self.chooserLock.release()

    def prepareImaging(self):
        imagingParameter = {}
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        imagingParameter['Directory'] = directory
        camData = self.imagingWorkerAppHandler.data
        if camData['CanSubframe']:
            self.logger.info('camera props: {0}, {1}, {2}'.format(camData['CameraXSize'], camData['CameraYSize'], camData['CanSubframe']))
        else:
            self.logger.warning('GetCameraProps with error: {0}'.format(camData['Message']))
            return {}
        if camData['CanSubframe'] and self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            imagingParameter['SizeX'] = int(camData['CameraXSize'] * scaleSubframe)
            imagingParameter['SizeY'] = int(camData['CameraYSize'] * scaleSubframe)
            imagingParameter['OffX'] = int((camData['CameraXSize'] - imagingParameter['SizeX']) / 2)
            imagingParameter['OffY'] = int((camData['CameraYSize'] - imagingParameter['SizeY']) / 2)
            imagingParameter['CanSubframe'] = True
        else:
            imagingParameter['SizeX'] = 0
            imagingParameter['SizeY'] = 0
            imagingParameter['OffX'] = 0
            imagingParameter['OffY'] = 0
            imagingParameter['CanSubframe'] = False
            self.logger.warning('Camera does not support subframe.')
        imagingParameter['GainValue'] = camData['Gains'][camData['Gain']]
        imagingParameter['BaseDirImages'] = self.IMAGEDIR + '/' + directory
        if self.app.ui.checkFastDownload.isChecked():
            imagingParameter['Speed'] = 'HiSpeed'
        else:
            imagingParameter['Speed'] = 'Normal'
        imagingParameter['Binning'] = int(float(self.app.ui.cameraBin.value()))
        imagingParameter['Exposure'] = int(float(self.app.ui.cameraExposure.value()))
        imagingParameter['Iso'] = int(float(self.app.ui.isoSetting.value()))
        imagingParameter['Blind'] = self.app.ui.checkUseBlindSolve.isChecked()
        imagingParameter['ScaleHint'] = float(self.app.ui.pixelSize.value()) * imagingParameter['Binning'] * 206.6 / float(self.app.ui.focalLength.value())
        if 'Binning' in imagingParameter:
            imagingParameter['SizeX'] = int(imagingParameter['SizeX'] / imagingParameter['Binning'])
            imagingParameter['SizeY'] = int(imagingParameter['SizeY'] / imagingParameter['Binning'])
        return imagingParameter

    def capturingImage(self, imagingParameter, simulation):
        if self.app.workerModelingDispatcher.modelingRunner.cancel:
            self.logger.info('Modeling cancelled after capturing image')
            return False, 'Cancel modeling pressed', imagingParameter
        LocalSiderealTimeFitsHeader = imagingParameter['LocalSiderealTime'][0:10]
        RaJ2000FitsHeader = self.transform.decimalToDegree(imagingParameter['RaJ2000'], False, False, ' ')
        DecJ2000FitsHeader = self.transform.decimalToDegree(imagingParameter['DecJ2000'], True, False, ' ')
        RaJNowFitsHeader = self.transform.decimalToDegree(imagingParameter['RaJNow'], False, True, ' ')
        DecJNowFitsHeader = self.transform.decimalToDegree(imagingParameter['DecJNow'], True, True, ' ')
        if imagingParameter['Pierside'] == '1':
            pierside_fits_header = 'E'
        else:
            pierside_fits_header = 'W'
        self.logger.info('imagingParameter: {0}'.format(imagingParameter))
        suc, mes, imagingParameter = self.imagingWorkerAppHandler.getImage(imagingParameter)
        if suc:
            self.logger.info('suc: {0}, imagingParameter{1}'.format(suc, imagingParameter))
            fitsFileHandle = pyfits.open(imagingParameter['ImagePath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                imagingParameter['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
            fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()
            fitsHeader['OBJCTRA'] = RaJ2000FitsHeader
            fitsHeader['OBJCTDEC'] = DecJ2000FitsHeader
            fitsHeader['CDELT1'] = str(imagingParameter['ScaleHint'])
            fitsHeader['CDELT2'] = str(imagingParameter['ScaleHint'])
            fitsHeader['PIXSCALE'] = str(imagingParameter['ScaleHint'])
            fitsHeader['SCALE'] = str(imagingParameter['ScaleHint'])
            fitsHeader['MW_MRA'] = RaJNowFitsHeader
            fitsHeader['MW_MDEC'] = DecJNowFitsHeader
            fitsHeader['MW_ST'] = LocalSiderealTimeFitsHeader
            fitsHeader['MW_MSIDE'] = pierside_fits_header
            fitsHeader['MW_EXP'] = imagingParameter['Exposure']
            fitsHeader['MW_AZ'] = imagingParameter['Azimuth']
            fitsHeader['MW_ALT'] = imagingParameter['Altitude']
            self.logger.info('DATE-OBS:{0}, OBJCTRA:{1} OBJTDEC:{2} CDELT1:{3} MW_MRA:{4} '
                             'MW_MDEC:{5} MW_ST:{6} MW_PIER:{7} MW_EXP:{8} MW_AZ:{9} MW_ALT:{10}'
                             .format(fitsHeader['DATE-OBS'], fitsHeader['OBJCTRA'], fitsHeader['OBJCTDEC'],
                                     fitsHeader['CDELT1'], fitsHeader['MW_MRA'], fitsHeader['MW_MDEC'],
                                     fitsHeader['MW_ST'], fitsHeader['MW_MSIDE'], fitsHeader['MW_EXP'],
                                     fitsHeader['MW_AZ'], fitsHeader['MW_ALT']))
            fitsFileHandle.flush()
            fitsFileHandle.close()
            self.app.imageQueue.put(imagingParameter['ImagePath'])
            return True, 'OK', imagingParameter
        else:
            return False, mes, imagingParameter

    def addSolveRandomValues(self, imagingParameter):
        imagingParameter['RaJ2000Solved'] = imagingParameter['RaJ2000'] + (2 * random.random() - 1) / 3600
        imagingParameter['DecJ2000Solved'] = imagingParameter['DecJ2000'] + (2 * random.random() - 1) / 360
        imagingParameter['Scale'] = 1.3
        imagingParameter['Angle'] = 90
        imagingParameter['TimeTS'] = 2.5
        ra, dec = self.transform.transformERFA(imagingParameter['RaJ2000Solved'], imagingParameter['DecJ2000Solved'], 3)
        imagingParameter['RaJNowSolved'] = ra
        imagingParameter['DecJNowSolved'] = dec
        imagingParameter['RaError'] = (imagingParameter['RaJ2000Solved'] - imagingParameter['RaJ2000']) * 3600
        imagingParameter['DecError'] = (imagingParameter['DecJ2000Solved'] - imagingParameter['DecJ2000']) * 3600
        imagingParameter['ModelError'] = math.sqrt(imagingParameter['RaError'] * imagingParameter['RaError'] + imagingParameter['DecError'] * imagingParameter['DecError'])
        return imagingParameter

    def solveImage(self, imagingParameter, simulation):
        imagingParameter['UseFitsHeaders'] = True
        suc, mes, imagingParameter = self.imagingWorkerAppHandler.solveImage(imagingParameter)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            ra_sol_Jnow, dec_sol_Jnow = self.transform.transformERFA(imagingParameter['RaJ2000Solved'], imagingParameter['DecJ2000Solved'], 3)
            imagingParameter['RaJNowSolved'] = ra_sol_Jnow
            imagingParameter['DecJNowSolved'] = dec_sol_Jnow
            imagingParameter['RaError'] = (imagingParameter['RaJ2000Solved'] - imagingParameter['RaJ2000']) * 3600
            imagingParameter['DecError'] = (imagingParameter['DecJ2000Solved'] - imagingParameter['DecJ2000']) * 3600
            imagingParameter['ModelError'] = math.sqrt(imagingParameter['RaError'] * imagingParameter['RaError'] + imagingParameter['DecError'] * imagingParameter['DecError'])
            fitsFileHandle = pyfits.open(imagingParameter['ImagePath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            fitsHeader['MW_PRA'] = imagingParameter['RaJNowSolved']
            fitsHeader['MW_PDEC'] = imagingParameter['DecJNowSolved']
            fitsHeader['MW_SRA'] = imagingParameter['RaJ2000Solved']
            fitsHeader['MW_SDEC'] = imagingParameter['DecJ2000Solved']
            fitsHeader['MW_PSCAL'] = imagingParameter['Scale']
            fitsHeader['MW_PANGL'] = imagingParameter['Angle']
            fitsHeader['MW_PTS'] = imagingParameter['TimeTS']
            self.logger.info('MW_PRA:{0} MW_PDEC:{1} MW_PSCAL:{2} MW_PANGL:{3} MW_PTS:{4}'.
                             format(fitsHeader['MW_PRA'], fitsHeader['MW_PDEC'], fitsHeader['MW_PSCAL'],
                                    fitsHeader['MW_PANGL'], fitsHeader['MW_PTS']))
            fitsFileHandle.flush()
            fitsFileHandle.close()
            if simulation:
                imagingParameter = self.addSolveRandomValues(imagingParameter)
            return True, mes, imagingParameter
        else:
            return False, mes, imagingParameter

