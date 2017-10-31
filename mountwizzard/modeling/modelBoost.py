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
import os
import shutil
import time
import PyQt5
from queue import Queue
from modeling.modelBase import ModelBase


class Slewpoint(PyQt5.QtCore.QObject):

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
            number = self.queuePoint.get()
            time.sleep(0.1)
            print('Start Slewing to Point {0}'.format(number))
            time.sleep(5)
            print('Settling of point {0}'.format(number))
            time.sleep(0.5)
            print('Tracking of point {0}'.format(number))
            self.main.workerImage.queueImage.put(number)


class Image(PyQt5.QtCore.QObject):

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
                number = self.queueImage.get()
                time.sleep(0.5)
                print('Start Integration of point {0}'.format(number))
                time.sleep(5)
                print('Download of point {0}'.format(number))
                self.main.workerSlewpoint.signalSlewing.emit()
                time.sleep(2)
                print('Store Image of point {0}'.format(number))
                time.sleep(0.2)
                self.main.workerPlatesolve.queuePlatesolve.put(number)

    @PyQt5.QtCore.pyqtSlot()
    def stop(self):
        self.isRunning = False


class Platesolve(PyQt5.QtCore.QObject):

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
                number = self.queuePlatesolve.get()
                print('Start Platesolve of point {0}'.format(number))
                time.sleep(5)
                print('Got coordinates of point {0}'.format(number))
                time.sleep(0.1)

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
        self.modelRun = False
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
            refinePoints = self.runBoost(self.app.modeling.modelPoints.RefinementPoints, directory, settlingTime, simulation, keepImages)
            for i in range(0, len(refinePoints)):
                refinePoints[i]['index'] += len(self.modelData)
            self.modelData = refinePoints
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
        # loading test data
        for i in range(1, 10):
            self.workerSlewpoint.queuePoint.put(i)
        # start process
        self.workerSlewpoint.signalSlewing.emit()
        while self.app.modeling.modelRun:
            PyQt5.QtWidgets.QApplication.processEvents()
            if self.app.modeling.cancel:
                break
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

        return results
        # counter and timer for performance estimation
        numCheckPoints = 0
        timeStart = time.time()

        # here starts the real model running cycle
        for i, (p_az, p_alt, p_item, p_solve) in enumerate(runPoints):
            self.app.modeling.modelRun = True
            modelData['Azimuth'] = p_az
            modelData['Altitude'] = p_alt
            if p_item.isVisible():
                # todo: put the code to multi thread modeling
                if self.app.modeling.cancel:
                    self.app.modeling.cancel = False
                    self.app.modelLogQueue.put('#BW{0} -\t {1} Model canceled !\n'.format(self.timeStamp(), modeltype))
                    # tracking should be on after canceling the modeling
                    self.app.mountCommandQueue.put('AP')
                    # clearing the gui
                    self.app.modelLogQueue.put('status-- of --')
                    self.app.modelLogQueue.put('percent0')
                    self.app.modelLogQueue.put('timeleft--:--')
                    self.logger.info('Modeling cancelled in main loop')
                    # finally stopping modeling run
                    break
                self.app.modelLogQueue.put('#BG{0} - Slewing to point {1:2d}  @ Az: {2:3.0f}\xb0 Alt: {3:2.0f}\xb0\n'.format(self.timeStamp(), i+1, p_az, p_alt))
                self.logger.info('point {0:2d}  Az: {1:3.0f} Alt: {2:2.0f}'.format(i+1, p_az, p_alt))
                if modeltype in ['TimeChange']:
                    # in time change there is only slew for the first time, than only track during imaging
                    if i == 0:
                        self.slewMountDome(p_az, p_alt)
                        self.app.mountCommandQueue.put('RT9')
                else:
                    self.slewMountDome(p_az, p_alt)
                self.app.modelLogQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec'.format(self.timeStamp(), settlingTime))
                timeCounter = settlingTime
                while timeCounter > 0:
                    time.sleep(1)
                    timeCounter -= 1
                    self.app.modelLogQueue.put('backspace')
                    self.app.modelLogQueue.put('{0:02d} sec'.format(timeCounter))
                self.app.modelLogQueue.put('\n')
            if p_item.isVisible() and p_solve:
                modelData['File'] = self.app.modeling.CAPTUREFILE + '{0:03d}'.format(i) + '.fit'
                modelData['LocalSiderealTime'] = self.app.mount.data['LocalSiderealTime']
                modelData['LocalSiderealTimeFloat'] = self.app.modeling.transform.degStringToDecimal(self.app.mount.data['LocalSiderealTime'][0:9])
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
                self.app.modelLogQueue.put('{0} -\t Capturing image for modeling point {1:2d}\n'.format(self.timeStamp(), i + 1))
                suc, mes, imagepath = self.capturingImage(modelData, simulation)
                if modeltype in ['TimeChange']:
                    self.app.mountCommandQueue.put('RT9')
                self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
                if suc:
                    self.app.modelLogQueue.put('{0} -\t Solving Image\n'.format(self.timeStamp()))
                    suc, mes, modelData = self.solveImage(modelData, simulation)
                    self.app.modelLogQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['ImagePath']))
                    if suc:
                        if modeltype in ['Base', 'Refinement', 'All']:
                            suc = self.addRefinementStar(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                            if suc:
                                self.app.modelLogQueue.put('{0} -\t Point added\n'.format(self.timeStamp()))
                                numCheckPoints += 1
                                results.append(copy.copy(modelData))
                                p_item.setVisible(False)
                            else:
                                self.app.modelLogQueue.put('{0} -\t Point could not be added - please check!\n'.format(self.timeStamp()))
                                self.logger.info('raE:{0} decE:{1} star could not be added'.format(modelData['RaError'], modelData['DecError']))
                        self.app.modelLogQueue.put('{0} -\t RA_diff:  {1:2.1f}    DEC_diff: {2:2.1f}\n'.format(self.timeStamp(), modelData['RaError'], modelData['DecError']))
                        self.logger.info('modelData: {0}'.format(modelData))
                    else:
                        self.app.modelLogQueue.put('{0} -\t Solving error: {1}\n'.format(self.timeStamp(), mes))
                self.app.modelLogQueue.put('status{0} of {1}'.format(i+1, len(runPoints)))
                modelBuildDone = (i + 1) / len(runPoints)
                self.app.modelLogQueue.put('percent{0}'.format(modelBuildDone))
                actualTime = time.time() - timeStart
                timeCalculated = actualTime / (i + 1) * (len(runPoints) - i - 1)
                mm = int(timeCalculated / 60)
                ss = int(timeCalculated - 60 * mm)
                self.app.modelLogQueue.put('timeleft{0:02d}:{1:02d}'.format(mm, ss))
        if not keepImages:
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.modelLogQueue.put('#BW{0} - {1} Model run finished. Number of modeled points: {2:3d}\n\n'.format(self.timeStamp(), modeltype, numCheckPoints))
        self.app.modeling.modelRun = False
        return results
