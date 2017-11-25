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
import copy
import os
import shutil
import time
import PyQt5
# Cameras
from modeling import imagingApps
# analyse save functions
from analyse import analysedata
# modelPoints
from modeling import modelingPoints
# transformations
from astrometry import transform
from queue import Queue


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
        self.queuePoint.queue.clear()

    @PyQt5.QtCore.pyqtSlot()
    def slewing(self):
        if not self.queuePoint.empty():
            modelData = self.queuePoint.get()
            if modelData['Item'].isVisible():
                self.main.app.messageQueue.put('#BG{0} - Slewing to point {1:2d}  @ Az: {2:3.0f}\xb0 Alt: {3:2.0f}\xb0\n'.format(self.main.timeStamp(), modelData['Index'] + 1, modelData['Azimuth'], modelData['Altitude']))
                self.main.slewMountDome(modelData['Azimuth'], modelData['Altitude'])
                self.main.app.messageQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec\n'.format(self.main.timeStamp(), modelData['SettlingTime']))
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
                modelData['File'] = self.main.app.workerModeling.CAPTUREFILE + '{0:03d}'.format(modelData['Index']) + '.fit'
                modelData['LocalSiderealTime'] = self.main.app.mount.data['LocalSiderealTime']
                modelData['LocalSiderealTimeFloat'] = self.main.app.workerModeling.transform.degStringToDecimal(self.main.app.mount.data['LocalSiderealTime'][0:9])
                modelData['RaJ2000'] = self.main.app.mount.data['RaJ2000']
                modelData['DecJ2000'] = self.main.app.mount.data['DecJ2000']
                modelData['RaJNow'] = self.main.app.mount.data['RaJNow']
                modelData['DecJNow'] = self.main.app.mount.data['DecJNow']
                modelData['Pierside'] = self.main.app.mount.data['Pierside']
                modelData['RefractionTemperature'] = self.main.app.mount.data['RefractionTemperature']
                modelData['RefractionPressure'] = self.main.app.mount.data['RefractionPressure']
                self.main.app.messageQueue.put('{0} -\t Capturing image for model point {1:2d}\n'.format(self.main.timeStamp(), modelData['Index'] + 1))
                while True:
                    suc, mes = self.main.app.workerModeling.SGPro.SgGetDeviceStatus('Camera')
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
        self.queueImage.queue.clear()


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
                    self.main.app.messageQueue.put('{0} -\t Solving image for model point {1}\n'.format(self.main.timeStamp(), modelData['Index'] + 1))
                    suc, mes, modelData = self.main.solveImage(modelData, modelData['Simulation'])
                    modelData['PlateSolveSuccess'] = suc
                    if modelData['PlateSolveSuccess']:
                        self.main.app.messageQueue.put('{0} -\t Image path: {1}\n'.format(self.main.timeStamp(), modelData['ImagePath']))
                        self.main.app.messageQueue.put('{0} -\t RA_diff:  {1:2.1f}    DEC_diff: {2:2.1f}\n'.format(self.main.timeStamp(), modelData['RaError'], modelData['DecError']))

                        modelData['Item'].setVisible(False)
                    else:
                        self.main.app.messageQueue.put('{0} -\t Solving error: {1}\n'.format(self.main.timeStamp(), mes))
                self.main.solvedPointsQueue.put(modelData)
                self.main.app.messageQueue.put('status{0} of {1}'.format(modelData['Index'] + 1, self.main.numberPointsMax))
                self.main.numberSolvedPoints += 1
                if self.main.numberSolvedPoints == self.main.numberPointsMax:
                    self.main.hasFinished = True

    @PyQt5.QtCore.pyqtSlot()
    def stop(self):
        self.isRunning = False
        self.queuePlatesolve.queue.clear()


