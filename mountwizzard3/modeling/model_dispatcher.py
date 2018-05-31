############################################################
# -*- coding: utf-8 -*-
#
#       #   #  #   #   #  ####
#      ##  ##  #  ##  #     #
#     # # # #  # # # #     ###
#    #  ##  #  ##  ##        #
#   #   #   #  #   #     ####
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.6.4
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import time
import PyQt5
import queue
from modeling import model_build


class ModelingDispatcher(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalModelPointsRedraw = PyQt5.QtCore.pyqtSignal()
    signalCancel = PyQt5.QtCore.pyqtSignal()

    CYCLE = 200
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        # make main sources available
        self.app = app
        self.thread = thread
        self.cycleTimer = None
        self.commandDispatcherQueue = queue.Queue()
        self.modelingRunner = model_build.ModelingBuild(self.app)
        # signal for stopping modeling
        self.signalCancel.connect(self.modelingRunner.setCancel)

        # definitions for the command dispatcher. this enables spawning commands from outside into the current thread for running
        self.commandDispatch = {
            'RunInitialModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runInitialModel,
                            'Method': self.modelingRunner.runInitialModel,
                            'Cancel': self.app.ui.btn_cancelInitialModel
                        }
                    ]
                },
            'RunFullModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runFullModel,
                            'Method': self.modelingRunner.runFullModel,
                            'Cancel': self.app.ui.btn_cancelFullModel
                        }
                    ]
                },
            'PlateSolveSync':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_plateSolveSync,
                            'Method': self.modelingRunner.plateSolveSync
                        }
                    ]
                },
            'RunTimeChangeModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runTimeChangeModel,
                            'Method': self.modelingRunner.runTimeChangeModel,
                            'Cancel': self.app.ui.btn_cancelAnalyseModel
                        }
                    ]
                },
            'RunHystereseModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runHystereseModel,
                            'Method': self.modelingRunner.runHystereseModel,
                            'Cancel': self.app.ui.btn_cancelAnalyseModel
                        }
                    ]
                },
            'GenerateDSOPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateDSOPoints,
                            'Method': self.modelingRunner.modelPoints.generateDSOPoints,
                            'Parameter': ['self.app.ui.checkSortPoints.isChecked()',
                                          'int(self.app.ui.numberHoursDSO.value())',
                                          'int(self.app.ui.numberPointsDSO.value())',
                                          'int(self.app.ui.numberHoursPreview.value())'
                                          ]
                        }
                    ]
                },
            'GenerateMaxPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateMaxPoints,
                            'Method': self.modelingRunner.modelPoints.generateMaxPoints,
                            'Parameter': ['self.app.ui.checkDeletePointsHorizonMask.isChecked()',
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
                            'Method': self.modelingRunner.modelPoints.generateNormalPoints,
                            'Parameter': ['self.app.ui.checkDeletePointsHorizonMask.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()'
                                          ]
                        }
                    ]
                },
            'GenerateMinPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateMinPoints,
                            'Method': self.modelingRunner.modelPoints.generateMinPoints,
                            'Parameter': ['self.app.ui.checkDeletePointsHorizonMask.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()'
                                          ]
                        }
                    ]
                },
            'ShowInitialPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_showFullModelPoints,
                            'Method': self.modelingRunner.modelPoints.showInitialPoints,
                            'Parameter': ['self.app.ui.le_modelInitialPointsFileName.text()']
                        }
                    ]
                },
            'ShowFullPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_showFullModelPoints,
                            'Method': self.modelingRunner.modelPoints.showFullPoints,
                            'Parameter': ['self.app.ui.le_modelFullPointsFileName.text()',
                                          'self.app.ui.checkDeletePointsHorizonMask.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()']
                        }
                    ]
                },
            'GenerateGridPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateGridPoints,
                            'Method': self.modelingRunner.modelPoints.generateGridPoints,
                            'Parameter': ['self.app.ui.checkDeletePointsHorizonMask.isChecked()',
                                          'self.app.ui.checkSortPoints.isChecked()',
                                          'int(self.app.ui.numberGridPointsRow.value())',
                                          'int(self.app.ui.numberGridPointsCol.value())',
                                          'int(self.app.ui.altitudeMin.value())',
                                          'int(self.app.ui.altitudeMax.value())']
                        }
                    ]
                },
            'GenerateInitialPoints':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_generateInitialPoints,
                            'Method': self.modelingRunner.modelPoints.generateInitialPoints,
                            'Parameter': ['float(self.app.ui.azimuthBase.value())',
                                          'float(self.app.ui.altitudeBase.value())',
                                          'int(self.app.ui.numberBase.value())']
                        }
                    ]
                },
            'DeletePoints':
                {
                    'Worker': [
                        {
                            'Method': self.modelingRunner.modelPoints.deletePoints
                        }
                    ]
                }
            }
        # signal slot
        self.app.ui.btn_plateSolveSync.clicked.connect(lambda: self.commandDispatcherQueue.put('PlateSolveSync'))
        self.app.ui.btn_showFullModelPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('ShowFullPoints'))
        self.app.ui.btn_showInitialModelPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('ShowInitialPoints'))
        self.app.ui.btn_generateDSOPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('GenerateDSOPoints'))
        self.app.ui.numberHoursDSO.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateDSOPoints'))
        self.app.ui.numberPointsDSO.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateDSOPoints'))
        self.app.ui.numberHoursPreview.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateDSOPoints'))
        self.app.ui.btn_generateMaxPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('GenerateMaxPoints'))
        self.app.ui.btn_generateNormalPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('GenerateNormalPoints'))
        self.app.ui.btn_generateMinPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('GenerateMinPoints'))
        self.app.ui.btn_generateGridPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.numberGridPointsRow.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.numberGridPointsCol.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.altitudeMin.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.altitudeMax.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.btn_generateInitialPoints.clicked.connect(lambda: self.commandDispatcherQueue.put('GenerateInitialPoints'))
        self.app.ui.altitudeBase.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateInitialPoints'))
        self.app.ui.azimuthBase.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateInitialPoints'))
        self.app.ui.numberBase.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateInitialPoints'))
        self.app.ui.btn_runTimeChangeModel.clicked.connect(lambda: self.commandDispatcherQueue.put('RunTimeChangeModel'))
        self.app.ui.btn_runHystereseModel.clicked.connect(lambda: self.commandDispatcherQueue.put('RunHystereseModel'))
        self.app.ui.btn_runFullModel.clicked.connect(lambda: self.commandDispatcherQueue.put('RunFullModel'))
        self.app.ui.btn_runInitialModel.clicked.connect(lambda: self.commandDispatcherQueue.put('RunInitialModel'))

    def initConfig(self):
        # before changing value through config (which fires the signals) i have to disable them
        self.app.ui.numberHoursDSO.valueChanged.disconnect()
        self.app.ui.numberPointsDSO.valueChanged.disconnect()
        self.app.ui.numberHoursPreview.valueChanged.disconnect()
        self.app.ui.numberGridPointsRow.valueChanged.disconnect()
        self.app.ui.numberGridPointsCol.valueChanged.disconnect()
        self.app.ui.altitudeMin.valueChanged.disconnect()
        self.app.ui.altitudeMax.valueChanged.disconnect()
        self.app.ui.altitudeBase.valueChanged.disconnect()
        self.app.ui.azimuthBase.valueChanged.disconnect()
        self.app.ui.numberBase.valueChanged.disconnect()
        try:
            if 'CheckSortPoints' in self.app.config:
                self.app.ui.checkSortPoints.setChecked(self.app.config['CheckSortPoints'])
            if 'CheckDeletePointsHorizonMask' in self.app.config:
                self.app.ui.checkDeletePointsHorizonMask.setChecked(self.app.config['CheckDeletePointsHorizonMask'])
            if 'AltitudeBase' in self.app.config:
                self.app.ui.altitudeBase.setValue(self.app.config['AltitudeBase'])
            if 'AzimuthBase' in self.app.config:
                self.app.ui.azimuthBase.setValue(self.app.config['AzimuthBase'])
            if 'NumberGridPointsCol' in self.app.config:
                self.app.ui.numberGridPointsCol.setValue(self.app.config['NumberGridPointsCol'])
            if 'NumberGridPointsRow' in self.app.config:
                self.app.ui.numberGridPointsRow.setValue(self.app.config['NumberGridPointsRow'])
            if 'AltitudeMin' in self.app.config:
                self.app.ui.altitudeMin.setValue(self.app.config['AltitudeMin'])
            if 'AltitudeMax' in self.app.config:
                self.app.ui.altitudeMax.setValue(self.app.config['AltitudeMax'])
            if 'NumberPointsDSO' in self.app.config:
                self.app.ui.numberPointsDSO.setValue(self.app.config['NumberPointsDSO'])
            if 'NumberHoursDSO' in self.app.config:
                self.app.ui.numberHoursDSO.setValue(self.app.config['NumberHoursDSO'])

        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.modelingRunner.initConfig()
        # and restored
        self.app.ui.numberHoursDSO.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateDSOPoints'))
        self.app.ui.numberPointsDSO.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateDSOPoints'))
        self.app.ui.numberHoursPreview.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateDSOPoints'))
        self.app.ui.numberGridPointsRow.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.numberGridPointsCol.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.altitudeMin.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.altitudeMax.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateGridPoints'))
        self.app.ui.altitudeBase.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateInitialPoints'))
        self.app.ui.azimuthBase.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateInitialPoints'))
        self.app.ui.numberBase.valueChanged.connect(lambda: self.commandDispatcherQueue.put('GenerateInitialPoints'))

    def storeConfig(self):
        self.app.config['CheckSortPoints'] = self.app.ui.checkSortPoints.isChecked()
        self.app.config['CheckDeletePointsHorizonMask'] = self.app.ui.checkDeletePointsHorizonMask.isChecked()
        self.app.config['AltitudeBase'] = self.app.ui.altitudeBase.value()
        self.app.config['AzimuthBase'] = self.app.ui.azimuthBase.value()
        self.app.config['NumberGridPointsRow'] = self.app.ui.numberGridPointsRow.value()
        self.app.config['NumberGridPointsCol'] = self.app.ui.numberGridPointsCol.value()
        self.app.config['AltitudeMin'] = self.app.ui.altitudeMin.value()
        self.app.config['AltitudeMax'] = self.app.ui.altitudeMax.value()
        self.app.config['NumberPointsDSO'] = self.app.ui.numberPointsDSO.value()
        self.app.config['NumberHoursDSO'] = self.app.ui.numberHoursDSO.value()
        # and calling the underlying classes as well
        self.modelingRunner.storeConfig()

    def run(self):
        self.logger.info('model dispatcher started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.signalDestruct.connect(self.destruct, type=PyQt5.QtCore.Qt.BlockingQueuedConnection)
        self.cycleTimer = PyQt5.QtCore.QTimer(self)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.doCommand)
        self.cycleTimer.start(self.CYCLE)

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.signalDestruct.emit()
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('model dispatcher stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if not self.commandDispatcherQueue.empty():
            command = self.commandDispatcherQueue.get()
            self.commandDispatcher(command)

    def commandDispatcher(self, command):
        # if we have a command in dispatcher
        if command in self.commandDispatch:
            # running through all necessary commands
            for work in self.commandDispatch[command]['Worker']:
                # if we want to color a button, which one
                if 'Button' in work:
                    self.app.signalChangeStylesheet.emit(work['Button'], 'running', True)
                if 'Parameter' in work:
                    parameter = []
                    for p in work['Parameter']:
                        parameter.append(eval(p))
                    work['Method'](*parameter)
                else:
                    work['Method']()
                time.sleep(0.2)
                if 'Button' in work:
                    self.app.signalChangeStylesheet.emit(work['Button'], 'running', False)
                if 'Cancel' in work:
                    self.app.signalChangeStylesheet.emit(work['Cancel'], 'cancel', False)
                    self.modelingRunner.cancel = False
