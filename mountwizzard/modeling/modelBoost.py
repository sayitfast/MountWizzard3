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
import shutil
import time
import PyQt5
from queue import Queue
from modeling.modelBase import ModelBase


class Slewpoint(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queuePoint = Queue()
    signalSlewing = PyQt5.QtCore.pyqtSignal(name='slew')

    def __init__(self, main):
        PyQt5.QtCore.QThread.__init__(self)
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
                self.main.app.modelLogQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec'.format(self.main.timeStamp(), modelData['SettlingTime']))
                timeCounter = modelData['SettlingTime']
                while timeCounter > 0:
                    time.sleep(1)
                    timeCounter -= 1
                    self.main.app.modelLogQueue.put('backspace')
                    self.main.app.modelLogQueue.put('{0:02d} sec'.format(timeCounter))
                self.main.app.modelLogQueue.put('\n')
            self.main.workerImage.queueImage.put(modelData)


class Image(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queueImage = Queue()
    signalImaging = PyQt5.QtCore.pyqtSignal(name='image')

    def __init__(self, main):
        PyQt5.QtCore.QThread.__init__(self)
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
                suc, mes, imagepath = self.main.capturingImage(modelData, modelData['Simulation'])
                self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
                modelData['ImagingSuccess'] = suc
                self.main.workerSlewpoint.signalSlewing.emit()
                self.main.workerPlatesolve.queuePlatesolve.put(modelData)

    @PyQt5.QtCore.pyqtSlot()
    def stop(self):
        self.isRunning = False


class Platesolve(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queuePlatesolve = Queue()
    signalPlatesolveFinished = PyQt5.QtCore.pyqtSignal(name='platesolveFinished')

    def __init__(self, main):
        PyQt5.QtCore.QThread.__init__(self)
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
                self.main.solvedPointsQueue.put(modelData)
                self.main.app.modelLogQueue.put('status{0} of {1}'.format(modelData['Index'] + 1, self.main.numberPointsMax))

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
        self.workerSlewpoint.signalSlewing.emit()
        while self.app.modeling.modelRun:
            PyQt5.QtWidgets.QApplication.processEvents()
            # stop loop if cancelled
            if self.app.modeling.cancel:
                break
            # stop loop if finished
            if not self.app.modeling.modelRun:
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
        self.numberSolvedPoints = 0
        while not self.solvedPointsQueue.empty():
            results.append(self.solvedPointsQueue.get())
            self.numberSolvedPoints += 1
        if not keepImages:
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.modelLogQueue.put('#BW{0} - Boost Model run finished. Number of modeled points: {1:3d}\n\n'.format(self.timeStamp(), self.numberSolvedPoints))
        return results
