############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################
import logging
import os
import platform
import threading
import datetime
import math
import random
import shutil
import sys
# library for fits file handling
import pyfits
# cameras
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
        # make imaging applications available
        if platform.system() == 'Windows':
            self.SGPro = sgpro.SGPro(self.app)
            self.MaximDL = maximdl.MaximDLCamera(self.app)
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.TheSkyX = theskyx.TheSkyX(self.app)
        self.NoneCam = none.NoneCamera(self.app)
        self.INDICamera = indicamera.INDICamera(self.app)
        # select default application
        self.imagingAppHandler = self.NoneCam

        self.chooserLock = threading.Lock()
        # run it first, to set all imaging applications up
        self.chooseImaging()

    def initConfig(self):
        try:
            if 'ImagingApplication' in self.app.config:
                self.app.ui.pd_chooseImaging.setCurrentIndex(int(self.app.config['ImagingApplication']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        if self.NoneCam.appAvailable:
            self.app.ui.pd_chooseImaging.addItem('No Application')
        if self.INDICamera.appAvailable:
            self.app.ui.pd_chooseImaging.addItem('INDI Camera')
        if platform.system() == 'Windows':
            if self.SGPro.appAvailable:
                self.app.ui.pd_chooseImaging.addItem('SGPro - ' + self.SGPro.appName)
            if self.MaximDL.appAvailable:
                self.app.ui.pd_chooseImaging.addItem('MaximDL - ' + self.MaximDL.appName)
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            if self.TheSkyX.appAvailable:
                self.app.ui.pd_chooseImaging.addItem('TheSkyX - ' + self.TheSkyX.appName)
        # connect change in imaging app to the subroutine of setting it up
        self.app.ui.pd_chooseImaging.currentIndexChanged.connect(self.chooseImaging)

    def storeConfig(self):
        self.app.config['ImagingApplication'] = self.app.ui.pd_chooseImaging.currentIndex()

    def chooseImaging(self):
        self.chooserLock.acquire()
        self.app.ui.btn_runBoostModel.setVisible(False)
        self.app.ui.btn_runBoostModel.setEnabled(False)
        if self.imagingAppHandler.cameraConnected:
            self.imagingAppHandler.disconnectCamera()
        if self.app.ui.pd_chooseImaging.currentText().startswith('No Application'):
            self.imagingAppHandler = self.NoneCam
            self.logger.info('actual camera / plate solver is None')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('INDI Camera'):
            self.imagingAppHandler = self.INDICamera
            self.logger.info('actual camera / plate solver is INDI Camera')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('SGPro'):
            self.imagingAppHandler = self.SGPro
            self.app.ui.btn_runBoostModel.setEnabled(True)
            self.app.ui.btn_runBoostModel.setVisible(True)
            self.logger.info('actual camera / plate solver is SGPro')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('TheSkyX'):
            self.imagingAppHandler = self.TheSkyX
            self.logger.info('actual camera / plate solver is TheSkyX')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('MaximDL'):
            self.imagingAppHandler = self.MaximDL
            self.logger.info('actual camera / plate solver is MaximDL')
        self.imagingAppHandler.checkAppStatus()
        self.imagingAppHandler.connectCamera()
        self.chooserLock.release()

    def prepareImaging(self, directory):
        modelData = {}
        # do all the calculations once
        suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.workerModeling.imagingApps.imagingAppHandler.getCameraProps()
        if suc:
            self.logger.info('camera props: {0}, {1}, {2}'.format(sizeX, sizeY, canSubframe))
        else:
            self.logger.warning('SgGetCameraProps with error: {0}'.format(mes))
            return {}
        if canSubframe and self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            modelData['SizeX'] = int(sizeX * scaleSubframe)
            modelData['SizeY'] = int(sizeY * scaleSubframe)
            modelData['OffX'] = int((sizeX - modelData['SizeX']) / 2)
            modelData['OffY'] = int((sizeY - modelData['SizeY']) / 2)
            modelData['CanSubframe'] = True
        else:
            modelData['SizeX'] = 0
            modelData['SizeY'] = 0
            modelData['OffX'] = 0
            modelData['OffY'] = 0
            modelData['CanSubframe'] = False
            self.logger.warning('Camera does not support subframe.')
        modelData['GainValue'] = gainValue
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
        if self.app.workerModeling.cancel:
            self.logger.info('Modeling cancelled after capturing image')
            return False, 'Cancel modeling pressed', modelData
        LocalSiderealTimeFitsHeader = modelData['LocalSiderealTime'][0:10]
        RaJ2000FitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['RaJ2000'], False, False, ' ')
        DecJ2000FitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['DecJ2000'], True, False, ' ')
        RaJNowFitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['RaJNow'], False, True, ' ')
        DecJNowFitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['DecJNow'], True, True, ' ')
        if modelData['Pierside'] == '1':
            pierside_fits_header = 'E'
        else:
            pierside_fits_header = 'W'
        self.logger.info('modelData: {0}'.format(modelData))
        suc, mes, modelData = self.app.workerModeling.imagingApps.imagingAppHandler.getImage(modelData)
        if suc:
            if simulation:
                if getattr(sys, 'frozen', False):
                    # we are running in a bundle
                    bundle_dir = sys._MEIPASS
                else:
                    # we are running in a normal Python environment
                    bundle_dir = os.path.dirname(sys.modules['__main__'].__file__)
                shutil.copyfile(bundle_dir + self.app.workerModeling.REF_PICTURE, modelData['ImagePath'])
            else:
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
        ra, dec = self.app.workerModeling.transform.transformERFA(modelData['RaJ2000Solved'], modelData['DecJ2000Solved'], 3)
        modelData['RaJNowSolved'] = ra
        modelData['DecJNowSolved'] = dec
        modelData['RaError'] = (modelData['RaJ2000Solved'] - modelData['RaJ2000']) * 3600
        modelData['DecError'] = (modelData['DecJ2000Solved'] - modelData['DecJ2000']) * 3600
        modelData['ModelError'] = math.sqrt(modelData['RaError'] * modelData['RaError'] + modelData['DecError'] * modelData['DecError'])
        return modelData

    def solveImage(self, modelData, simulation):
        modelData['UseFitsHeaders'] = True
        suc, mes, modelData = self.app.workerModeling.imagingApps.imagingAppHandler.solveImage(modelData)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            ra_sol_Jnow, dec_sol_Jnow = self.app.workerModeling.transform.transformERFA(modelData['RaJ2000Solved'], modelData['DecJ2000Solved'], 3)
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

    def plateSolveSync(self, simulation=False):
        self.app.modelLogQueue.put('delete')
        self.app.modelLogQueue.put('{0} - Start Sync Mount Model\n'.format(self.timeStamp()))
        modelData = {}
        modelData = self.prepareImaging(modelData, '')
        modelData['base_dir_images'] = self.app.workerModeling.IMAGEDIR + '/platesolvesync'
        self.logger.info('modelData: {0}'.format(modelData))
        self.app.mountCommandQueue.put('PO')
        self.app.mountCommandQueue.put('AP')
        if not os.path.isdir(modelData['BaseDirImages']):
            os.makedirs(modelData['BaseDirImages'])
        modelData['File'] = 'platesolvesync.fit'
        modelData['LocalSiderealTime'] = self.app.mount.sidereal_time[0:9]
        modelData['LocalSiderealTimeFloat'] = self.app.workerModeling.transform.degStringToDecimal(
            self.app.mount.sidereal_time[0:9])
        modelData['RaJ2000'] = self.app.mount.data['RaJ2000']
        modelData['DecJ2000'] = self.app.mount.data['DecJ2000']
        modelData['RaJNow'] = self.app.mount.data['RaJNow']
        modelData['DecJNow'] = self.app.mount.data['DecJNow']
        modelData['Pierside'] = self.app.mount.data['Pierside']
        modelData['RefractionTemperature'] = self.app.mount.data['RefractionTemperature']
        modelData['RefractionPressure'] = self.app.mount.data['RefractionPressure']
        modelData['Azimuth'] = 0
        modelData['Altitude'] = 0
        self.app.modelLogQueue.put('{0} -\t Capturing image\n'.format(self.timeStamp()))
        suc, mes, imagepath = self.capturingImage(modelData, simulation)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            self.app.modelLogQueue.put('{0} -\t Solving Image\n'.format(self.timeStamp()))
            suc, mes, modelData = self.solveImage(modelData, simulation)
            self.app.modelLogQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['ImagePath']))
            if suc:
                suc = self.app.mount.syncMountModel(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                if suc:
                    self.app.modelLogQueue.put('{0} -\t Mount Model Synced\n'.format(self.timeStamp()))
                else:
                    self.app.modelLogQueue.put(
                        '{0} -\t Mount Model could not be synced - please check!\n'.format(self.timeStamp()))
            else:
                self.app.modelLogQueue.put('{0} -\t Solving error: {1}\n'.format(self.timeStamp(), mes))
        if not self.app.ui.checkKeepImages.isChecked():
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.modelLogQueue.put('{0} - Sync Mount Model finished !\n'.format(self.timeStamp()))
