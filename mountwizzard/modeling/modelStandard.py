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
from modeling.modelBase import ModelBase


class ModelStandard(ModelBase):

    def __init__(self, app):
        super(ModelStandard, self).__init__(app)
        # make main sources available
        self.app = app
        self.results = []
        self.modelRun = False

    def runBaseModel(self):
        if self.app.ui.checkClearModelFirst.isChecked():
            self.app.modelLogQueue.put('Clearing alignment modeling - taking 4 seconds.\n')
            self.clearAlignmentModel()
            self.app.modelLogQueue.put('Model cleared!\n')
        settlingTime, directory = self.setupRunningParameters()
        if len(self.app.workerModeling.modelPoints.BasePoints) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            self.app.modeling.modelData = self.runModel('Base', self.app.workerModeling.modelPoints.BasePoints, directory, settlingTime, simulation, keepImages)
            self.app.modeling.modelData = self.app.mount.retrofitMountData(self.app.modeling.modelData)
            name = directory + '_base.dat'
            if len(self.app.modeling.modelData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.app.workerModeling.analyse.saveData(self.app.modeling.modelData, name)
                self.app.mount.saveBaseModel()
        else:
            self.logger.warning('There are no Basepoints for modeling')

    def runRefinementModel(self):
        num = self.app.mount.numberModelStars()
        simulation = self.app.ui.checkSimulation.isChecked()
        if num > 2 or simulation:
            settlingTime, directory = self.setupRunningParameters()
            if len(self.app.workerModeling.modelPoints.RefinementPoints) > 0:
                if self.app.ui.checkKeepRefinement.isChecked():
                    self.app.mount.loadRefinementModel()
                else:
                    self.app.mount.loadBaseModel()
                keepImages = self.app.ui.checkKeepImages.isChecked()
                refinePoints = self.runModel('Refinement', self.app.workerModeling.modelPoints.RefinementPoints, directory, settlingTime, simulation, keepImages)
                for i in range(0, len(refinePoints)):
                    refinePoints[i]['Index'] += len(self.app.modeling.modelData)
                self.app.modeling.modelData = self.app.modeling.modelData + refinePoints
                self.app.modeling.modelData = self.app.mount.retrofitMountData(self.app.modeling.modelData)
                name = directory + '_refinement.dat'
                if len(self.app.modeling.modelData) > 0:
                    self.app.ui.le_analyseFileName.setText(name)
                    self.app.workerModeling.analyse.saveData(self.app.modeling.modelData, name)
                    self.app.mount.saveRefinementModel()
            else:
                self.logger.warning('There are no Refinement Points to modeling')
        else:
            self.app.modelLogQueue.put('Refine stopped, no BASE model available !\n')
            self.app.messageQueue.put('Refine stopped, no BASE model available !\n')

    def runCheckModel(self):
        settlingTime, directory = self.setupRunningParameters()
        points = self.app.workerModeling.modelPoints.BasePoints + self.app.workerModeling.modelPoints.RefinementPoints
        if len(points) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            self.app.workerModeling.modelAnalyseData = self.runModel('Check', points, directory, settlingTime, simulation, keepImages)
            name = directory + '_check.dat'
            if len(self.app.workerModeling.modelAnalyseData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.app.workerModeling.analyse.saveData(self.app.workerModeling.modelAnalyseData, name)
        else:
            self.logger.warning('There are no Refinement or Base Points to modeling')

    def runAllModel(self):
        self.runBaseModel()
        self.runRefinementModel()

    def runTimeChangeModel(self):
        settlingTime, directory = self.setupRunningParameters()
        points = []
        for i in range(0, int(float(self.app.ui.numberRunsTimeChange.value()))):
            points.append((int(self.app.ui.azimuthTimeChange.value()), int(self.app.ui.altitudeTimeChange.value()),
                           PyQt5.QtWidgets.QGraphicsTextItem(''), True))
        simulation = self.app.ui.checkSimulation.isChecked()
        keepImages = self.app.ui.checkKeepImages.isChecked()
        self.app.workerModeling.modelAnalyseData = self.runModel('TimeChange', points, directory, settlingTime, simulation, keepImages)
        name = directory + '_timechange.dat'
        if len(self.app.workerModeling.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.app.workerModeling.analyse.saveData(self.app.workerModeling.modelAnalyseData, name)

    def runHystereseModel(self):
        waitingTime, directory = self.setupRunningParameters()
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
        self.app.workerModeling.modelAnalyseData = self.runModel('Hysterese', points, directory, waitingTime, simulation, keepImages)
        name = directory + '_hysterese.dat'
        self.app.ui.le_analyseFileName.setText(name)
        if len(self.app.workerModeling.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.app.workerModeling.analyse.saveData(self.app.workerModeling.modelAnalyseData, name)

    # noinspection PyUnresolvedReferences
    def runModel(self, modeltype, runPoints, directory, settlingTime, simulation=False, keepImages=False):
        # start clearing the data
        modelData = {}
        results = []
        # preparing the gui outputs
        self.app.modelLogQueue.put('status-- of --')
        self.app.modelLogQueue.put('percent0')
        self.app.modelLogQueue.put('timeleft--:--')
        self.app.modelLogQueue.put('delete')
        self.app.modelLogQueue.put('#BW{0} - Start {1} Model\n'.format(self.timeStamp(), modeltype))
        modelData = self.prepareImaging(modelData, directory)
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
            self.app.workerModeling.modelRun = True
            modelData['Azimuth'] = p_az
            modelData['Altitude'] = p_alt
            if p_item.isVisible():
                # todo: put the code to multi thread modeling
                if self.app.workerModeling.cancel:
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
                modelData['File'] = self.app.workerModeling.CAPTUREFILE + '{0:03d}'.format(i) + '.fit'
                modelData['LocalSiderealTime'] = self.app.mount.data['LocalSiderealTime']
                modelData['LocalSiderealTimeFloat'] = self.app.workerModeling.transform.degStringToDecimal(self.app.mount.data['LocalSiderealTime'][0:9])
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
                self.app.modelLogQueue.put('{0} -\t Capturing image for model point {1:2d}\n'.format(self.timeStamp(), i + 1))
                suc, mes, imagepath = self.capturingImage(modelData, simulation)
                if modeltype in ['TimeChange']:
                    self.app.mountCommandQueue.put('RT9')
                self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
                if suc:
                    self.app.modelLogQueue.put('{0} -\t Solving image for model point{1}\n'.format(self.timeStamp(), i + 1))
                    suc, mes, modelData = self.solveImage(modelData, simulation)
                    self.app.modelLogQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['ImagePath']))
                    if suc:
                        if modeltype in ['Base', 'Refinement', 'All']:
                            suc = self.app.mount.addRefinementStar(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                            if suc:
                                self.app.modelLogQueue.put('{0} -\t Point added\n'.format(self.timeStamp()))
                                numCheckPoints += 1
                                results.append(copy.copy(modelData))
                                p_item.setVisible(False)
                                PyQt5.QtWidgets.QApplication.processEvents()
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
        self.app.workerModeling.modelRun = False
        return results
