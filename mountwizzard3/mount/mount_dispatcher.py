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
import copy
from mount import mount_command
from mount import mount_statusfast
from mount import mount_statusmedium
from mount import mount_statusslow
from mount import mount_statusonce
from mount import mount_getalignmodel
from mount import mount_setalignmodel
from mount import mount_getmodelnames
from mount import mount_modelhandling
from analyse import analysedata
from baseclasses import checkIP
from astrometry import transform


class MountDispatcher(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)

    # needed signals for mount connections
    signalMountConnected = PyQt5.QtCore.pyqtSignal(dict)
    signalCancelRunTargetRMS = PyQt5.QtCore.pyqtSignal()

    # signals for data transfer to other threads
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal(float, float)
    signalMountLimits = PyQt5.QtCore.pyqtSignal()
    signalAlignmentStars = PyQt5.QtCore.pyqtSignal()
    signalMountShowAlignmentModel = PyQt5.QtCore.pyqtSignal()
    signalMountShowModelNames = PyQt5.QtCore.pyqtSignal()
    signalSlewFinished = PyQt5.QtCore.pyqtSignal()

    CYCLE = 200
    signalDestruct = PyQt5.QtCore.pyqtSignal()

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
        # positions of greenwich at start
        'SiteLatitude': '51:28:37',
        'SiteLongitude': '00:00:00',
        'SiteHeight': '46',
        'MountIP': '',
        'MountMAC': '',
        'MountPort': 3490,
        'LocalSiderealTime': '',
        # date of 01.05.2018
        'JulianDate': '2458240',
        'FW': 0
    }

    mountStatus = {
            'Fast': False,
            'Medium': False,
            'Slow': False,
            'Once': False,
            'GetAlign': False,
            'SetAlign': False,
            'GetName': False,
            'Command': False
    }

    def __init__(self, app, thread):
        super().__init__()
        self.app = app
        self.thread = thread
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexIPChange = PyQt5.QtCore.QMutex()
        self.commandDispatcherQueue = queue.Queue()
        self.cycleTimer = None
        # getting all supporting classes assigned
        self.mountModelHandling = mount_modelhandling.MountModelHandling(self.app, self.data)
        self.analyse = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)
        self.checkIP = checkIP.CheckIP()

        # getting all threads setup
        # commands sending thread
        self.threadMountCommandRunner = PyQt5.QtCore.QThread()
        self.workerMountCommandRunner = mount_command.MountCommandRunner(self.app, self.threadMountCommandRunner, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountCommandRunner.setObjectName("MountCommandRunner")
        self.workerMountCommandRunner.moveToThread(self.threadMountCommandRunner)
        self.threadMountCommandRunner.started.connect(self.workerMountCommandRunner.run)
        # fast status thread
        self.threadMountStatusRunnerFast = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerFast = mount_statusfast.MountStatusRunnerFast(self.app, self.threadMountStatusRunnerFast, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountStatusRunnerFast.setObjectName("MountStatusRunnerFast")
        self.workerMountStatusRunnerFast.moveToThread(self.threadMountStatusRunnerFast)
        self.threadMountStatusRunnerFast.started.connect(self.workerMountStatusRunnerFast.run)
        # medium status thread
        self.threadMountStatusRunnerMedium = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerMedium = mount_statusmedium.MountStatusRunnerMedium(self.app, self.threadMountStatusRunnerMedium, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountStatusRunnerMedium.setObjectName("MountStatusRunnerMedium")
        self.workerMountStatusRunnerMedium.moveToThread(self.threadMountStatusRunnerMedium)
        self.threadMountStatusRunnerMedium.started.connect(self.workerMountStatusRunnerMedium.run)
        # slow status thread
        self.threadMountStatusRunnerSlow = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerSlow = mount_statusslow.MountStatusRunnerSlow(self.app, self.threadMountStatusRunnerSlow, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountStatusRunnerSlow.setObjectName("MountStatusRunnerSlow")
        self.workerMountStatusRunnerSlow.moveToThread(self.threadMountStatusRunnerSlow)
        self.threadMountStatusRunnerSlow.started.connect(self.workerMountStatusRunnerSlow.run)
        # once status thread
        self.threadMountStatusRunnerOnce = PyQt5.QtCore.QThread()
        self.workerMountStatusRunnerOnce = mount_statusonce.MountStatusRunnerOnce(self.app, self.threadMountStatusRunnerOnce, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountStatusRunnerOnce.setObjectName("MountStatusRunnerOnce")
        self.workerMountStatusRunnerOnce.moveToThread(self.threadMountStatusRunnerOnce)
        self.threadMountStatusRunnerOnce.started.connect(self.workerMountStatusRunnerOnce.run)
        # get alignment model
        self.threadMountGetAlignmentModel = PyQt5.QtCore.QThread()
        self.workerMountGetAlignmentModel = mount_getalignmodel.MountGetAlignmentModel(self.app, self.threadMountGetAlignmentModel, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountGetAlignmentModel.setObjectName("MountGetAlignmentModel")
        self.workerMountGetAlignmentModel.moveToThread(self.threadMountGetAlignmentModel)
        self.threadMountGetAlignmentModel.started.connect(self.workerMountGetAlignmentModel.run)
        # set alignment model
        self.threadMountSetAlignmentModel = PyQt5.QtCore.QThread()
        self.workerMountSetAlignmentModel = mount_setalignmodel.MountSetAlignmentModel(self.app, self.threadMountSetAlignmentModel, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountSetAlignmentModel.setObjectName("MountSetAlignmentModel")
        self.workerMountSetAlignmentModel.moveToThread(self.threadMountSetAlignmentModel)
        self.threadMountSetAlignmentModel.started.connect(self.workerMountSetAlignmentModel.run)
        # get model names
        self.threadMountGetModelNames = PyQt5.QtCore.QThread()
        self.workerMountGetModelNames = mount_getmodelnames.MountGetModelNames(self.app, self.threadMountGetModelNames, self.data, self.signalMountConnected, self.mountStatus)
        self.threadMountGetModelNames.setObjectName("MountGetModelNames")
        self.workerMountGetModelNames.moveToThread(self.threadMountGetModelNames)
        self.threadMountGetModelNames.started.connect(self.workerMountGetModelNames.run)

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
        self.app.ui.btn_setRefractionParameters.clicked.connect(lambda: self.commandDispatcherQueue.put('SetRefractionParameter'))
        self.app.ui.btn_runTargetRMSAlignment.clicked.connect(lambda: self.commandDispatcherQueue.put('RunTargetRMSAlignment'))
        self.app.ui.btn_deleteWorstPoint.clicked.connect(lambda: self.commandDispatcherQueue.put('DeleteWorstPoint'))
        self.app.ui.btn_flipMount.clicked.connect(lambda: self.commandDispatcherQueue.put('FLIP'))
        self.app.ui.btn_reloadAlignmentModel.clicked.connect(lambda: self.commandDispatcherQueue.put('ReloadAlignmentModel'))
        self.app.ui.btn_mountShutdown.clicked.connect(lambda: self.commandDispatcherQueue.put('Shutdown'))
        self.app.ui.btn_clearModel.clicked.connect(lambda: self.commandDispatcherQueue.put('ClearAlign'))

        self.signalCancelRunTargetRMS.connect(self.setCancelRunTargetRMS)
        self.app.ui.btn_saveModel.clicked.connect(self.saveSelectedModel)
        self.app.ui.btn_loadModel.clicked.connect(self.loadSelectedModel)
        self.app.ui.btn_deleteModel.clicked.connect(self.deleteSelectedModel)
        self.app.ui.listModelName.itemDoubleClicked.connect(self.getListAction)
        self.signalMountShowModelNames.connect(self.setModelNamesList)
        self.signalMountConnected.connect(self.setMountConnectionStatus)

    def initConfig(self):
        try:
            if 'MountIP' in self.app.config:
                self.app.ui.le_mountIP.setText(self.app.config['MountIP'])
                self.app.sharedMountDataLock.lockForWrite()
                self.data['MountIP'] = self.app.config['MountIP']
                self.app.sharedMountDataLock.unlock()
            if 'MountMAC' in self.app.config:
                self.app.ui.le_mountMAC.setText(self.app.config['MountMAC'])
                self.app.sharedMountDataLock.lockForWrite()
                self.data['MountMAC'] = self.app.config['MountMAC']
                self.app.sharedMountDataLock.unlock()
            if 'CheckAutoRefractionContinuous' in self.app.config:
                self.app.ui.checkAutoRefractionContinous.setChecked(self.app.config['CheckAutoRefractionContinuous'])
            if 'CheckAutoRefractionNotTracking' in self.app.config:
                self.app.ui.checkAutoRefractionNotTracking.setChecked(self.app.config['CheckAutoRefractionNotTracking'])
            if 'CheckAutoRefractionNone' in self.app.config:
                self.app.ui.checkAutoRefractionNone.setChecked(self.app.config['CheckAutoRefractionNone'])
            # if we have already stored the site data, we use it until we get new information from mount
            if 'SiteLongitude' in self.app.config:
                self.data['SiteLongitude'] = copy.copy(self.app.config['SiteLongitude'])
            if 'SiteLatitude' in self.app.config:
                self.data['SiteLatitude'] = copy.copy(self.app.config['SiteLatitude'])
            if 'SiteHeight' in self.app.config:
                self.data['SiteHeight'] = copy.copy(self.app.config['SiteHeight'])
                self.app.signalMountSiteData.emit(self.data['SiteLatitude'],
                                                  self.data['SiteLongitude'],
                                                  self.data['SiteHeight'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['MountIP'] = self.app.ui.le_mountIP.text()
        self.app.config['MountMAC'] = self.app.ui.le_mountMAC.text()
        self.app.config['CheckAutoRefractionContinuous'] = self.app.ui.checkAutoRefractionContinous.isChecked()
        self.app.config['CheckAutoRefractionNotTracking'] = self.app.ui.checkAutoRefractionNotTracking.isChecked()
        self.app.config['CheckAutoRefractionNone'] = self.app.ui.checkAutoRefractionNone.isChecked()
        # if we had a connection to the mount, the site data should be there.
        if self.mountStatus['Once']:
            self.app.config['SiteLongitude'] = copy.copy(self.data['SiteLongitude'])
            self.app.config['SiteLatitude'] = copy.copy(self.data['SiteLatitude'])
            self.app.config['SiteHeight'] = copy.copy(self.data['SiteHeight'])

    def setCancelRunTargetRMS(self):
        self.cancelRunTargetRMS = True

    def changedSettings(self):
        self.mutexIPChange.lock()
        # stopping all interaction
        if self.isRunning:
            # stopping thread for chang of parameters
            self.logger.info('Stopping threads for IP change')
            self.workerMountStatusRunnerFast.stop()
            self.workerMountStatusRunnerMedium.stop()
            self.workerMountStatusRunnerSlow.stop()
            self.workerMountStatusRunnerOnce.stop()
            self.workerMountGetAlignmentModel.stop()
            self.workerMountSetAlignmentModel.stop()
            self.workerMountCommandRunner.stop()
            self.workerMountGetModelNames.stop()
            self.app.sharedMountDataLock.lockForWrite()
            self.data['MountIP'] = self.app.ui.le_mountIP.text()
            self.data['MountMAC'] = self.app.ui.le_mountMAC.text()
            self.logger.info('Setting IP address for mount to: {0}'.format(self.data['MountIP']))
            self.app.sharedMountDataLock.unlock()
            # and restarting for using new parameters
            self.threadMountCommandRunner.start()
            self.threadMountGetModelNames.start()
            self.threadMountSetAlignmentModel.start()
            self.threadMountGetAlignmentModel.start()
            self.threadMountStatusRunnerOnce.start()
            self.threadMountStatusRunnerSlow.start()
            self.threadMountStatusRunnerMedium.start()
            self.threadMountStatusRunnerFast.start()
        else:
            self.logger.info('IP change when threads not running')
            self.app.sharedMountDataLock.lockForWrite()
            self.data['MountIP'] = self.app.ui.le_mountIP.text()
            self.data['MountMAC'] = self.app.ui.le_mountMAC.text()
            self.app.sharedMountDataLock.unlock()
        self.app.messageQueue.put('Setting IP address for mount to: {0}\n'.format(self.data['MountIP']))
        self.mutexIPChange.unlock()

    def run(self):
        self.app.ui.le_mountIP.editingFinished.connect(self.changedSettings, type=PyQt5.QtCore.Qt.QueuedConnection)
        self.logger.info('mount dispatcher started')
        # sending default status to gui in red
        self.app.signalSetMountStatus.emit(0)
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.threadMountCommandRunner.start()
        self.threadMountSetAlignmentModel.start()
        self.threadMountGetModelNames.start()
        self.threadMountGetAlignmentModel.start()
        self.threadMountStatusRunnerOnce.start()
        self.threadMountStatusRunnerSlow.start()
        self.threadMountStatusRunnerMedium.start()
        self.threadMountStatusRunnerFast.start()
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
        # stopping all interaction
        self.logger.info('mount dispatcher stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.workerMountStatusRunnerFast.stop()
        self.workerMountStatusRunnerMedium.stop()
        self.workerMountStatusRunnerSlow.stop()
        self.workerMountStatusRunnerOnce.stop()
        self.workerMountGetAlignmentModel.stop()
        self.workerMountSetAlignmentModel.stop()
        self.workerMountGetModelNames.stop()
        self.workerMountCommandRunner.stop()
        self.signalDestruct.disconnect(self.destruct)
        self.app.ui.le_mountIP.editingFinished.disconnect(self.changedSettings)

    def doCommand(self):
        if not self.commandDispatcherQueue.empty():
            command = self.commandDispatcherQueue.get()
            if isinstance(command, dict):
                # transferring complete working set
                self.manualCommandDispatcher(command)
            else:
                # doing standard work based on init
                self.commandDispatcher(command)

    def manualCommandDispatcher(self, command):
        # running through all necessary commands
        for work in command['Worker']:
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

    def setMountConnectionStatus(self, status):
        for key in status:
            self.mountStatus[key] = status[key]
        stat = 0
        for key in self.mountStatus:
            if self.mountStatus[key]:
                stat += 1
        if stat == 0:
            # red
            self.app.signalSetMountStatus.emit(0)
        elif stat == len(self.mountStatus):
            # all connected green
            self.app.signalSetMountStatus.emit(2)
        else:
            # otherwise yellow
            self.app.signalSetMountStatus.emit(1)

    def setModelNamesList(self):
        self.app.ui.listModelName.clear()
        for name in self.data['ModelNames']:
            self.app.ui.listModelName.addItem(name)
        self.app.ui.listModelName.sortItems()
        self.app.ui.listModelName.update()

    def getListAction(self):
        name = self.app.ui.listModelName.currentItem().text()
        question = 'Action with mount model:\n\n\t{0}\n\n'.format(name)
        value = self.app.dialogMessageLoadSaveDelete(self.app, 'Mount model management', question)
        if value == 0:
            action = {
                'Worker': [
                    {
                        'Button': self.app.ui.btn_loadModel,
                        'Parameter': [name],
                        'Method': self.mountModelHandling.loadModel,
                    }
                ]
            }
            self.commandDispatcherQueue.put(action)
        elif value == 1:
            action = {
                'Worker': [
                    {
                        'Button': self.app.ui.btn_saveModel,
                        'Parameter': [name],
                        'Method': self.mountModelHandling.saveModel,
                    }
                ]
            }
            self.commandDispatcherQueue.put(action)
        elif value == 2:
            action = {
                'Worker': [
                    {
                        'Button': self.app.ui.btn_deleteModel,
                        'Parameter': [name],
                        'Method': self.mountModelHandling.deleteModel,
                    }
                ]
            }
            self.commandDispatcherQueue.put(action)
        else:
            pass

    def saveSelectedModel(self):
        if self.app.ui.listModelName.currentItem() is not None:
            name = self.app.ui.listModelName.currentItem().text()
        else:
            name = ''
        name, ok = self.app.dialogInputText(self.app, 'Please enter the model name', 'Model name:', name)
        if ok:
            # limit length of name to 15 characters
            name = name[:15]
            action = {
                'Worker': [
                    {
                        'Button': self.app.ui.btn_saveModel,
                        'Parameter': [name],
                        'Method': self.mountModelHandling.saveModel,
                    }
                ]
            }
            self.commandDispatcherQueue.put(action)

    def loadSelectedModel(self):
        if self.app.ui.listModelName.currentItem() is not None:
            name = self.app.ui.listModelName.currentItem().text()
            action = {
                'Worker': [
                    {
                        'Button': self.app.ui.btn_loadModel,
                        'Parameter': [name],
                        'Method': self.mountModelHandling.loadModel,
                    }
                ]
            }
            self.commandDispatcherQueue.put(action)

    def deleteSelectedModel(self):
        if self.app.ui.listModelName.currentItem() is not None:
            name = self.app.ui.listModelName.currentItem().text()
            action = {
                'Worker': [
                    {
                        'Button': self.app.ui.btn_deleteModel,
                        'Parameter': [name],
                        'Method': self.mountModelHandling.deleteModel,
                    }
                ]
            }
            self.commandDispatcherQueue.put(action)

    def mountShutdown(self):
        # mount has to run
        if self.workerMountCommandRunner.socket.state() != PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            return
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
            self.logger.info('Mount modeling synced')
            return True
        else:
            self.logger.warning('Error in sync mount modeling')
            return False

    def programBatchData(self, data):
        if not('RaJNow' in data and 'DecJNow' in data):
            self.logger.warning('RaJNow or DecJNow not in data file')
            self.messageQueue.put('Mount coordinates missing\n')
            return
        if not('RaJNowSolved' in data and 'DecJNowSolved' in data):
            self.logger.warning('RaJNowSolved or DecJNowSolved not in data file')
            self.messageQueue.put('Solved data missing\n')
            return
        if not('Pierside' in data and 'LocalSiderealTimeFloat' in data):
            self.logger.warning('Pierside and LocalSiderealTimeFloat not in data file')
            self.messageQueue.put('Time and Pierside missing\n')
            return
        self.app.messageQueue.put('#BWProgramming alignment model data\n')
        self.workerMountSetAlignmentModel.result = None
        self.workerMountSetAlignmentModel.setAlignmentModel(data)
        while self.workerMountSetAlignmentModel.result is None:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if self.workerMountSetAlignmentModel.result:
            self.logger.info('Model successful finished!')
            self.app.messageQueue.put('#BWProgrammed alignment model with {0} points\n'.format(len(data['Index'])))
        else:
            self.logger.warning('Model could not be calculated with current data!')
            self.app.messageQueue.put('#BRProgramming alignment model finished with errors\n')
        self.commandDispatcherQueue.put('ReloadAlignmentModel')

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
            returnValue = True
        else:
            self.logger.warning('Size mount modeling {0} and modeling data {1} do not fit !'.format(len(modelingData['Index']), len(self.data['ModelError'])))
            self.app.messageQueue.put('Mount Model and Model Data could not be synced\n')
            self.app.messageQueue.put('Error data sync mismatch!\n')
            returnValue = False
        self.app.sharedMountDataLock.unlock()
        self.app.sharedModelingDataLock.unlock()
        return returnValue
