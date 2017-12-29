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


def timeStamp():
    return time.strftime("%H:%M:%S", time.localtime())


class ModelingRunner:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        # make environment available to class
        self.app = app

        # assign support classes
        self.analyseData = analysedata.Analyse(self.app)
        self.transform = self.app.transform
        self.modelPoints = modelingPoints.ModelPoints(self.app)
        self.imagingApps = imagingApps.ImagingApps(self.app)

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

        # class variables
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

    def initConfig(self):
        self.imagingApps.initConfig()
        self.modelPoints.initConfig()

    def storeConfig(self):
        self.imagingApps.storeConfig()
        self.modelPoints.storeConfig()

    def run(self):
        pass

    def stop(self):
        pass

    def clearAlignmentModel(self):
        # clearing the older results, because they are invalid afterwards
        self.modelingResultData = []
        # clearing the mount model and wait 4 seconds for the mount computer to recover (I don't know why, but Per Frejval did it)
        self.app.mountCommandQueue.put('ClearAlign')
        time.sleep(4)

    def checkModelingAvailable(self):
        # modeling is available when mount connected and imaging is running
        return self.app.workerMountDispatcher.workerMountStatusRunnerFast.connected and self.imagingApps.imagingWorkerAppHandler.isRunning

    def slewMountDome(self, azimuth, altitude, domeIsConnected):
        # limit azimuth and altitude
        if azimuth >= 360:
            azimuth = 359.9
        elif azimuth < 0.0:
            azimuth = 0.0
        # setting the coordinates for the mount
        self.app.mountCommandQueue.put('Sz{0:03d}*{1:02d}'.format(int(azimuth), int((azimuth - int(azimuth)) * 60 + 0.5)))
        self.app.mountCommandQueue.put('Sa+{0:02d}*{1:02d}'.format(int(altitude), int((altitude - int(altitude)) * 60 + 0.5)))
        self.app.mountCommandQueue.put('MS')
        # if there is a dome connected, we have to start slewing it, too
        counterMaxWait = 0
        if domeIsConnected:
            self.app.domeCommandQueue.put(('SlewAzimuth', azimuth))
            # now we wait for both start slewing
            while not self.app.mount.data['Slewing'] and not self.app.workerDome.data['Slewing']:
                counterMaxWait += 1
                # there might be the situation that no slew is needed or slew time is short
                if self.cancel or counterMaxWait == 10:
                    self.logger.info('Modeling cancelled in loop mount and dome wait while for start slewing')
                    break
                time.sleep(0.2)
            # and waiting for both to stop slewing
            while self.app.mount.data['Slewing'] or self.app.workerAscomDome.data['Slewing']:
                if self.cancel:
                    self.logger.info('Modeling cancelled in loop mount and dome wait while for stop slewing')
                    break
                time.sleep(0.2)
        else:
            # if there is no dome, we wait for the mount start slewing
            while not self.app.mount.data['Slewing']:
                counterMaxWait += 1
                # there might be the situation that no slew is needed or slew time is short
                if self.cancel or counterMaxWait == 10:
                    self.logger.info('Modeling cancelled in loop mount wait while for start slewing')
                    break
                time.sleep(0.2)
            # and the mount stop slewing
            while self.app.mount.data['Slewing']:
                if self.cancel:
                    self.logger.info('Modeling cancelled in loop mount wait while for stop slewing')
                    break
                time.sleep(0.2)

    def runBoost(self, messageQueue, runPoints, modelData, settlingTime, simulation=False, keepImages=False):
        # start clearing the data
        results = []
        # preparing the gui outputs
        messageQueue.put('status-- of --')
        messageQueue.put('percent0')
        messageQueue.put('timeleft--:--')
        messageQueue.put('#BW{0} - Start Boost Model\n'.format(timeStamp()))
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
            messageQueue.put('status-- of --')
            messageQueue.put('percent0')
            messageQueue.put('timeleft--:--')
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
        messageQueue.put('#BW{0} - Boost Model Step 1 finished. Number of images and solved points: {1:3d}\n\n'.format(timeStamp(), self.numberSolvedPoints))
        return results

    def runModel(self, messageQueue, modeltype, runPoints, modelData, settlingTime, simulation=False, keepImages=False, domeIsConnected=False):
        # start clearing the data
        results = []
        # preparing the gui outputs
        messageQueue.put('status-- of --')
        messageQueue.put('percent0')
        messageQueue.put('timeleft--:--')
        messageQueue.put('#BW{0} - Start {1} Model\n'.format(timeStamp(), modeltype))
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
            self.modelRun = True
            modelData['Azimuth'] = p_az
            modelData['Altitude'] = p_alt
            if p_item.isVisible():
                # todo: put the code to multi thread modeling
                if self.cancel:
                    messageQueue.put('#BW{0} -\t {1} Model canceled !\n'.format(timeStamp(), modeltype))
                    # tracking should be on after canceling the modeling
                    self.app.mountCommandQueue.put('AP')
                    # clearing the gui
                    messageQueue.put('status-- of --')
                    messageQueue.put('percent0')
                    messageQueue.put('timeleft--:--')
                    self.logger.info('Modeling cancelled in main loop')
                    # finally stopping modeling run
                    break
                messageQueue.put('#BG{0} - Slewing to point {1:2d}  @ Az: {2:3.0f}\xb0 Alt: {3:2.0f}\xb0\n'.format(timeStamp(), i + 1, p_az, p_alt))
                self.logger.info('point {0:2d}  Az: {1:3.0f} Alt: {2:2.0f}'.format(i+1, p_az, p_alt))
                if modeltype in ['TimeChange']:
                    # in time change there is only slew for the first time, than only track during imaging
                    if i == 0:
                        self.slewMountDome(p_az, p_alt, domeIsConnected)
                        self.app.mountCommandQueue.put('RT9')
                else:
                    self.slewMountDome(p_az, p_alt, domeIsConnected)
                messageQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec'.format(timeStamp(), settlingTime))
                timeCounter = settlingTime
                while timeCounter > 0:
                    time.sleep(1)
                    timeCounter -= 1
                messageQueue.put('\n')
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
                messageQueue.put('{0} -\t Capturing image for model point {1:2d}\n'.format(timeStamp(), i + 1))
                suc, mes, imagepath = self.imagingApps.capturingImage(modelData, simulation)
                if modeltype in ['TimeChange']:
                    self.app.mountCommandQueue.put('RT9')
                self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
                if suc:
                    messageQueue.put('{0} -\t Solving image for model point{1}\n'.format(timeStamp(), i + 1))
                    suc, mes, modelData = self.imagingApps.solveImage(modelData, simulation)
                    messageQueue.put('{0} -\t Image path: {1}\n'.format(timeStamp(), modelData['ImagePath']))
                    if suc:
                        if modeltype in ['Base', 'Refinement', 'All']:
                            suc = self.app.mount.addRefinementStar(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                            if suc:
                                messageQueue.put('{0} -\t Point added\n'.format(timeStamp()))
                                numCheckPoints += 1
                                results.append(copy.copy(modelData))
                                p_item.setVisible(False)
                                PyQt5.QtWidgets.QApplication.processEvents()
                            else:
                                messageQueue.put('{0} -\t Point could not be added - please check!\n'.format(timeStamp()))
                                self.logger.info('raE:{0} decE:{1} star could not be added'.format(modelData['RaError'], modelData['DecError']))
                        messageQueue.put('{0} -\t RA_diff:  {1:2.1f}    DEC_diff: {2:2.1f}\n'.format(timeStamp(), modelData['RaError'], modelData['DecError']))
                        self.logger.info('modelData: {0}'.format(modelData))
                    else:
                        messageQueue.put('{0} -\t Solving error: {1}\n'.format(timeStamp(), mes))
                messageQueue.put('status{0} of {1}'.format(i+1, len(runPoints)))
                modelBuildDone = (i + 1) / len(runPoints)
                messageQueue.put('percent{0}'.format(modelBuildDone))
                actualTime = time.time() - timeStart
                timeCalculated = actualTime / (i + 1) * (len(runPoints) - i - 1)
                mm = int(timeCalculated / 60)
                ss = int(timeCalculated - 60 * mm)
                messageQueue.put('timeleft{0:02d}:{1:02d}'.format(mm, ss))
        if not keepImages:
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        messageQueue.put('#BW{0} - {1} Model run finished. Number of modeled points: {2:3d}\n'.format(timeStamp(), modeltype, numCheckPoints))
        self.modelRun = False
        return results

    def runBaseModel(self):
        if not self.checkModelingAvailable():
            return
        if self.app.ui.checkClearModelFirst.isChecked():
            self.app.modelLogQueue.put('Clearing alignment modeling - taking 4 seconds.\n')
            self.clearAlignmentModel()
            self.app.modelLogQueue.put('Model cleared!\n')
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        if len(self.modelPoints.BasePoints) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            modelData = self.imagingApps.prepareImaging()
            domeIsConnected = self.app.workerAscomDome.isRunning
            self.modelData = self.runModel(self.app.messageQueue, 'Base', self.modelPoints.BasePoints, modelData, settlingTime, simulation, keepImages, domeIsConnected)
            self.modelData = self.app.mount.retrofitMountData(self.modelData)
            name = modelData['Directory'] + '_base.dat'
            if len(self.modelData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.analyseData.saveData(self.modelData, name)
                self.app.mount.saveBaseModel()
        else:
            self.logger.warning('There are no Basepoints for modeling')

    def runRefinementModel(self):
        if not self.checkModelingAvailable():
            return
        num = self.app.mount.numberModelStars()
        simulation = self.app.ui.checkSimulation.isChecked()
        if num > 2 or simulation:
            settlingTime = int(float(self.app.ui.settlingTime.value()))
            if len(self.modelPoints.RefinementPoints) > 0:
                if self.app.ui.checkKeepRefinement.isChecked():
                    self.app.mount.loadRefinementModel()
                else:
                    self.app.mount.loadBaseModel()
                keepImages = self.app.ui.checkKeepImages.isChecked()
                modelData = self.imagingApps.prepareImaging()
                domeIsConnected = self.app.workerAscomDome.isRunning
                refinePoints = self.runModel(self.app.messageQueue, 'Refinement', self.modelPoints.RefinementPoints, modelData, settlingTime, simulation, keepImages, domeIsConnected)
                for i in range(0, len(refinePoints)):
                    refinePoints[i]['Index'] += len(self.modelData)
                self.modelData = self.modelData + refinePoints
                self.modelData = self.app.mount.retrofitMountData(self.modelData)
                name = modelData['Directory'] + '_refinement.dat'
                if len(self.modelData) > 0:
                    self.app.ui.le_analyseFileName.setText(name)
                    self.analyseData.saveData(self.modelData, name)
                    self.app.mount.saveRefinementModel()
            else:
                self.logger.warning('There are no Refinement Points to modeling')
        else:
            self.app.messageQueue.put('Refine stopped, no BASE model available !\n')

    def runCheckModel(self):
        if not self.checkModelingAvailable():
            return
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        points = self.modelPoints.BasePoints + self.modelPoints.RefinementPoints
        if len(points) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            domeIsConnected = self.app.workerAscomDome.isRunning
            modelData = self.imagingApps.prepareImaging()
            self.modelingResultData = self.runModel(self.app.messageQueue, 'Check', points, modelData, settlingTime, simulation, keepImages, domeIsConnected)
            name = modelData['Directory'] + '_check.dat'
            if len(self.modelingResultData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.analyseData.saveData(self.modelingResultData, name)
        else:
            self.logger.warning('There are no Refinement or Base Points to modeling')

    def runAllModel(self):
        self.runBaseModel()
        self.runRefinementModel()

    def runTimeChangeModel(self):
        if not self.checkModelingAvailable():
            return
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        points = []
        for i in range(0, int(float(self.app.ui.numberRunsTimeChange.value()))):
            points.append((int(self.app.ui.azimuthTimeChange.value()), int(self.app.ui.altitudeTimeChange.value()),
                           PyQt5.QtWidgets.QGraphicsTextItem(''), True))
        simulation = self.app.ui.checkSimulation.isChecked()
        keepImages = self.app.ui.checkKeepImages.isChecked()
        domeIsConnected = self.app.workerAscomDome.isRunning
        modelData = self.imagingApps.prepareImaging()
        self.modelingResultData = self.runModel(self.app.messageQueue, 'TimeChange', points, modelData, settlingTime, simulation, keepImages, domeIsConnected)
        name = modelData['Directory'] + '_timechange.dat'
        if len(self.modelingResultData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.analyseData.saveData(self.modelingResultData, name)

    def runHystereseModel(self):
        if not self.checkModelingAvailable():
            return
        waitingTime = int(float(self.app.ui.settlingTime.value()))
        alt1 = int(float(self.app.ui.altitudeHysterese1.value()))
        alt2 = int(float(self.app.ui.altitudeHysterese2.value()))
        az1 = int(float(self.app.ui.azimuthHysterese1.value()))
        az2 = int(float(self.app.ui.azimuthHysterese2.value()))
        numberRunsHysterese = int(float(self.app.ui.numberRunsHysterese.value()))
        points = []
        for i in range(0, numberRunsHysterese):
            points.append((az1, alt1, PyQt5.QtWidgets.QGraphicsTextItem(''), True))
            points.append((az2, alt2, PyQt5.QtWidgets.QGraphicsTextItem(''), False))
        simulation = self.app.ui.checkSimulation.isChecked()
        keepImages = self.app.ui.checkKeepImages.isChecked()
        domeIsConnected = self.app.workerAscomDome.isRunning
        modelData = self.imagingApps.prepareImaging()
        self.modelingResultData = self.runModel(self.app.messageQueue, 'Hysterese', points, modelData, waitingTime, simulation, keepImages, domeIsConnected)
        name = modelData['Directory'] + '_hysterese.dat'
        self.app.ui.le_analyseFileName.setText(name)
        if len(self.modelingResultData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.analyseData.saveData(self.modelingResultData, name)

    def runBatchModel(self):
        nameDataFile = self.app.ui.le_analyseFileName.text()
        self.logger.info('modeling from {0}'.format(nameDataFile))
        data = self.app.workerModeling.analyse.loadData(nameDataFile)
        if not('RaJNow' in data and 'DecJNow' in data):
            self.logger.warning('RaJNow or DecJNow not in data file')
            self.app.modelLogQueue.put('{0} - mount coordinates missing\n'.format(timeStamp()))
            return
        if not('RaJNowSolved' in data and 'DecJNowSolved' in data):
            self.logger.warning('RaJNowSolved or DecJNowSolved not in data file')
            self.app.modelLogQueue.put('{0} - solved data missing\n'.format(timeStamp()))
            return
        if not('Pierside' in data and 'LocalSiderealTime' in data):
            self.logger.warning('Pierside and LocalSiderealTime not in data file')
            self.app.modelLogQueue.put('{0} - Time and Pierside missing\n'.format(timeStamp()))
            return
        self.app.mount.programBatchData(data)

    def runBoostModel(self):
        if not self.checkModelingAvailable():
            return
        if not self.app.ui.pd_chooseImagingApp.currentText().startswith('SGPro'):
            return
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        if len(self.app.workerModeling.modelPoints.RefinementPoints) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            domeIsConnected = self.app.workerAscomDome.isRunning
            modelData = self.imagingApps.prepareImaging()
            self.app.modeling.modelData = self.runBoost(self.app.messageQueue, self.app.workerModeling.modelPoints.RefinementPoints, modelData, settlingTime, simulation, keepImages, domeIsConnected)
            self.app.modeling.modelData = self.app.mount.retrofitMountData(self.app.modeling.modelData)
            name = modelData['Directory'] + '_boost.dat'
            if len(self.app.modeling.modelData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.app.workerModeling.analyse.saveData(self.app.modeling.modelData, name)
                self.app.mount.saveRefinementModel()
                # if not self.app.workerModeling.cancel:
                self.app.mount.programBatchData(self.modelData)
        else:
            self.logger.warning('There are no Refinement Points to modeling')

    def plateSolveSync(self, simulation=False):
        self.app.messageQueue.put('{0} - Start Sync Mount Model\n'.format(timeStamp()))
        modelData = self.imagingApps.prepareImaging()
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
        self.app.messageQueue.put('{0} -\t Capturing image\n'.format(timeStamp()))
        suc, mes, imagepath = self.imagingApps.capturingImage(modelData, simulation)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            self.app.messageQueue.put('{0} -\t Solving Image\n'.format(timeStamp()))
            suc, mes, modelData = self.imagingApps.solveImage(modelData, simulation)
            self.app.messageQueue.put('{0} -\t Image path: {1}\n'.format(timeStamp(), modelData['ImagePath']))
            if suc:
                suc = self.app.mount.syncMountModel(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                if suc:
                    self.app.messageQueue.put('{0} -\t Mount Model Synced\n'.format(timeStamp()))
                else:
                    self.app.messageQueue.put('{0} -\t Mount Model could not be synced - please check!\n'.format(timeStamp()))
            else:
                self.app.messageQueue.put('{0} -\t Solving error: {1}\n'.format(timeStamp(), mes))
        if not self.app.ui.checkKeepImages.isChecked():
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.messageQueue.put('{0} - Sync Mount Model finished !\n'.format(timeStamp()))
