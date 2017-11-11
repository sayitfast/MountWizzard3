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
import time
# threading
import threading
import PyQt5
# for data storing
from analyse.analysedata import Analyse
# cameras
from camera import none
from camera import indicamera
if platform.system() == 'Windows':
    from camera import maximdl
    from camera import sgpro
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    from camera import theskyx
# modelPoints
from modeling import modelPoints
# workers
from modeling import modelStandard
from modeling import modelBoost


class Modeling(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    signalModelConnected = PyQt5.QtCore.pyqtSignal(int, name='ModelConnected')
    signalModelRedraw = PyQt5.QtCore.pyqtSignal(bool, name='ModelRedrawPoints')

    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red;'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'
    REF_PICTURE = '/model001.fit'
    IMAGEDIR = os.getcwd().replace('\\', '/') + '/images'
    CAPTUREFILE = 'modeling'

    CYCLESTATUSFAST = 1000

    def __init__(self, app):
        super().__init__()
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()

        # make main sources available
        self.app = app
        # make windows imaging applications available
        if platform.system() == 'Windows':
            self.SGPro = sgpro.SGPro(self.app)
            self.MaximDL = maximdl.MaximDLCamera(self.app)
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.TheSkyX = theskyx.TheSkyX(self.app)
        # make non windows applications available
        self.NoneCam = none.NoneCamera(self.app)
        self.INDICamera = indicamera.INDICamera(self.app)
        # select default application
        self.imagingHandler = self.NoneCam
        # assign support classes
        self.analyse = Analyse(self.app)
        self.transform = self.app.mount.transform
        self.modelPoints = modelPoints.ModelPoints(self.app, self.transform)
        self.modelStandard = modelStandard.ModelStandard(self.app)
        self.modelBoost = modelBoost.ModelBoost(self.app)

        self.chooserLock = threading.Lock()
        # finally initialize the class configuration
        self.cancel = False
        self.modelRun = False
        self.modelAnalyseData = []
        self.modelData = {}

        self.commandDispatch = {
            'RunBaseModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runBaseModel,
                            'Method': self.modelStandard.runBaseModel,
                            'Cancel': self.app.ui.btn_cancelModel1
                        }
                    ]
                },
            'RunRefinementModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runRefinementModel,
                            'Method': self.modelStandard.runRefinementModel,
                            'Cancel': self.app.ui.btn_cancelModel2
                        }
                    ]
                },
            'RunBoostModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runBoostModel,
                            'Method': self.modelBoost.runModel,
                            'Cancel': self.app.ui.btn_cancelModel2
                        }
                    ]
                },
            'PlateSolveSync':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_plateSolveSync,
                            'Method': self.modelStandard.plateSolveSync,
                            'Parameter': ['self.app.ui.checkSimulation.isChecked()'],
                        }
                    ]
                },
            'RunBatchModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runBatchModel,
                            'Method': self.modelStandard.runBatchModel,
                            'Cancel': self.app.ui.btn_cancelModel2
                        }
                    ]
                },
            'RunCheckModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runCheckModel,
                            'Method': self.modelStandard.runCheckModel,
                            'Cancel': self.app.ui.btn_cancelModel2
                        }
                    ]
                },
            'RunTimeChangeModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runTimeChangeModel,
                            'Method': self.modelStandard.runTimeChangeModel,
                            'Cancel': self.app.ui.btn_cancelAnalyseModel
                        }
                    ]
                },
            'RunHystereseModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runHystereseModel,
                            'Method': self.modelStandard.runHystereseModel,
                            'Cancel': self.app.ui.btn_cancelAnalyseModel
                        }
                    ]
                },
            'ClearAlignmentModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_clearAlignmentModel,
                            'Method': self.modelStandard.clearAlignmentModel,
                            'Cancel': self.app.ui.btn_cancelAnalyseModel
                        }
                    ]
                },
            'GenerateDSOPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateDSOPoints,
                            'Method': self.modelPoints.generateDSOPoints,
                            'Parameter': ['self.app.ui.checkSortPoints.isChecked()',
                                          'int(float(self.app.ui.numberHoursDSO.value()))',
                                          'int(float(self.app.ui.numberPointsDSO.value()))',
                                          'int(float(self.app.ui.numberHoursPreview.value()))'
                                          ]
                        }
                    ]
                },
            'GenerateDensePoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateDensePoints,
                            'Method': self.modelPoints.generateDensePoints,
                            'Parameter': ['self.app.ui.checkSortPoints.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()'
                                          ]
                        }
                    ]
                },
            'GenerateNormalPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateNormalPoints,
                            'Method': self.modelPoints.generateNormalPoints,
                            'Parameter': ['self.app.ui.checkSortPoints.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()'
                                          ]
                        }
                    ]
                },
            'LoadBasePoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadBasePoints,
                            'Method': self.modelPoints.loadBasePoints,
                            'Parameter': ['self.app.ui.le_modelPointsFileName.text()']
                        }
                    ]
                },
            'LoadRefinementPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateNormalPoints,
                            'Method': self.modelPoints.loadRefinementPoints,
                            'Parameter': ['self.app.ui.le_modelPointsFileName.text()',
                                          'self.app.ui.checkSortPoints.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()']
                        }
                    ]
                },
            'GenerateGridPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateGridPoints,
                            'Method': self.modelPoints.generateGridPoints,
                            'Parameter': ['self.app.ui.checkSortPoints.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()',
                                          'int(float(self.app.ui.numberGridPointsRow.value()))',
                                          'int(float(self.app.ui.numberGridPointsCol.value()))',
                                          'int(float(self.app.ui.altitudeMin.value()))',
                                          'int(float(self.app.ui.altitudeMax.value()))']
                        }
                    ]
                },
            'GenerateBasePoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateBasePoints,
                            'Method': self.modelPoints.generateBasePoints,
                            'Parameter': ['float(self.app.ui.azimuthBase.value())',
                                          'float(self.app.ui.altitudeBase.value())']
                        }
                    ]
                },
            'DeletePoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_deletePoints,
                            'Method': self.modelPoints.deletePoints
                        }
                    ]
                }
            }
        # setting the config up
        self.initConfig()
        # run it first, to set all imaging applications up
        self.chooseImaging()

    def initConfig(self):
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
        try:
            if 'ImagingApplication' in self.app.config:
                self.app.ui.pd_chooseImaging.setCurrentIndex(int(self.app.config['ImagingApplication']))
            if 'CheckSortPoints' in self.app.config:
                self.app.ui.checkSortPoints.setChecked(self.app.config['CheckSortPoints'])
            if 'CheckDeletePointsHorizonMask' in self.app.config:
                self.app.ui.checkDeletePointsHorizonMask.setChecked(self.app.config['CheckDeletePointsHorizonMask'])
            if 'CheckSimulation' in self.app.config:
                self.app.ui.checkSimulation.setChecked(self.app.config['CheckSimulation'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        # connect change in imaging app to the subroutine of setting it up
        self.app.ui.pd_chooseImaging.currentIndexChanged.connect(self.chooseImaging)

    def storeConfig(self):
        self.app.config['ImagingApplication'] = self.app.ui.pd_chooseImaging.currentIndex()
        self.app.config['CheckSortPoints'] = self.app.ui.checkSortPoints.isChecked()
        self.app.config['CheckDeletePointsHorizonMask'] = self.app.ui.checkDeletePointsHorizonMask.isChecked()
        self.app.config['CheckSimulation'] = self.app.ui.checkSimulation.isChecked()

    def chooseImaging(self):
        self.chooserLock.acquire()
        self.app.ui.btn_runBoostModel.setVisible(False)
        self.app.ui.btn_runBoostModel.setEnabled(False)
        if self.imagingHandler.cameraConnected:
            self.imagingHandler.disconnectCamera()
        if self.app.ui.pd_chooseImaging.currentText().startswith('No Application'):
            self.imagingHandler = self.NoneCam
            self.logger.info('actual camera / plate solver is None')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('INDI Camera'):
            self.imagingHandler = self.INDICamera
            self.logger.info('actual camera / plate solver is INDI Camera')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('SGPro'):
            self.imagingHandler = self.SGPro
            self.app.ui.btn_runBoostModel.setEnabled(True)
            self.app.ui.btn_runBoostModel.setVisible(True)
            self.logger.info('actual camera / plate solver is SGPro')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('TheSkyX'):
            self.imagingHandler = self.TheSkyX
            self.logger.info('actual camera / plate solver is TheSkyX')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('MaximDL'):
            self.imagingHandler = self.MaximDL
            self.logger.info('actual camera / plate solver is MaximDL')
        self.imagingHandler.checkAppStatus()
        self.imagingHandler.connectCamera()
        self.chooserLock.release()

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.app.ui.btn_plateSolveSync.clicked.connect(lambda: self.commandDispatcher('PlateSolveSync'))
        self.app.ui.btn_deletePoints.clicked.connect(lambda: self.commandDispatcher('DeletePoints'))
        self.app.ui.btn_loadRefinementPoints.clicked.connect(lambda: self.commandDispatcher('LoadRefinementPoints'))
        self.app.ui.btn_loadBasePoints.clicked.connect(lambda: self.commandDispatcher('LoadBasePoints'))
        self.app.ui.btn_generateDSOPoints.clicked.connect(lambda: self.commandDispatcher('GenerateDSOPoints'))
        self.app.ui.numberHoursDSO.valueChanged.connect(lambda: self.commandDispatcher('GenerateDSOPoints'))
        self.app.ui.numberPointsDSO.valueChanged.connect(lambda: self.commandDispatcher('GenerateDSOPoints'))
        self.app.ui.numberHoursPreview.valueChanged.connect(lambda: self.commandDispatcher('GenerateDSOPoints'))
        self.app.ui.btn_generateDensePoints.clicked.connect(lambda: self.commandDispatcher('GenerateDensePoints'))
        self.app.ui.btn_generateNormalPoints.clicked.connect(lambda: self.commandDispatcher('GenerateNormalPoints'))
        self.app.ui.btn_generateGridPoints.clicked.connect(lambda: self.commandDispatcher('GenerateGridPoints'))
        self.app.ui.numberGridPointsRow.valueChanged.connect(lambda: self.commandDispatcher('GenerateGridPoints'))
        self.app.ui.numberGridPointsCol.valueChanged.connect(lambda: self.commandDispatcher('GenerateGridPoints'))
        self.app.ui.altitudeMin.valueChanged.connect(lambda: self.commandDispatcher('GenerateGridPoints'))
        self.app.ui.altitudeMax.valueChanged.connect(lambda: self.commandDispatcher('GenerateGridPoints'))
        self.app.ui.btn_generateBasePoints.clicked.connect(lambda: self.commandDispatcher('GenerateBasePoints'))
        self.app.ui.btn_runCheckModel.clicked.connect(lambda: self.commandDispatcher('RunCheckModel'))
        self.app.ui.btn_runTimeChangeModel.clicked.connect(lambda: self.commandDispatcher('RunTimeChangeModel'))
        self.app.ui.btn_runHystereseModel.clicked.connect(lambda: self.commandDispatcher('RunHystereseModel'))
        self.app.ui.btn_runCheckModel.clicked.connect(lambda: self.commandDispatcher('RunCheckModel'))
        self.app.ui.btn_runRefinementModel.clicked.connect(lambda: self.commandDispatcher('RunRefinementModel'))
        self.app.ui.btn_runBoostModel.clicked.connect(lambda: self.commandDispatcher('RunBoostModel'))
        self.app.ui.btn_runBatchModel.clicked.connect(lambda: self.commandDispatcher('RunBatchModel'))
        self.app.ui.btn_clearAlignmentModel.clicked.connect(lambda: self.commandDispatcher('ClearAlignmentModel'))
        self.app.ui.btn_runBaseModel.clicked.connect(lambda: self.commandDispatcher('RunBaseModel'))
        self.signalModelConnected.emit(3)
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.getStatusFast()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.finished.emit()

    def commandDispatcher(self, command):
        # if we have a command in dispatcher
        if command in self.commandDispatch:
            # running through all necessary commands
            for work in self.commandDispatch[command]['Worker']:
                # if we want to color a button, which one
                if 'Button' in work:
                    work['Button'].setStyleSheet(self.BLUE)
                PyQt5.QtWidgets.QApplication.processEvents()
                if 'Parameter' in work:
                    parameter = []
                    for p in work['Parameter']:
                        parameter.append(eval(p))
                    work['Method'](*parameter)
                else:
                    work['Method']()
                time.sleep(1)
                if 'Button' in work:
                    work['Button'].setStyleSheet(self.DEFAULT)
                if 'Cancel' in work:
                    work['Cancel'].setStyleSheet(self.DEFAULT)
                self.signalModelRedraw.emit(True)
                PyQt5.QtWidgets.QApplication.processEvents()

    def cancelModeling(self):
        if self.modelRun:
            self.app.ui.btn_cancelModel.setStyleSheet(self.RED)
            self.logger.info('User canceled modeling with cancel any model run')
            self.cancel = True

    def cancelAnalyseModeling(self):
        if self.modelRun:
            self.app.ui.btn_cancelAnalyseModel.setStyleSheet(self.RED)
            self.logger.info('User canceled modeling with cancel analyse run')
            self.cancel = True

    def getStatusFast(self):
        self.imagingHandler.checkAppStatus()
        self.imagingHandler.getCameraStatus()
        self.signalModelConnected.emit(1)
        if self.imagingHandler.appRunning:
            self.signalModelConnected.emit(2)
        if self.imagingHandler.cameraConnected:
            self.signalModelConnected.emit(3)
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUSFAST, self.getStatusFast)
            PyQt5.QtWidgets.QApplication.processEvents()
