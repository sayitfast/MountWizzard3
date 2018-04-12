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
import math
from mount import mount_command
from mount import mount_statusfast
from mount import mount_statusmedium
from mount import mount_statusslow
from mount import mount_statusonce
from mount import mount_getalignmodel
from mount import mount_modelhandling
from analyse import analysedata
from baseclasses import checkIP
from astrometry import transform


class MountDispatcher(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)

    # needed signals for mount connections
    signalMountConnectedOnce = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedSlow = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedMedium = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedFast = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedGetAlign = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedProgAlign = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedCommand = PyQt5.QtCore.pyqtSignal(dict)

    # signals for data transfer to other threads
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal(float, float)
    signalMountShowAlignmentModel = PyQt5.QtCore.pyqtSignal()
    signalSlewFinished = PyQt5.QtCore.pyqtSignal()

    CYCLE_COMMAND = 0.2

    statusReference = {
        '0': 'Tracking',
        '1': 'Stopped after STOP',
        '2': 'Slewing to park position',
        '3': 'Unparking',
        '4': 'Slewing to home position',
        '5': 'Parked',
        '6': 'Slewing or going to stop',
        '7': 'Tracking Off no move',
        '8': 'Motor low temperature',
        '9': 'Tracking outside limits',
        '10': 'Following Satellite',
        '11': 'User OK Needed',
        '98': 'Unknown Status',
        '99': 'Error'
    }

    data = {
        'SiteLatitude': '49:00:00',
        'SiteLongitude': '01:00:00',
        'SiteHeight': '1',
        'MountIP': '',
        'MountMAC': '',
        'MountPort': 3490,
        'LocalSiderealTime': '',
        'JulianDate': '2458096.5',
        'FW': 21501
    }

    def __init__(self, app, thread):
        super().__init__()
        self.app = app
        self.thread = thread
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexIPChange = PyQt5.QtCore.QMutex()
        self.commandDispatcherQueue = queue.Queue()
        # getting all supporting classes assigned
        self.mountModelHandling = mount_modelhandling.MountModelHandling(self.app, self.data)
        self.analyse = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)
        self.checkIP = checkIP.CheckIP()
        self.settingsChanged = False

        # getting all threads setup
        # commands sending thread
        self.threadMountCommandRunner = PyQt5.QtCore.QThread()
        self.workerMountCommandRunner = mount_command.MountCommandRunner(self.app, self.threadMountCommandRunner, self.data, self.signalMountConnectedCommand)
        self.threadMountCommandRunner.setObjectName("MountCommandRunner")
        self.workerMountCommandRunner.moveToThread(self.threadMountCommandRunner)
        self.threadMountCommandRunner.started.connect(self.workerMountCommandRunner.run)
        # fast status thread
        self.threadMountStatusRunnerFast = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerFast = mount_statusfast.MountStatusRunnerFast(self.app, self.threadMountStatusRunnerFast, self.data, self.signalMountConnectedFast)
        self.threadMountStatusRunnerFast.setObjectName("MountStatusRunnerFast")
        self.workerMountStatusRunnerFast.moveToThread(self.threadMountStatusRunnerFast)
        self.threadMountStatusRunnerFast.started.connect(self.workerMountStatusRunnerFast.run)
        # medium status thread
        self.threadMountStatusRunnerMedium = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerMedium = mount_statusmedium.MountStatusRunnerMedium(self.app, self.threadMountStatusRunnerMedium, self.data, self.signalMountConnectedMedium)
        self.threadMountStatusRunnerMedium.setObjectName("MountStatusRunnerMedium")
        self.workerMountStatusRunnerMedium.moveToThread(self.threadMountStatusRunnerMedium)
        self.threadMountStatusRunnerMedium.started.connect(self.workerMountStatusRunnerMedium.run)
        # slow status thread
        self.threadMountStatusRunnerSlow = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerSlow = mount_statusslow.MountStatusRunnerSlow(self.app, self.threadMountStatusRunnerSlow, self.data, self.signalMountConnectedSlow)
        self.threadMountStatusRunnerSlow.setObjectName("MountStatusRunnerSlow")
        self.workerMountStatusRunnerSlow.moveToThread(self.threadMountStatusRunnerSlow)
        self.threadMountStatusRunnerSlow.started.connect(self.workerMountStatusRunnerSlow.run)
        # once status thread
        self.threadMountStatusRunnerOnce = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerOnce = mount_statusonce.MountStatusRunnerOnce(self.app, self.threadMountStatusRunnerOnce, self.data, self.signalMountConnectedOnce)
        self.threadMountStatusRunnerOnce.setObjectName("MountStatusRunnerOnce")
        self.workerMountStatusRunnerOnce.moveToThread(self.threadMountStatusRunnerOnce)
        self.threadMountStatusRunnerOnce.started.connect(self.workerMountStatusRunnerOnce.run)
        # get alignment model
        self.threadMountGetAlignmentModel = PyQt5.QtCore.QThread()
        self.workerMountGetAlignmentModel = mount_getalignmodel.MountGetAlignmentModel(self.app, self.threadMountGetAlignmentModel, self.data, self.signalMountConnectedGetAlign)
        self.threadMountGetAlignmentModel.setObjectName("MountGetAlignmentModel")
        self.workerMountGetAlignmentModel.moveToThread(self.threadMountGetAlignmentModel)
        self.threadMountGetAlignmentModel.started.connect(self.workerMountGetAlignmentModel.run)

        self.mountStatus = {'Fast': False,
                            'Medium': False,
                            'Slow': False,
                            'Once': False,
                            'GetAlign': False,
                            'Command': False}
        self.cancelRunTargetRMS = False
        self.runTargetRMS = False
        self.programAlignmentModelStatus = None
        self.commandDispatch = {
            'RunTargetRMSAlignment':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_runTargetRMSAlignment,
                            'Method': self.runTargetRMSAlignment,
                            'Cancel': self.app.ui.btn_cancelRunTargetRMSAlignment
                        }
                    ]
                },
            'ClearAlign':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_clearModel,
                            'Method': self.mountModelHandling.clearAlign
                        }
                    ]
                },
            'DeleteWorstPoint':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_deleteWorstPoint,
                            'Method': self.deleteWorstPoint,
                        }
                    ]
                },
            'ReloadAlignmentModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_reloadAlignmentModel,
                            'Method': self.reloadAlignmentModel,
                        }
                    ]
                },
            'SaveBackupModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveBackupModel,
                            'Parameter': ['BACKUP'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'LoadBackupModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadBackupModel,
                            'Parameter': ['BACKUP'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'LoadInitialModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadInitialModel,
                            'Parameter': ['INITIAL'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveInitialModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveInitialModel,
                            'Parameter': ['INITIAL'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'LoadFull1Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadFull1Model,
                            'Parameter': ['FULL1'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveFull1Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveFull1Model,
                            'Parameter': ['FULL1'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'LoadFull2Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadFull2Model,
                            'Parameter': ['FULL2'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveFull2Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveFull2Model,
                            'Parameter': ['FULL2'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'LoadDSO1Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadDSO1Model,
                            'Parameter': ['DSO1'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveDSO1Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveDSO1Model,
                            'Parameter': ['DSO1'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'LoadDSO2Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadDSO2Model,
                            'Parameter': ['DSO2'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveDSO2Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveDSO2Model,
                            'Parameter': ['DSO2'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'SetRefractionParameter':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_setRefractionParameters,
                            'Method': self.workerMountStatusRunnerMedium.getStatusMedium,
                        }
                    ]
                },
            'FLIP':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_flipMount,
                            'Method': self.flipMount,
                        }
                    ]
                },
            'Shutdown':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_mountShutdown,
                            'Method': self.mountShutdown,
                        }
                    ]
                }
        }
        # signal slot
        # self.app.ui.le_mountIP.textChanged.connect(self.setIP)
        self.app.ui.le_mountIP.editingFinished.connect(self.changedMountConnectionSettings)
        self.app.ui.le_mountMAC.editingFinished.connect(self.setMAC)
        self.app.ui.btn_setRefractionParameters.clicked.connect(lambda: self.commandDispatcherQueue.put('SetRefractionParameter'))
        self.app.ui.btn_runTargetRMSAlignment.clicked.connect(lambda: self.commandDispatcherQueue.put('RunTargetRMSAlignment'))
        self.app.ui.btn_deleteWorstPoint.clicked.connect(lambda: self.commandDispatcherQueue.put('DeleteWorstPoint'))
        self.app.ui.btn_flipMount.clicked.connect(lambda: self.commandDispatcherQueue.put('FLIP'))
        self.app.ui.btn_reloadAlignmentModel.clicked.connect(lambda: self.commandDispatcherQueue.put('ReloadAlignmentModel'))
        self.app.ui.btn_saveBackupModel.clicked.connect(lambda: self.commandDispatcherQueue.put('SaveBackupModel'))
        self.app.ui.btn_loadBackupModel.clicked.connect(lambda: self.commandDispatcherQueue.put('LoadBackupModel'))
        self.app.ui.btn_saveFull2Model.clicked.connect(lambda: self.commandDispatcherQueue.put('SaveFull2Model'))
        self.app.ui.btn_loadFull2Model.clicked.connect(lambda: self.commandDispatcherQueue.put('LoadFull2Model'))
        self.app.ui.btn_saveFull1Model.clicked.connect(lambda: self.commandDispatcherQueue.put('SaveFull1Model'))
        self.app.ui.btn_loadFull1Model.clicked.connect(lambda: self.commandDispatcherQueue.put('LoadFull1Model'))
        self.app.ui.btn_saveInitialModel.clicked.connect(lambda: self.commandDispatcherQueue.put('SaveInitialModel'))
        self.app.ui.btn_loadInitialModel.clicked.connect(lambda: self.commandDispatcherQueue.put('LoadInitialModel'))
        self.app.ui.btn_saveDSO1Model.clicked.connect(lambda: self.commandDispatcherQueue.put('SaveDSO1Model'))
        self.app.ui.btn_loadDSO1Model.clicked.connect(lambda: self.commandDispatcherQueue.put('LoadDSO1Model'))
        self.app.ui.btn_saveDSO2Model.clicked.connect(lambda: self.commandDispatcherQueue.put('SaveDSO2Model'))
        self.app.ui.btn_loadDSO2Model.clicked.connect(lambda: self.commandDispatcherQueue.put('LoadDSO2Model'))
        self.app.ui.btn_mountShutdown.clicked.connect(lambda: self.commandDispatcherQueue.put('Shutdown'))
        self.app.ui.btn_clearModel.clicked.connect(lambda: self.commandDispatcherQueue.put('ClearAlign'))

    def initConfig(self):
        try:
            if 'MountIP' in self.app.config:
                self.app.ui.le_mountIP.setText(self.app.config['MountIP'])
            if 'MountMAC' in self.app.config:
                self.app.ui.le_mountMAC.setText(self.app.config['MountMAC'])
            if 'CheckAutoRefractionContinous' in self.app.config:
                self.app.ui.checkAutoRefractionContinous.setChecked(self.app.config['CheckAutoRefractionContinous'])
            if 'CheckAutoRefractionNotTracking' in self.app.config:
                self.app.ui.checkAutoRefractionNotTracking.setChecked(self.app.config['CheckAutoRefractionNotTracking'])
            if 'CheckAutoRefractionNone' in self.app.config:
                self.app.ui.checkAutoRefractionNone.setChecked(self.app.config['CheckAutoRefractionNone'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        # setting changes in gui on false, because the set of the config changed them already
        self.settingsChanged = True
        self.changedMountConnectionSettings()

    def storeConfig(self):
        self.app.config['MountIP'] = self.app.ui.le_mountIP.text()
        self.app.config['MountMAC'] = self.app.ui.le_mountMAC.text()
        self.app.config['CheckAutoRefractionContinous'] = self.app.ui.checkAutoRefractionContinous.isChecked()
        self.app.config['CheckAutoRefractionNotTracking'] = self.app.ui.checkAutoRefractionNotTracking.isChecked()
        self.app.config['CheckAutoRefractionNone'] = self.app.ui.checkAutoRefractionNone.isChecked()

    def changedMountConnectionSettings(self):
        if self.settingsChanged:
            self.settingsChanged = False
            self.mutexIPChange.lock()
            # stopping all interaction
            if self.isRunning:
                # stopping thread for chang of parameters
                self.workerMountStatusRunnerFast.stop()
                self.workerMountStatusRunnerMedium.stop()
                self.workerMountStatusRunnerSlow.stop()
                self.workerMountStatusRunnerOnce.stop()
                self.workerMountGetAlignmentModel.stop()
                self.workerMountCommandRunner.stop()
                self.app.sharedMountDataLock.lockForWrite()
                self.data['MountIP'] = self.app.ui.le_mountIP.text()
                self.data['MountMAC'] = self.app.ui.le_mountMAC.text()
                self.app.sharedMountDataLock.unlock()
                # and restarting for using new parameters
                self.threadMountCommandRunner.start()
                self.threadMountGetAlignmentModel.start()
                self.threadMountStatusRunnerOnce.start()
                self.threadMountStatusRunnerSlow.start()
                self.threadMountStatusRunnerMedium.start()
                self.threadMountStatusRunnerFast.start()
            else:
                self.app.sharedMountDataLock.lockForWrite()
                self.data['MountIP'] = self.app.ui.le_mountIP.text()
                self.data['MountMAC'] = self.app.ui.le_mountMAC.text()
                self.app.sharedMountDataLock.unlock()
            self.app.messageQueue.put('Setting IP address for mount to: {0}\n'.format(self.data['MountIP']))
            self.mutexIPChange.unlock()

    def setMAC(self):
        valid, value = self.checkIP.checkMAC(self.app.ui.le_mountMAC)
        self.app.sharedMountDataLock.lockForWrite()
        self.data['MountMAC'] = self.app.ui.le_mountMAC.text()
        self.app.sharedMountDataLock.unlock()

    def run(self):
        self.logger.info('mount dispatcher started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.threadMountCommandRunner.start()
        self.threadMountGetAlignmentModel.start()
        self.threadMountStatusRunnerOnce.start()
        self.threadMountStatusRunnerSlow.start()
        self.threadMountStatusRunnerMedium.start()
        self.threadMountStatusRunnerFast.start()
        while self.isRunning:
            if not self.doCommand():
                time.sleep(self.CYCLE_COMMAND)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.workerMountStatusRunnerFast.stop()
            self.workerMountStatusRunnerMedium.stop()
            self.workerMountStatusRunnerSlow.stop()
            self.workerMountStatusRunnerOnce.stop()
            self.workerMountGetAlignmentModel.stop()
            self.workerMountCommandRunner.stop()
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        # stopping all interaction
        self.logger.info('mount dispatcher stopped')

    def doCommand(self):
        if not self.commandDispatcherQueue.empty():
            command = self.commandDispatcherQueue.get()
            self.commandDispatcher(command)
            return True
        else:
            return False

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
                        parameter.append(p)
                    work['Method'](*parameter)
                else:
                    work['Method']()
                time.sleep(0.2)
                if 'Button' in work:
                    self.app.signalChangeStylesheet.emit(work['Button'], 'running', False)
                if 'Cancel' in work:
                    self.app.signalChangeStylesheet.emit(work['Cancel'], 'cancel', False)

    def mountShutdown(self):
        commandSet = {'command': ':shutdown#', 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'] == '1':
            self.workerMountCommandRunner.connected = False
            time.sleep(1)
            self.logger.info('Shutdown mount manually')
            self.app.messageQueue.put('Shutting mount down !\n')
        else:
            self.logger.error('error: {0}'.format(commandSet['reply']))
            self.app.messageQueue.put('#BRError in mount shutdown\n')

    def flipMount(self):
        commandSet = {'command': ':FLIP#', 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'] == '0':
            self.app.messageQueue.put('#BRFlip Mount could not be executed\n')
            self.logger.error('error: {0}'.format(commandSet['reply']))

    def syncMountModel(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.app.mountCommandQueue.put(':Sr{0}#'.format(ra))
        self.app.mountCommandQueue.put(':Sd{0}#'.format(dec))
        self.app.mountCommandQueue.put(':CMCFG0#')
        # send sync command
        commandSet = {'command': ':CM#', 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'][:5] == 'Coord':
            self.logger.info('mount modeling synced')
            return True
        else:
            self.logger.warning('error in sync mount modeling')
            return False

    def programBatchData(self, data):
        self.app.messageQueue.put('#BWProgramming alignment model data\n')
        commandSet = {'command': ':newalig#', 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        for i in range(0, len(data['Index'])):
            self.app.sharedMountDataLock.lockForRead()
            command = ':newalpt{0},{1},{2},{3},{4},{5}#'.format(self.transform.decimalToDegree(data['RaJNow'][i], False, True),
                                                                self.transform.decimalToDegree(data['DecJNow'][i], True, False),
                                                                data['Pierside'][i],
                                                                self.transform.decimalToDegree(data['RaJNowSolved'][i], False, True),
                                                                self.transform.decimalToDegree(data['DecJNowSolved'][i], True, False),
                                                                self.transform.decimalToDegree(data['LocalSiderealTimeFloat'][i], False, True))
            self.app.sharedMountDataLock.unlock()
            commandSet = {'command': command, 'reply': ''}
            self.app.mountCommandQueue.put(commandSet)
            while len(commandSet['reply']) == 0:
                time.sleep(0.1)
            if commandSet['reply'] == 'E':
                self.app.messageQueue.put('Point {0:02d} could not be added\n'.format(i + 1))
            else:
                self.app.messageQueue.put('Processed>{0:02d}'.format(i + 1))
        commandSet = {'command': ':endalig#', 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'] == 'V':
            self.logger.info('Model successful finished!')
            self.app.messageQueue.put('#BWProgrammed alignment model with {0} points\n'.format(len(data['Index'])))
        else:
            self.logger.warning('Model could not be calculated with current data!')
            self.app.messageQueue.put('#BRProgramming alignment model finished with errors\n')

    def runTargetRMSAlignment(self):
        self.runTargetRMS = True
        self.cancelRunTargetRMS = False
        self.app.messageQueue.put('#BWTarget RMS Run started\n')
        self.app.sharedMountDataLock.lockForRead()
        condition = ('Number' not in self.data or self.data['Number'] < 4)
        self.app.sharedMountDataLock.unlock()
        if condition:
            self.runTargetRMS = False
            return
        while True:
            self.app.sharedMountDataLock.lockForRead()
            data = self.data['RMS']
            self.app.sharedMountDataLock.unlock()
            if self.cancelRunTargetRMS:
                break
            if data < float(self.app.ui.targetRMS.value()):
                break
            if self.deleteWorstPoint():
                break
        if self.cancelRunTargetRMS:
            self.app.messageQueue.put('#BRTarget RMS Run canceled\n')
        else:
            self.app.messageQueue.put('#BWTarget RMS Run finished\n')
        self.runTargetRMS = False

    def reloadAlignmentModel(self):
        self.workerMountGetAlignmentModel.getAlignmentModel()
        # wait form alignment model to be downloaded
        while True:
            self.app.sharedMountDataLock.lockForRead()
            condition = not self.data['ModelLoading']
            self.app.sharedMountDataLock.unlock()
            if condition:
                break
            time.sleep(0.2)

    def deleteWorstPoint(self):
        # if there are less than 4 point, optimization can't take place
        self.app.sharedMountDataLock.lockForRead()
        if self.data['Number'] < 4:
            return True
        # find worst point
        maxError = 0
        worstPointIndex = 0
        for i in range(0, self.data['Number']):
            if self.data['ModelError'][i] > maxError:
                worstPointIndex = i
                maxError = self.data['ModelError'][i]
        self.app.messageQueue.put('Deleting worst point  {0:02d} with AZ:  {1:05.1f}  ALT:  {2:04.1f}  and error of:  {3:05.1f}\n'
                                  .format(worstPointIndex + 1,
                                          self.data['ModelAzimuth'][worstPointIndex],
                                          self.data['ModelAltitude'][worstPointIndex],
                                          maxError))
        self.app.sharedMountDataLock.unlock()
        commandSet = {'command': ':delalst{0:d}#'.format(worstPointIndex + 1), 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        time.sleep(0.2)
        if commandSet['reply'] == '1':
            # point could be deleted, feedback from mount ok
            self.logger.info('Deleting worst point {0} with error of:  {1}'.format(worstPointIndex+1, maxError))
            # get new calculated alignment model from mount
            self.app.messageQueue.put('\tPoint deleted\n')
        else:
            self.app.messageQueue.put('#BR\tPoint could not be deleted \n')
            self.logger.warning('Point {0} could not be deleted'.format(worstPointIndex))
        self.workerMountGetAlignmentModel.getAlignmentModel()
        # wait form alignment model to be downloaded
        while True:
            self.app.sharedMountDataLock.lockForRead()
            condition = not self.data['ModelLoading']
            self.app.sharedMountDataLock.unlock()
            if condition:
                break
            time.sleep(0.2)

    def retrofitMountData(self, modelingData):
        self.app.sharedMountDataLock.lockForRead()
        self.app.sharedModelingDataLock.lockForWrite()
        if len(self.data['ModelError']) == len(modelingData['Index']):
            modelingData['ModelErrorOptimized'] = list()
            modelingData['RaErrorOptimized'] = list()
            modelingData['DecErrorOptimized'] = list()
            for i in range(0, len(self.data['ModelError'])):
                modelingData['ModelErrorOptimized'].append(self.data['ModelError'][i])
                modelingData['RaErrorOptimized'].append(self.data['ModelError'][i] * math.sin(math.radians(self.data['ModelErrorAngle'][i])))
                modelingData['DecErrorOptimized'].append(self.data['ModelError'][i] * math.cos(math.radians(self.data['ModelErrorAngle'][i])))
            self.app.messageQueue.put('Data synced\n')
        else:
            self.logger.warning('Size mount modeling {0} and modeling data {1} do not fit !'.format(len(modelingData), len(self.data['ModelError'])))
            self.app.messageQueue.put('Mount Model and Model Data could not be synced\n')
            self.app.messageQueue.put('Error data sync mismatch!\n')
        self.app.sharedMountDataLock.unlock()
        self.app.sharedModelingDataLock.unlock()
