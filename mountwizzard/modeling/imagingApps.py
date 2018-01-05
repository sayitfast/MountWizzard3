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
        '''
        elif self.app.ui.pd_chooseImaging.currentText().startswith('INDI Camera'):
            self.imagingWorkerAppHandler = self.workerNoneCam
            self.imagingThreadAppHandler = self.threadNoneCam
            self.logger.info('Actual camera / plate solver is INDI Camera')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('TheSkyX'):
            self.imagingWorkerAppHandler = self.workerNoneCam
            self.imagingThreadAppHandler = self.threadNoneCam
            self.logger.info('Actual camera / plate solver is TheSkyX')
        '''
        self.imagingThreadAppHandler.start()
        self.chooserLock.release()

    def prepareImaging(self):
        modelData = {}
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        modelData['Directory'] = directory
        camData = self.imagingWorkerAppHandler.data
        if camData['CanSubframe']:
            self.logger.info('camera props: {0}, {1}, {2}'.format(camData['CameraXSize'], camData['CameraYSize'], camData['CanSubframe']))
        else:
            self.logger.warning('GetCameraProps with error: {0}'.format(camData['Message']))
            return {}
        if camData['CanSubframe'] and self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            modelData['SizeX'] = int(camData['CameraXSize'] * scaleSubframe)
            modelData['SizeY'] = int(camData['CameraYSize'] * scaleSubframe)
            modelData['OffX'] = int((camData['CameraXSize'] - modelData['SizeX']) / 2)
            modelData['OffY'] = int((camData['CameraYSize'] - modelData['SizeY']) / 2)
            modelData['CanSubframe'] = True
        else:
            modelData['SizeX'] = 0
            modelData['SizeY'] = 0
            modelData['OffX'] = 0
            modelData['OffY'] = 0
            modelData['CanSubframe'] = False
            self.logger.warning('Camera does not support subframe.')
        modelData['GainValue'] = camData['Gains'][camData['Gain']]
        modelData['BaseDirImages'] = self.IMAGEDIR + '/' + directory
        if self.app.ui.checkFastDownload.isChecked():
            modelData['Speed'] = 'HiSpeed'
        else:
            modelData['Speed'] = 'Normal'
        modelData['Binning'] = int(float(self.app.ui.cameraBin.value()))
        modelData['Exposure'] = int(float(self.app.ui.cameraExposure.value()))
        modelData['Iso'] = int(float(self.app.ui.isoSetting.value()))
        modelData['Blind'] = self.app.ui.checkUseBlindSolve.isChecked()
        modelData['ScaleHint'] = float(self.app.ui.pixelSize.value()) * modelData['Binning'] * 206.6 / float(self.app.ui.focalLength.value())
        if 'Binning' in modelData:
            modelData['SizeX'] = int(modelData['SizeX'] / modelData['Binning'])
            modelData['SizeY'] = int(modelData['SizeY'] / modelData['Binning'])
        return modelData

    def capturingImage(self, modelData, simulation):
        if self.app.workerModelingDispatcher.modelingRunner.cancel:
            self.logger.info('Modeling cancelled after capturing image')
            return False, 'Cancel modeling pressed', modelData
        LocalSiderealTimeFitsHeader = modelData['LocalSiderealTime'][0:10]
        RaJ2000FitsHeader = self.transform.decimalToDegree(modelData['RaJ2000'], False, False, ' ')
        DecJ2000FitsHeader = self.transform.decimalToDegree(modelData['DecJ2000'], True, False, ' ')
        RaJNowFitsHeader = self.transform.decimalToDegree(modelData['RaJNow'], False, True, ' ')
        DecJNowFitsHeader = self.transform.decimalToDegree(modelData['DecJNow'], True, True, ' ')
        if modelData['Pierside'] == '1':
            pierside_fits_header = 'E'
        else:
            pierside_fits_header = 'W'
        self.logger.info('modelData: {0}'.format(modelData))
        suc, mes, modelData = self.imagingWorkerAppHandler.getImage(modelData)
        if suc:
            self.logger.info('suc: {0}, modelData{1}'.format(suc, modelData))
            fitsFileHandle = pyfits.open(modelData['ImagePath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                modelData['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
            fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()
            fitsHeader['OBJCTRA'] = RaJ2000FitsHeader
            fitsHeader['OBJCTDEC'] = DecJ2000FitsHeader
            fitsHeader['CDELT1'] = str(modelData['ScaleHint'])
            fitsHeader['CDELT2'] = str(modelData['ScaleHint'])
            fitsHeader['PIXSCALE'] = str(modelData['ScaleHint'])
            fitsHeader['SCALE'] = str(modelData['ScaleHint'])
            fitsHeader['MW_MRA'] = RaJNowFitsHeader
            fitsHeader['MW_MDEC'] = DecJNowFitsHeader
            fitsHeader['MW_ST'] = LocalSiderealTimeFitsHeader
            fitsHeader['MW_MSIDE'] = pierside_fits_header
            fitsHeader['MW_EXP'] = modelData['Exposure']
            fitsHeader['MW_AZ'] = modelData['Azimuth']
            fitsHeader['MW_ALT'] = modelData['Altitude']
            self.logger.info('DATE-OBS:{0}, OBJCTRA:{1} OBJTDEC:{2} CDELT1:{3} MW_MRA:{4} '
                             'MW_MDEC:{5} MW_ST:{6} MW_PIER:{7} MW_EXP:{8} MW_AZ:{9} MW_ALT:{10}'
                             .format(fitsHeader['DATE-OBS'], fitsHeader['OBJCTRA'], fitsHeader['OBJCTDEC'],
                                     fitsHeader['CDELT1'], fitsHeader['MW_MRA'], fitsHeader['MW_MDEC'],
                                     fitsHeader['MW_ST'], fitsHeader['MW_MSIDE'], fitsHeader['MW_EXP'],
                                     fitsHeader['MW_AZ'], fitsHeader['MW_ALT']))
            fitsFileHandle.flush()
            fitsFileHandle.close()
            self.app.imageQueue.put(modelData['ImagePath'])
            return True, 'OK', modelData
        else:
            return False, mes, modelData

    def addSolveRandomValues(self, modelData):
        modelData['RaJ2000Solved'] = modelData['RaJ2000'] + (2 * random.random() - 1) / 3600
        modelData['DecJ2000Solved'] = modelData['DecJ2000'] + (2 * random.random() - 1) / 360
        modelData['Scale'] = 1.3
        modelData['Angle'] = 90
        modelData['TimeTS'] = 2.5
        ra, dec = self.transform.transformERFA(modelData['RaJ2000Solved'], modelData['DecJ2000Solved'], 3)
        modelData['RaJNowSolved'] = ra
        modelData['DecJNowSolved'] = dec
        modelData['RaError'] = (modelData['RaJ2000Solved'] - modelData['RaJ2000']) * 3600
        modelData['DecError'] = (modelData['DecJ2000Solved'] - modelData['DecJ2000']) * 3600
        modelData['ModelError'] = math.sqrt(modelData['RaError'] * modelData['RaError'] + modelData['DecError'] * modelData['DecError'])
        return modelData

    def solveImage(self, modelData, simulation):
        modelData['UseFitsHeaders'] = True
        suc, mes, modelData = self.imagingWorkerAppHandler.solveImage(modelData)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            ra_sol_Jnow, dec_sol_Jnow = self.transform.transformERFA(modelData['RaJ2000Solved'], modelData['DecJ2000Solved'], 3)
            modelData['RaJNowSolved'] = ra_sol_Jnow
            modelData['DecJNowSolved'] = dec_sol_Jnow
            modelData['RaError'] = (modelData['RaJ2000Solved'] - modelData['RaJ2000']) * 3600
            modelData['DecError'] = (modelData['DecJ2000Solved'] - modelData['DecJ2000']) * 3600
            modelData['ModelError'] = math.sqrt(modelData['RaError'] * modelData['RaError'] + modelData['DecError'] * modelData['DecError'])
            fitsFileHandle = pyfits.open(modelData['ImagePath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            fitsHeader['MW_PRA'] = modelData['RaJNowSolved']
            fitsHeader['MW_PDEC'] = modelData['DecJNowSolved']
            fitsHeader['MW_SRA'] = modelData['RaJ2000Solved']
            fitsHeader['MW_SDEC'] = modelData['DecJ2000Solved']
            fitsHeader['MW_PSCAL'] = modelData['Scale']
            fitsHeader['MW_PANGL'] = modelData['Angle']
            fitsHeader['MW_PTS'] = modelData['TimeTS']
            self.logger.info('MW_PRA:{0} MW_PDEC:{1} MW_PSCAL:{2} MW_PANGL:{3} MW_PTS:{4}'.
                             format(fitsHeader['MW_PRA'], fitsHeader['MW_PDEC'], fitsHeader['MW_PSCAL'],
                                    fitsHeader['MW_PANGL'], fitsHeader['MW_PTS']))
            fitsFileHandle.flush()
            fitsFileHandle.close()
            if simulation:
                modelData = self.addSolveRandomValues(modelData)
            return True, mes, modelData
        else:
            return False, mes, modelData

