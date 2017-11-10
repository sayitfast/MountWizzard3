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
import datetime
import logging
import math
import os
import random
import shutil
import sys
import time
# library for fits file handling
import pyfits


class ModelBase:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        # make main sources available
        self.app = app
        self.results = []
        self.modelRun = False

    @staticmethod
    def timeStamp():
        return time.strftime("%H:%M:%S", time.localtime())

    def clearAlignmentModel(self):
        self.app.workerModeling.modelAnalyseData = []
        self.app.mountCommandQueue.put('ClearAlign')
        time.sleep(4)

    def setupRunningParameters(self):
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        return settlingTime, directory

    def slewMountDome(self, az, alt):
        self.app.mountCommandQueue.put('Sz{0:03d}*{1:02d}'.format(int(az), int((az - int(az)) * 60 + 0.5)))
        self.app.mountCommandQueue.put('Sa+{0:02d}*{1:02d}'.format(int(alt), int((alt - int(alt)) * 60 + 0.5)))
        self.app.mountCommandQueue.put('MS')
        self.logger.info('Ascom Dome Thread running: {0}'.format(self.app.workerAscomDome.isRunning))
        break_counter = 0
        while not self.app.mount.data['Slewing']:
            time.sleep(0.1)
            break_counter += 1
            if break_counter == 30:
                break
        if self.app.workerAscomDome.isRunning:
            if az >= 360:
                az = 359.9
            elif az < 0.0:
                az = 0.0
            try:
                self.app.workerAscomDome.ascom.SlewToAzimuth(float(az))
            except Exception as e:
                self.logger.error('value: {0}, error: {1}'.format(az, e))
            self.logger.info('Azimuth:{0}'.format(az))
            while not self.app.mount.data['Slewing']:
                if self.app.workerModeling.cancel:
                    self.logger.info('Modeling cancelled after mount slewing')
                    break
                time.sleep(0.1)
            while self.app.mount.slewing or self.app.dome.slewing:
                if self.app.workerModeling.cancel:
                    self.logger.info('Modeling cancelled after dome slewing')
                    break
                time.sleep(0.1)
        else:
            while self.app.mount.data['Slewing']:
                if self.app.workerModeling.cancel:
                    self.logger.info('Modeling cancelled after mount slewing')
                    break
                time.sleep(0.1)

    def prepareImaging(self, modelData, directory):
        # do all the calculations once
        suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.workerModeling.imagingHandler.getCameraProps()
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
        modelData['BaseDirImages'] = self.app.workerModeling.IMAGEDIR + '/' + directory
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
        suc, mes, modelData = self.app.workerModeling.imagingHandler.getImage(modelData)
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
        suc, mes, modelData = self.app.workerModeling.imagingHandler.solveImage(modelData)
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

    def runBatchModel(self):
        nameDataFile = self.app.ui.le_analyseFileName.text()
        self.logger.info('modeling from {0}'.format(nameDataFile))
        data = self.app.workerModeling.analyse.loadData(nameDataFile)
        if not('RaJNow' in data and 'DecJNow' in data):
            self.logger.warning('RaJNow or DecJNow not in data file')
            self.app.modelLogQueue.put('{0} - mount coordinates missing\n'.format(self.timeStamp()))
            return
        if not('RaJNowSolved' in data and 'DecJNowSolved' in data):
            self.logger.warning('RaJNowSolved or DecJNowSolved not in data file')
            self.app.modelLogQueue.put('{0} - solved data missing\n'.format(self.timeStamp()))
            return
        if not('Pierside' in data and 'LocalSiderealTime' in data):
            self.logger.warning('Pierside and LocalSiderealTime not in data file')
            self.app.modelLogQueue.put('{0} - Time and Pierside missing\n'.format(self.timeStamp()))
            return
        self.app.mount.programBatchData(data)