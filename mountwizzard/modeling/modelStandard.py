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
            modelData = self.app.workerModeling.imagingApps.prepareImaging(directory)
            self.app.workerModeling.modelData = self.runModel('Base', self.app.workerModeling.modelPoints.BasePoints, modelData, settlingTime, simulation, keepImages)
            self.app.workerModeling.modelData = self.app.mount.retrofitMountData(self.app.workerModeling.modelData)
            name = directory + '_base.dat'
            if len(self.app.workerModeling.modelData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.app.workerModeling.analyse.saveData(self.app.workerModeling.modelData, name)
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
                modelData = self.app.workerModeling.imagingApps.prepareImaging(directory)
                refinePoints = self.runModel('Refinement', self.app.workerModeling.modelPoints.RefinementPoints, modelData, settlingTime, simulation, keepImages)
                for i in range(0, len(refinePoints)):
                    refinePoints[i]['Index'] += len(self.app.workerModeling.modelData)
                self.app.workerModeling.modelData = self.app.workerModeling.modelData + refinePoints
                self.app.workerModeling.modelData = self.app.mount.retrofitMountData(self.app.workerModeling.modelData)
                name = directory + '_refinement.dat'
                if len(self.app.workerModeling.modelData) > 0:
                    self.app.ui.le_analyseFileName.setText(name)
                    self.app.workerModeling.analyse.saveData(self.app.workerModeling.modelData, name)
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
            modelData = self.app.workerModeling.imagingApps.prepareImaging(directory)
            self.app.workerModeling.modelAnalyseData = self.runModel('Check', points, modelData, settlingTime, simulation, keepImages)
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
        modelData = self.app.workerModeling.imagingApps.prepareImaging(directory)
        self.app.workerModeling.modelAnalyseData = self.runModel('TimeChange', points, modelData, settlingTime, simulation, keepImages)
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
        modelData = self.app.workerModeling.imagingApps.prepareImaging(directory)
        self.app.workerModeling.modelAnalyseData = self.runModel('Hysterese', points, modelData, waitingTime, simulation, keepImages)
        name = directory + '_hysterese.dat'
        self.app.ui.le_analyseFileName.setText(name)
        if len(self.app.workerModeling.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.app.workerModeling.analyse.saveData(self.app.workerModeling.modelAnalyseData, name)