class ModelingBase:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        # make main sources available
        self.app = app
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
        self.solvedPointsQueue = Queue()
        self.timeStart = 0
        self.results = []
        self.modelingResultData = []
        self.modelData = []
        self.modelRun = False
        self.hasFinished = False
        self.numberPointsMax = 0
        self.numberSolvedPoints = 0
        self.cancel = False
        self.analyseData = analysedata.Analyse(app)
        # assign support classes
        self.transform = transform.Transform(app)
        self.modelPoints = modelingPoints.ModelPoints(self.app)
        self.imagingApps = imagingApps.ImagingApps(app)
        self.initConfig()

    def initConfig(self):
        pass

    def storeConfig(self):
        self.imagingApps.storeConfig()

    @staticmethod
    def timeStamp():
        return time.strftime("%H:%M:%S", time.localtime())

    def clearAlignmentModel(self):
        self.modelingResultData = []
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
            self.app.domeCommandQueue.put(('SlewAzimuth', az))
            while not self.app.mount.data['Slewing'] and not self.app.workerDome.data['Slewing']:
                if self.cancel:
                    self.logger.info('Modeling cancelled after mount slewing')
                    break
                time.sleep(0.1)
            while self.app.mount.data['Slewing'] or self.app.workerAscomDome.data['Slewing']:
                if self.cancel:
                    self.logger.info('Modeling cancelled after dome slewing')
                    break
                time.sleep(0.1)
        else:
            while self.app.mount.data['Slewing']:
                if self.app.workerModelingDispatcher.modelingRunner.cancel:
                    self.logger.info('Modeling cancelled after mount slewing')
                    break
                time.sleep(0.1)

    def checkModelingAvailable(self):
        if not self.app.mount.mountHandler.connected or not self.imagingApps.imagingWorkerAppHandler.isRunning:
            return False
        else:
            return True

    def plateSolveSync(self, simulation=False):
        self.app.messageQueue.put('{0} - Start Sync Mount Model\n'.format(self.timeStamp()))
        modelData = {}
        modelData = self.imagingApps.prepareImaging(modelData, '')
        modelData['base_dir_images'] = self.app.workerModeling.IMAGEDIR + '/platesolvesync'
        self.logger.info('modelData: {0}'.format(modelData))
        self.app.mountCommandQueue.put('PO')
        self.app.mountCommandQueue.put('AP')
        if not os.path.isdir(modelData['BaseDirImages']):
            os.makedirs(modelData['BaseDirImages'])
        modelData['File'] = 'platesolvesync.fit'
        modelData['LocalSiderealTime'] = self.app.mount.sidereal_time[0:9]
        modelData['LocalSiderealTimeFloat'] = self.transform.degStringToDecimal(self.app.mount.sidereal_time[0:9])
        modelData['RaJ2000'] = self.app.mount.data['RaJ2000']
        modelData['DecJ2000'] = self.app.mount.data['DecJ2000']
        modelData['RaJNow'] = self.app.mount.data['RaJNow']
        modelData['DecJNow'] = self.app.mount.data['DecJNow']
        modelData['Pierside'] = self.app.mount.data['Pierside']
        modelData['RefractionTemperature'] = self.app.mount.data['RefractionTemperature']
        modelData['RefractionPressure'] = self.app.mount.data['RefractionPressure']
        modelData['Azimuth'] = 0
        modelData['Altitude'] = 0
        self.app.messageQueue.put('{0} -\t Capturing image\n'.format(self.timeStamp()))
        suc, mes, imagepath = self.imagingApps.capturingImage(modelData, simulation)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            self.app.messageQueue.put('{0} -\t Solving Image\n'.format(self.timeStamp()))
            suc, mes, modelData = self.imagingApps.solveImage(modelData, simulation)
            self.app.messageQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['ImagePath']))
            if suc:
                suc = self.app.mount.syncMountModel(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                if suc:
                    self.app.messageQueue.put('{0} -\t Mount Model Synced\n'.format(self.timeStamp()))
                else:
                    self.app.messageQueue.put('{0} -\t Mount Model could not be synced - please check!\n'.format(self.timeStamp()))
            else:
                self.app.messageQueue.put('{0} -\t Solving error: {1}\n'.format(self.timeStamp(), mes))
        if not self.app.ui.checkKeepImages.isChecked():
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.messageQueue.put('{0} - Sync Mount Model finished !\n'.format(self.timeStamp()))

    def runBoost(self, runPoints, modelData, settlingTime, simulation=False, keepImages=False):
        # start clearing the data
        results = []
        # preparing the gui outputs
        self.app.messageQueue.put('status-- of --')
        self.app.messageQueue.put('percent0')
        self.app.messageQueue.put('timeleft--:--')
        self.app.messageQueue.put('#BW{0} - Start Boost Model\n'.format(self.timeStamp()))
        if not os.path.isdir(modelData['BaseDirImages']):
            os.makedirs(modelData['BaseDirImages'])
        self.logger.info('modelData: {0}'.format(modelData))
        self.app.mountCommandQueue.put('PO')
        self.app.mountCommandQueue.put('AP')
        self.app.workerModeling.modelRun = True
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
        self.timeStart = time.time()
        self.hasFinished = False
        self.workerSlewpoint.signalSlewing.emit()
        while self.app.workerModeling.modelRun:
            PyQt5.QtWidgets.QApplication.processEvents()
            # stop loop if cancelled
            if self.app.workerModeling.cancel:
                break
            # stop loop if finished
            if self.hasFinished:
                break
        if self.app.workerModeling.cancel:
            # clearing the gui
            self.app.messageQueue.put('status-- of --')
            self.app.messageQueue.put('percent0')
            self.app.messageQueue.put('timeleft--:--')
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
        self.app.workerModeling.modelRun = False
        while not self.solvedPointsQueue.empty():
            modelData = self.solvedPointsQueue.get()
            # clean up intermediate data
            del modelData['Item']
            del modelData['Simulation']
            del modelData['SettlingTime']
            results.append(copy.copy(modelData))
        if not keepImages:
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.messageQueue.put('#BW{0} - Boost Model Step 1 finished. Number of images and solved points: {1:3d}\n\n'.format(self.timeStamp(), self.numberSolvedPoints))
        return results

    def runModel(self, modeltype, runPoints, modelData, settlingTime, simulation=False, keepImages=False):
        # start clearing the data
        results = []
        # preparing the gui outputs
        self.app.messageQueue.put('status-- of --')
        self.app.messageQueue.put('percent0')
        self.app.messageQueue.put('timeleft--:--')
        self.app.messageQueue.put('#BW{0} - Start {1} Model\n'.format(self.timeStamp(), modeltype))
        if not modelData:
            return []
        if not os.path.isdir(modelData['BaseDirImages']):
            os.makedirs(modelData['BaseDirImages'])
        self.logger.info('modelData: {0}'.format(modelData))
        self.app.mountCommandQueue.put('PO')
        self.app.mountCommandQueue.put('AP')
        # counter and timer for performance estimation
        numCheckPoints = 0
        timeStart = time.time()
        # here starts the real model running cycle
        for i, (p_az, p_alt, p_item, p_solve) in enumerate(runPoints):
            self.app.workerModelingDispatcher.modelingRunner.modelRun = True
            modelData['Azimuth'] = p_az
            modelData['Altitude'] = p_alt
            if p_item.isVisible():
                # todo: put the code to multi thread modeling
                if self.cancel:
                    self.app.messageQueue.put('#BW{0} -\t {1} Model canceled !\n'.format(self.timeStamp(), modeltype))
                    # tracking should be on after canceling the modeling
                    self.app.mountCommandQueue.put('AP')
                    # clearing the gui
                    self.app.messageQueue.put('status-- of --')
                    self.app.messageQueue.put('percent0')
                    self.app.messageQueue.put('timeleft--:--')
                    self.logger.info('Modeling cancelled in main loop')
                    # finally stopping modeling run
                    break
                self.app.messageQueue.put('#BG{0} - Slewing to point {1:2d}  @ Az: {2:3.0f}\xb0 Alt: {3:2.0f}\xb0\n'.format(self.timeStamp(), i+1, p_az, p_alt))
                self.logger.info('point {0:2d}  Az: {1:3.0f} Alt: {2:2.0f}'.format(i+1, p_az, p_alt))
                if modeltype in ['TimeChange']:
                    # in time change there is only slew for the first time, than only track during imaging
                    if i == 0:
                        self.slewMountDome(p_az, p_alt)
                        self.app.mountCommandQueue.put('RT9')
                else:
                    self.slewMountDome(p_az, p_alt)
                self.app.messageQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec'.format(self.timeStamp(), settlingTime))
                timeCounter = settlingTime
                while timeCounter > 0:
                    time.sleep(1)
                    timeCounter -= 1
                self.app.messageQueue.put('\n')
            if p_item.isVisible() and p_solve:
                modelData['File'] = self.imagingApps.CAPTUREFILE + '{0:03d}'.format(i) + '.fit'
                modelData['LocalSiderealTime'] = self.app.mount.data['LocalSiderealTime']
                modelData['LocalSiderealTimeFloat'] = self.transform.degStringToDecimal(self.app.mount.data['LocalSiderealTime'][0:9])
                modelData['RaJ2000'] = self.app.mount.data['RaJ2000']
                modelData['DecJ2000'] = self.app.mount.data['DecJ2000']
                modelData['RaJNow'] = self.app.mount.data['RaJNow']
                modelData['DecJNow'] = self.app.mount.data['DecJNow']
                modelData['Pierside'] = self.app.mount.data['Pierside']
                modelData['Index'] = i
                modelData['RefractionTemperature'] = self.app.mount.data['RefractionTemperature']
                modelData['RefractionPressure'] = self.app.mount.data['RefractionPressure']
                if modeltype in ['TimeChange']:
                    self.app.mountCommandQueue.put('AP')
                self.app.messageQueue.put('{0} -\t Capturing image for model point {1:2d}\n'.format(self.timeStamp(), i + 1))
                suc, mes, imagepath = self.imagingApps.capturingImage(modelData, simulation)
                if modeltype in ['TimeChange']:
                    self.app.mountCommandQueue.put('RT9')
                self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
                if suc:
                    self.app.messageQueue.put('{0} -\t Solving image for model point{1}\n'.format(self.timeStamp(), i + 1))
                    suc, mes, modelData = self.imagingApps.solveImage(modelData, simulation)
                    self.app.messageQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['ImagePath']))
                    if suc:
                        if modeltype in ['Base', 'Refinement', 'All']:
                            suc = self.app.mount.addRefinementStar(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                            if suc:
                                self.app.messageQueue.put('{0} -\t Point added\n'.format(self.timeStamp()))
                                numCheckPoints += 1
                                results.append(copy.copy(modelData))
                                p_item.setVisible(False)
                                PyQt5.QtWidgets.QApplication.processEvents()
                            else:
                                self.app.messageQueue.put('{0} -\t Point could not be added - please check!\n'.format(self.timeStamp()))
                                self.logger.info('raE:{0} decE:{1} star could not be added'.format(modelData['RaError'], modelData['DecError']))
                        self.app.messageQueue.put('{0} -\t RA_diff:  {1:2.1f}    DEC_diff: {2:2.1f}\n'.format(self.timeStamp(), modelData['RaError'], modelData['DecError']))
                        self.logger.info('modelData: {0}'.format(modelData))
                    else:
                        self.app.messageQueue.put('{0} -\t Solving error: {1}\n'.format(self.timeStamp(), mes))
                self.app.messageQueue.put('status{0} of {1}'.format(i+1, len(runPoints)))
                modelBuildDone = (i + 1) / len(runPoints)
                self.app.messageQueue.put('percent{0}'.format(modelBuildDone))
                actualTime = time.time() - timeStart
                timeCalculated = actualTime / (i + 1) * (len(runPoints) - i - 1)
                mm = int(timeCalculated / 60)
                ss = int(timeCalculated - 60 * mm)
                self.app.messageQueue.put('timeleft{0:02d}:{1:02d}'.format(mm, ss))
        if not keepImages:
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.messageQueue.put('#BW{0} - {1} Model run finished. Number of modeled points: {2:3d}\n'.format(self.timeStamp(), modeltype, numCheckPoints))
        self.app.workerModelingDispatcher.modelingRunner.modelRun = False
        return results
