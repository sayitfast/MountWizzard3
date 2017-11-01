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
import copy
import logging
import os
import sys
import shutil
import time
import datetime
import PyQt5
import pyfits
from queue import Queue
from modeling.modelBase import ModelBase


class Slewpoint(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queuePoint = Queue()
    signalSlewing = PyQt5.QtCore.pyqtSignal(name='slew')

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.isRunning = True
        self.signalSlewing.connect(self.slewing)

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        if not self.isRunning:
            self.isRunning = True
        while self.isRunning:
            PyQt5.QtWidgets.QApplication.processEvents()

    @PyQt5.QtCore.pyqtSlot()
    def stop(self):
        self.isRunning = False

    @PyQt5.QtCore.pyqtSlot()
    def slewing(self):
        if not self.queuePoint.empty():
            modelData = self.queuePoint.get()
            if modelData['Item'].isVisible():
                self.main.app.modelLogQueue.put('#BG{0} - Slewing to point {1:2d}  @ Az: {2:3.0f}\xb0 Alt: {3:2.0f}\xb0\n'.format(self.main.timeStamp(), modelData['Index'] + 1, modelData['Azimuth'], modelData['Altitude']))
                self.main.slewMountDome(modelData['Azimuth'], modelData['Altitude'])
                self.main.app.modelLogQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec\n'.format(self.main.timeStamp(), modelData['SettlingTime']))
                timeCounter = modelData['SettlingTime']
                while timeCounter > 0:
                    time.sleep(1)
                    timeCounter -= 1
            self.main.workerImage.queueImage.put(modelData)


class Image(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queueImage = Queue()
    signalImaging = PyQt5.QtCore.pyqtSignal(name='image')

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.isRunning = True

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        if not self.isRunning:
            self.isRunning = True
        while self.isRunning:
            PyQt5.QtWidgets.QApplication.processEvents()
            if not self.queueImage.empty():
                modelData = self.queueImage.get()
                modelData['File'] = self.main.app.modeling.CAPTUREFILE + '{0:03d}'.format(modelData['Index']) + '.fit'
                modelData['LocalSiderealTime'] = self.main.app.mount.data['LocalSiderealTime']
                modelData['LocalSiderealTimeFloat'] = self.main.app.modeling.transform.degStringToDecimal(self.main.app.mount.data['LocalSiderealTime'][0:9])
                modelData['RaJ2000'] = self.main.app.mount.data['RaJ2000']
                modelData['DecJ2000'] = self.main.app.mount.data['DecJ2000']
                modelData['RaJNow'] = self.main.app.mount.data['RaJNow']
                modelData['DecJNow'] = self.main.app.mount.data['DecJNow']
                modelData['Pierside'] = self.main.app.mount.data['Pierside']
                modelData['RefractionTemperature'] = self.main.app.mount.data['RefractionTemperature']
                modelData['RefractionPressure'] = self.main.app.mount.data['RefractionPressure']
                self.main.app.modelLogQueue.put('{0} -\t Capturing image for modeling point {1:2d}\n'.format(self.main.timeStamp(), modelData['Index'] + 1))
                while True:
                    suc, mes = self.main.app.modeling.SGPro.SgGetDeviceStatus('Camera')
                    if suc and mes == 'IDLE':
                            break
                suc, mes, imagepath = self.main.capturingImage(modelData, modelData['Simulation'])
                self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
                modelData['ImagingSuccess'] = suc
                # self.main.workerSlewpoint.signalSlewing.emit()
                self.main.workerPlatesolve.queuePlatesolve.put(modelData)

    @PyQt5.QtCore.pyqtSlot()
    def stop(self):
        self.isRunning = False


class Platesolve(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queuePlatesolve = Queue()
    signalPlatesolveFinished = PyQt5.QtCore.pyqtSignal(name='platesolveFinished')

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.isRunning = True

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        if not self.isRunning:
            self.isRunning = True
        while self.isRunning:
            PyQt5.QtWidgets.QApplication.processEvents()
            if not self.queuePlatesolve.empty():
                modelData = self.queuePlatesolve.get()
                if modelData['ImagingSuccess']:
                    self.main.app.modelLogQueue.put('{0} -\t Solving Image\n'.format(self.main.timeStamp()))
                    suc, mes, modelData = self.main.solveImage(modelData, modelData['Simulation'])
                    modelData['PlateSolveSuccess'] = suc
                    if modelData['PlateSolveSuccess']:
                        self.main.app.modelLogQueue.put('{0} -\t Image path: {1}\n'.format(self.main.timeStamp(), modelData['ImagePath']))
                        modelData['Item'].setVisible(False)
                    else:
                        self.main.app.modelLogQueue.put('{0} -\t Solving error: {1}\n'.format(self.main.timeStamp(), mes))
                del modelData['Item']
                del modelData['Simulation']
                del modelData['SettlingTime']
                self.main.solvedPointsQueue.put(modelData)
                self.main.app.modelLogQueue.put('status{0} of {1}'.format(modelData['Index'] + 1, self.main.numberPointsMax))
                self.main.numberSolvedPoints += 1
                if self.main.numberSolvedPoints == self.main.numberPointsMax:
                    self.main.hasFinished = True

    @PyQt5.QtCore.pyqtSlot()
    def stop(self):
        self.isRunning = False


class ModelBoost(ModelBase):

    def __init__(self, app):
        super(ModelBoost, self).__init__(app)
        # make main sources available
        self.app = app
        self.modelData = None
        self.results = []
        self.solvedPointsQueue = Queue()
        self.modelRun = False
        self.hasFinished = False
        self.numberPointsMax = 0
        self.numberSolvedPoints = 0
        # initialize the parallel thread modeling parts
        self.workerSlewpoint = Slewpoint(self)
        self.threadSlewpoint = PyQt5.QtCore.QThread()
        self.workerSlewpoint.moveToThread(self.threadSlewpoint)
        self.threadSlewpoint.started.connect(self.workerSlewpoint.run)
        # self.threadSlewpoint.start()
        self.workerImage = Image(self)
        self.threadImage = PyQt5.QtCore.QThread()
        self.workerImage.moveToThread(self.threadImage)
        self.threadImage.started.connect(self.workerImage.run)
        # self.threadImage.start()
        self.workerPlatesolve = Platesolve(self)
        self.threadPlatesolve = PyQt5.QtCore.QThread()
        self.workerPlatesolve.moveToThread(self.threadPlatesolve)
        self.threadPlatesolve.started.connect(self.workerPlatesolve.run)
        # self.threadPlatesolve.start()

    def capturingImage(self, modelData, simulation):
        if self.app.modeling.cancel:
            self.logger.info('Modeling cancelled while capturing image')
            return False, 'Modeling cancelled by user', modelData
        suc, mes, guid = self.app.modeling.SGPro.SgCaptureImage(binningMode=modelData['Binning'],
                                                                exposureLength=modelData['Exposure'],
                                                                iso=str(modelData['Iso']),
                                                                gain=modelData['GainValue'],
                                                                speed=modelData['Speed'],
                                                                frameType='Light',
                                                                filename=modelData['File'],
                                                                path=modelData['BaseDirImages'],
                                                                useSubframe=modelData['CanSubframe'],
                                                                posX=modelData['OffX'],
                                                                posY=modelData['OffY'],
                                                                width=modelData['SizeX'],
                                                                height=modelData['SizeY'])
        modelData['ImagePath'] = ''
        self.logger.info('Capture Image from SGPro {0}, {1}, {2}'.format(suc, mes, guid))
        if suc:
            # waiting for the start of integration
            time.sleep(1)
            # storing the mount and environment data
            modelData['LocalSiderealTime'] = self.app.mount.sidereal_time[0:9]
            modelData['LocalSiderealTimeFloat'] = self.app.modeling.transform.degStringToDecimal(self.app.mount.sidereal_time[0:9])
            modelData['RaJ2000'] = self.app.mount.data['RaJ2000']
            modelData['DecJ2000'] = self.app.mount.data['DecJ2000']
            modelData['RaJNow'] = self.app.mount.data['RaJNow']
            modelData['DecJNow'] = self.app.mount.data['DecJNow']
            modelData['Pierside'] = self.app.mount.data['Pierside']
            modelData['RefractionTemperature'] = self.app.mount.data['RefractionTemperature']
            modelData['RefractionPressure'] = self.app.mount.data['RefractionPressure']
            modelData['Azimuth'] = 0
            modelData['Altitude'] = 0
            # waiting for the end of integration
            while True:
                suc, mes = self.app.modeling.SGPro.SgGetDeviceStatus('Camera')
                if suc:
                    if mes != 'INTEGRATING':
                        break
            self.app.modeling.modelBoost.workerSlewpoint.signalSlewing.emit()
            # waiting for downloading and storing the image as fits file
            # todo: what if there is no fits file ?
            while True:
                suc, modelData['ImagePath'] = self.app.modeling.SGPro.SgGetImagePath(guid)
                if suc:
                    break
                else:
                    time.sleep(0.5)
            # I got a fits file, than i have to add some data
            LocalSiderealTimeFitsHeader = modelData['LocalSiderealTime'][0:10]
            RaJ2000FitsHeader = self.app.modeling.transform.decimalToDegree(modelData['RaJ2000'], False, False, ' ')
            DecJ2000FitsHeader = self.app.modeling.transform.decimalToDegree(modelData['DecJ2000'], True, False, ' ')
            RaJNowFitsHeader = self.app.modeling.transform.decimalToDegree(modelData['RaJNow'], False, True, ' ')
            DecJNowFitsHeader = self.app.modeling.transform.decimalToDegree(modelData['DecJNow'], True, True, ' ')
            if modelData['Pierside'] == '1':
                pierside_fits_header = 'E'
            else:
                pierside_fits_header = 'W'
            # if i do simulation i copy a real image instead of using the simulated image of the camera
            if simulation:
                if getattr(sys, 'frozen', False):
                    # we are running in a bundle
                    bundle_dir = sys._MEIPASS
                else:
                    # we are running in a normal Python environment
                    bundle_dir = os.path.dirname(sys.modules['__main__'].__file__)
                shutil.copyfile(bundle_dir + self.app.modeling.REF_PICTURE, modelData['ImagePath'])
            else:
                self.logger.info('suc: {0}, modelData{1}'.format(suc, modelData))
                fitsFileHandle = pyfits.open(modelData['ImagePath'], mode='update')
                fitsHeader = fitsFileHandle[0].header
                if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                    modelData['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
                fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()
                # i have to update the header for coordinates, because telescope will slew, when the download takes place and i don't know
                # at which point in time the coordinates are taken from the mount by SGPro. Ideally it is the time, when imaging is starting
                # than it's not necessary
                fitsHeader['OBJCTRA'] = RaJ2000FitsHeader
                fitsHeader['OBJCTDEC'] = DecJ2000FitsHeader
                # the rest of the information is needed for the solver to find the appropriate solution. There are different fields possible
                fitsHeader['CDELT1'] = str(modelData['ScaleHint'])
                fitsHeader['CDELT2'] = str(modelData['ScaleHint'])
                fitsHeader['PIXSCALE'] = str(modelData['ScaleHint'])
                fitsHeader['SCALE'] = str(modelData['ScaleHint'])
                # additional Information from MountWizzard should be stored in fits file
                fitsHeader['MW_MRA'] = RaJNowFitsHeader
                fitsHeader['MW_MDEC'] = DecJNowFitsHeader
                fitsHeader['MW_ST'] = LocalSiderealTimeFitsHeader
                fitsHeader['MW_MSIDE'] = pierside_fits_header
                fitsHeader['MW_EXP'] = modelData['Exposure']
                fitsHeader['MW_AZ'] = modelData['Azimuth']
                fitsHeader['MW_ALT'] = modelData['Altitude']
                fitsFileHandle.flush()
                fitsFileHandle.close()
                self.logger.info('Fits header rewritten')
            # show the picture automatically in image window - if opened
            self.app.imageQueue.put(modelData['ImagePath'])
            return True, 'OK', modelData

    # noinspection PyUnresolvedReferences
    def runModel(self):
        settlingTime, directory = self.setupRunningParameters()
        if len(self.app.modeling.modelPoints.RefinementPoints) > 0:
            if self.app.ui.checkKeepRefinement.isChecked():
                self.app.mount.loadRefinementModel()
            else:
                self.app.mount.loadBaseModel()
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            self.modelData = self.runBoost(self.app.modeling.modelPoints.RefinementPoints, directory, settlingTime, simulation, keepImages)
            self.modelData = self.app.mount.retrofitMountData(self.modelData)
            name = directory + '_boost.dat'
            if len(self.modelData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.app.modeling.analyse.saveData(self.modelData, name)
                self.app.mount.saveRefinementModel()
        else:
            self.logger.warning('There are no Refinement Points to modeling')

    def runBoost(self, runPoints, directory, settlingTime, simulation=False, keepImages=False):
        # start clearing the data
        modelData = {}
        results = []
        # preparing the gui outputs
        self.app.modelLogQueue.put('status-- of --')
        self.app.modelLogQueue.put('percent0')
        self.app.modelLogQueue.put('timeleft--:--')
        self.app.modelLogQueue.put('delete')
        self.app.modelLogQueue.put('#BW{0} - Start Boost Model\n'.format(self.timeStamp()))
        modelData = self.prepareImaging(modelData, directory)
        if not os.path.isdir(modelData['BaseDirImages']):
            os.makedirs(modelData['BaseDirImages'])
        self.logger.info('modelData: {0}'.format(modelData))
        self.app.mountCommandQueue.put('PO')
        self.app.mountCommandQueue.put('AP')
        self.app.modeling.modelRun = True
        self.threadSlewpoint.start()
        self.threadImage.start()
        self.threadPlatesolve.start()
        # here starts the real model running cycle
        # loading all the point in queue
        for i, (p_az, p_alt, p_item, p_solve) in enumerate(runPoints):
            if p_item.isVisible() and p_solve:
                modelData['Index'] = i
                modelData['Azimuth'] = p_az
                modelData['Altitude'] = p_alt
                modelData['Item'] = p_item
                modelData['SettlingTime'] = settlingTime
                modelData['Simulation'] = simulation
                self.workerSlewpoint.queuePoint.put(copy.copy(modelData))
        self.numberPointsMax = len(runPoints)
        # start process
        self.hasFinished = False
        self.workerSlewpoint.signalSlewing.emit()
        while self.app.modeling.modelRun:
            PyQt5.QtWidgets.QApplication.processEvents()
            # stop loop if cancelled
            if self.app.modeling.cancel:
                break
            # stop loop if finished
            if self.hasFinished:
                break
        if self.app.modeling.cancel:
            # clearing the gui
            self.app.modelLogQueue.put('status-- of --')
            self.app.modelLogQueue.put('percent0')
            self.app.modelLogQueue.put('timeleft--:--')
            self.logger.info('Modeling cancelled in main loop')
        self.workerSlewpoint.stop()
        self.threadSlewpoint.quit()
        self.threadSlewpoint.wait()
        self.workerImage.stop()
        self.threadImage.quit()
        self.threadImage.wait()
        self.workerPlatesolve.stop()
        self.threadPlatesolve.quit()
        self.threadPlatesolve.wait()
        self.app.modeling.modelRun = False
        while not self.solvedPointsQueue.empty():
            results.append(self.solvedPointsQueue.get())
        if not keepImages:
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.modelLogQueue.put('#BW{0} - Boost Model run finished. Number of modeled points: {1:3d}\n\n'.format(self.timeStamp(), self.numberSolvedPoints))
        return results
