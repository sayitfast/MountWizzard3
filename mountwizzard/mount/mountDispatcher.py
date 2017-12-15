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
# import basic stuff
import time
# import PyQT5 for threading purpose
import PyQt5
import threading
from mount import mountCommandRunner
from mount import mountStatusRunnerFast
from mount import mountStatusRunnerMedium
from mount import mountStatusRunnerSlow
from mount import mountStatusRunnerOnce
from mount import mountGetAlignmentModel
# astrometry
from astrometry import transform
from mount import mountModelHandling
from analyse import analysedata
from baseclasses import checkParamIP


class MountDispatcher(PyQt5.QtCore.QThread):
    finished = PyQt5.QtCore.pyqtSignal()
    logger = logging.getLogger(__name__)
    signalMountConnectedOnce = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedSlow = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedMedium = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedFast = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedAlign = PyQt5.QtCore.pyqtSignal(dict)
    signalMountConnectedCommand = PyQt5.QtCore.pyqtSignal(dict)
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal([float, float])
    signalMountTrackPreview = PyQt5.QtCore.pyqtSignal()
    signalMountShowAlignmentModel = PyQt5.QtCore.pyqtSignal()

    CYCLE_AUTO_UPDATE = 3000

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

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.ipChangeLock = threading.Lock()
        # getting all supporting classes assigned
        self.mountModelHandling = mountModelHandling.MountModelHandling(self.app, self.data)
        self.analyse = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)
        self.checkIP = checkParamIP.CheckIP()

        # getting all threads setup
        # commands sending thread
        self.workerMountCommandRunner = mountCommandRunner.MountCommandRunner(self.app, self.data, self.signalMountConnectedCommand)
        self.threadMountCommandRunner = PyQt5.QtCore.QThread()
        self.threadMountCommandRunner.setObjectName("MountCommandRunner")
        self.workerMountCommandRunner.moveToThread(self.threadMountCommandRunner)
        self.threadMountCommandRunner.started.connect(self.workerMountCommandRunner.run)
        self.workerMountCommandRunner.finished.connect(self.workerMountCommandRunnerStop)
        # fast status thread
        self.workerMountStatusRunnerFast = mountStatusRunnerFast.MountStatusRunnerFast(self.app, self.data, self.signalMountConnectedFast, self.signalMountAzAltPointer)
        self.threadMountStatusRunnerFast = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerFast.setObjectName("MountStatusRunnerFast")
        self.workerMountStatusRunnerFast.moveToThread(self.threadMountStatusRunnerFast)
        self.threadMountStatusRunnerFast.started.connect(self.workerMountStatusRunnerFast.run)
        self.workerMountStatusRunnerFast.finished.connect(self.workerMountStatusRunnerFastStop)
        # medium status thread
        self.workerMountStatusRunnerMedium = mountStatusRunnerMedium.MountStatusRunnerMedium(self.app, self.data, self.signalMountConnectedMedium, self.signalMountTrackPreview)
        self.threadMountStatusRunnerMedium = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerMedium.setObjectName("MountStatusRunnerMedium")
        self.workerMountStatusRunnerMedium.moveToThread(self.threadMountStatusRunnerMedium)
        self.threadMountStatusRunnerMedium.started.connect(self.workerMountStatusRunnerMedium.run)
        self.workerMountStatusRunnerMedium.finished.connect(self.workerMountStatusRunnerMediumStop)
        # slow status thread
        self.workerMountStatusRunnerSlow = mountStatusRunnerSlow.MountStatusRunnerSlow(self.app, self.data, self.signalMountConnectedSlow)
        self.threadMountStatusRunnerSlow = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerSlow.setObjectName("MountStatusRunnerSlow")
        self.workerMountStatusRunnerSlow.moveToThread(self.threadMountStatusRunnerSlow)
        self.threadMountStatusRunnerSlow.started.connect(self.workerMountStatusRunnerSlow.run)
        self.workerMountStatusRunnerSlow.finished.connect(self.workerMountStatusRunnerSlowStop)
        # once status thread
        self.workerMountStatusRunnerOnce = mountStatusRunnerOnce.MountStatusRunnerOnce(self.app, self.data, self.signalMountConnectedOnce)
        self.threadMountStatusRunnerOnce = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerOnce.setObjectName("MountStatusRunnerOnce")
        self.workerMountStatusRunnerOnce.moveToThread(self.threadMountStatusRunnerOnce)
        self.threadMountStatusRunnerOnce.started.connect(self.workerMountStatusRunnerOnce.run)
        self.workerMountStatusRunnerOnce.finished.connect(self.workerMountStatusRunnerOnceStop)
        # get alignment model
        self.workerMountGetAlignmentModel = mountGetAlignmentModel.MountGetAlignmentModel(self.app, self.data, self.signalMountConnectedAlign, self.signalMountShowAlignmentModel)
        self.threadMountGetAlignmentModel = PyQt5.QtCore.QThread()
        self.threadMountGetAlignmentModel.setObjectName("MountGetAlignmentModel")
        self.workerMountGetAlignmentModel.moveToThread(self.threadMountGetAlignmentModel)
        self.threadMountGetAlignmentModel.started.connect(self.workerMountGetAlignmentModel.run)
        self.workerMountGetAlignmentModel.finished.connect(self.workerMountGetAlignmentModelStop)

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
                            'Button': self.app.ui.btn_clearAlignmentModel,
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
            'LoadBaseModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadBaseModel,
                            'Parameter': ['BASE'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveBaseModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveBaseModel,
                            'Parameter': ['BASE'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'LoadRefinementModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadRefinementModel,
                            'Parameter': ['REFINE'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveRefinementModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveRefinementModel,
                            'Parameter': ['REFINE'],
                            'Method': self.mountModelHandling.saveModel,
                        }
                    ]
                },
            'LoadSimpleModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadSimpleModel,
                            'Parameter': ['SIMPLE'],
                            'Method': self.mountModelHandling.loadModel,
                        }
                    ]
                },
            'SaveSimpleModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveSimpleModel,
                            'Parameter': ['SIMPLE'],
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

        self.mountStatus = {'Fast': False,
                            'Medium': False,
                            'Slow': False,
                            'Once': False,
                            'Align': False,
                            'Command': False}
        self.cancelRunTargetRMS = False
        self.runTargetRMS = False

    def initConfig(self):
        try:
            if 'MountIP' in self.app.config:
                self.app.ui.le_mountIP.setText(self.app.config['MountIP'])
            if 'MountMAC' in self.app.config:
                self.app.ui.le_mountMAC.setText(self.app.config['MountMAC'])
            if 'CheckAutoRefractionCamera' in self.app.config:
                self.app.ui.checkAutoRefractionCamera.setChecked(self.app.config['CheckAutoRefractionCamera'])
            if 'CheckAutoRefractionNotTracking' in self.app.config:
                self.app.ui.checkAutoRefractionNotTracking.setChecked(self.app.config['CheckAutoRefractionNotTracking'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            self.app.ui.le_mountIP.textChanged.connect(self.changedMountConnectionSettings)
            self.app.ui.le_mountMAC.textChanged.connect(self.changedMountConnectionSettings)
            self.setIP()
            self.setMAC()

    def storeConfig(self):
        self.app.config['MountIP'] = self.app.ui.le_mountIP.text()
        self.app.config['MountMAC'] = self.app.ui.le_mountMAC.text()
        self.app.config['CheckAutoRefractionCamera'] = self.app.ui.checkAutoRefractionCamera.isChecked()
        self.app.config['CheckAutoRefractionNotTracking'] = self.app.ui.checkAutoRefractionNotTracking.isChecked()

    def changedMountConnectionSettings(self):
        # todo: change of IP address in the run with reconnect
        return
        # stopping all interaction
        self.ipChangeLock.acquire()
        self.workerMountCommandRunner.stop()
        self.workerMountGetAlignmentModel.stop()
        self.workerMountStatusRunnerOnce.stop()
        self.workerMountStatusRunnerSlow.stop()
        self.workerMountStatusRunnerMedium.stop()
        self.workerMountStatusRunnerFast.stop()
        # setting new values
        self.setIP()
        self.setMAC()
        # starting new communication
        self.threadMountCommandRunner.start()
        self.threadMountGetAlignmentModel.start()
        self.threadMountStatusRunnerOnce.start()
        self.threadMountStatusRunnerSlow.start()
        self.threadMountStatusRunnerMedium.start()
        self.threadMountStatusRunnerFast.start()
        self.ipChangeLock.release()

    def setIP(self):
        valid, value = self.checkIP.checkIP(self.app.ui.le_mountIP)
        if valid:
            self.data['MountIP'] = value

    def setMAC(self):
        valid, value = self.checkIP.checkMAC(self.app.ui.le_mountMAC)
        if valid:
            self.data['mountMAC'] = value

    def workerMountStatusRunnerFastStop(self):
        self.threadMountStatusRunnerFast.quit()
        self.threadMountStatusRunnerFast.wait()

    def workerMountStatusRunnerMediumStop(self):
        self.threadMountStatusRunnerMedium.quit()
        self.threadMountStatusRunnerMedium.wait()

    def workerMountStatusRunnerSlowStop(self):
        self.threadMountStatusRunnerSlow.quit()
        self.threadMountStatusRunnerSlow.wait()

    def workerMountStatusRunnerOnceStop(self):
        self.threadMountStatusRunnerOnce.quit()
        self.threadMountStatusRunnerOnce.wait()

    def workerMountCommandRunnerStop(self):
        self.threadMountCommandRunner.quit()
        self.threadMountCommandRunner.wait()

    def workerMountGetAlignmentModelStop(self):
        self.threadMountGetAlignmentModel.quit()
        self.threadMountGetAlignmentModel.wait()

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.threadMountStatusRunnerOnce.start()
        self.threadMountStatusRunnerSlow.start()
        self.threadMountStatusRunnerMedium.start()
        self.threadMountStatusRunnerFast.start()
        self.threadMountCommandRunner.start()
        self.threadMountGetAlignmentModel.start()

        self.app.ui.btn_setRefractionParameters.clicked.connect(lambda: self.commandDispatcher('SetRefractionParameter'))
        self.app.ui.btn_runTargetRMSAlignment.clicked.connect(lambda: self.commandDispatcher('RunTargetRMSAlignment'))
        self.app.ui.btn_deleteWorstPoint.clicked.connect(lambda: self.commandDispatcher('DeleteWorstPoint'))
        self.app.ui.btn_flipMount.clicked.connect(lambda: self.commandDispatcher('FLIP'))
        self.app.ui.btn_saveBackupModel.clicked.connect(lambda: self.commandDispatcher('SaveBackupModel'))
        self.app.ui.btn_loadBackupModel.clicked.connect(lambda: self.commandDispatcher('LoadBackupModel'))
        self.app.ui.btn_saveSimpleModel.clicked.connect(lambda: self.commandDispatcher('SaveSimpleModel'))
        self.app.ui.btn_loadSimpleModel.clicked.connect(lambda: self.commandDispatcher('LoadSimpleModel'))
        self.app.ui.btn_saveRefinementModel.clicked.connect(lambda: self.commandDispatcher('SaveRefinementModel'))
        self.app.ui.btn_loadRefinementModel.clicked.connect(lambda: self.commandDispatcher('LoadRefinementModel'))
        self.app.ui.btn_saveBaseModel.clicked.connect(lambda: self.commandDispatcher('SaveBaseModel'))
        self.app.ui.btn_loadBaseModel.clicked.connect(lambda: self.commandDispatcher('LoadBaseModel'))
        self.app.ui.btn_saveDSO1Model.clicked.connect(lambda: self.commandDispatcher('SaveDSO1Model'))
        self.app.ui.btn_loadDSO1Model.clicked.connect(lambda: self.commandDispatcher('LoadDSO1Model'))
        self.app.ui.btn_saveDSO2Model.clicked.connect(lambda: self.commandDispatcher('SaveDSO2Model'))
        self.app.ui.btn_loadDSO2Model.clicked.connect(lambda: self.commandDispatcher('LoadDSO2Model'))
        self.app.ui.btn_mountShutdown.clicked.connect(lambda: self.commandDispatcher('Shutdown'))
        self.app.ui.btn_clearAlignmentModel.clicked.connect(lambda: self.commandDispatcher('ClearAlign'))
        while self.isRunning:
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        # stopping all interaction
        self.workerMountCommandRunner.stop()
        self.workerGetAlignmentModel.stop()
        self.workerMountStatusRunnerOnce.stop()
        self.workerMountStatusRunnerSlow.stop()
        self.workerMountStatusRunnerMedium.stop()
        self.workerMountStatusRunnerFast.stop()
        self.finished.emit()

    def commandDispatcher(self, command):
        # if we have a command in dispatcher
        if command in self.commandDispatch:
            # running through all necessary commands
            for work in self.commandDispatch[command]['Worker']:
                # if we want to color a button, which one
                if 'Button' in work:
                    work['Button'].setProperty('running', True)
                    work['Button'].style().unpolish(work['Button'])
                    work['Button'].style().polish(work['Button'])
                if 'Parameter' in work:
                    parameter = []
                    for p in work['Parameter']:
                        parameter.append(p)
                    work['Method'](*parameter)
                else:
                    work['Method']()
                time.sleep(0.2)
                if 'Button' in work:
                    work['Button'].setProperty('running', False)
                    work['Button'].style().unpolish(work['Button'])
                    work['Button'].style().polish(work['Button'])
                if 'Cancel' in work:
                    work['Cancel'].setProperty('cancel', False)
                    work['Cancel'].style().unpolish(work['Cancel'])
                    work['Cancel'].style().polish(work['Cancel'])
                PyQt5.QtWidgets.QApplication.processEvents()

    def mountShutdown(self):
        reply = self.workerMountCommandRunner.sendCommand(':shutdown#')
        if reply == '1':
            self.workerMountCommandRunner.connected = False
            time.sleep(1)
            self.logger.info('Shutdown mount manually')
            self.app.messageQueue.put('Shutting mount down !\n')
        else:
            self.logger.error('error: {0}'.format(reply))
            self.app.messageQueue.put('#BRError in mount shutdown\n')

    def flipMount(self):
        reply = self.workerMountCommandRunner.sendCommand(':FLIP#').rstrip('#').strip()
        if reply == '0':
            self.app.messageQueue.put('#BRFlip Mount could not be executed\n')
            self.logger.error('error: {0}'.format(reply))

    def syncMountModel(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.workerMountCommandRunner.sendCommand(':Sr{0}#'.format(ra))
        self.workerMountCommandRunner.sendCommand(':Sd{0}#'.format(dec))
        self.workerMountCommandRunner.sendCommand(':CMCFG0#')
        # send sync command
        reply = self.workerMountCommandRunner.sendCommand(':CM#')
        if reply[:5] == 'Coord':
            self.logger.info('mount modeling synced')
            return True
        else:
            self.logger.warning('error in sync mount modeling')
            return False

    def addRefinementStar(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.workerMountCommandRunner.sendCommand(':Sr{0}#'.format(ra))
        self.workerMountCommandRunner.sendCommand(':Sd{0}#'.format(dec))
        starNumber = self.numberModelStars()
        reply = self.workerMountCommandRunner.sendCommand(':CMS#')
        starAdded = self.numberModelStars() - starNumber
        if reply == 'E':
            # 'E' says star could not be added
            if starAdded == 1:
                self.logger.error('star added, but return value was E')
                return True
            else:
                self.logger.error('error adding star')
                return False
        else:
            self.logger.info('refinement star added')
            return True

    def programBatchData(self, data):
        self.saveBackupModel()
        self.workerMountCommandRunner.sendCommand(':newalig#')
        for i in range(0, len(data['Index'])):
            command = 'newalpt{0},{1},{2},{3},{4},{5}'.format(self.transform.decimalToDegree(data['RaJNow'][i], False, True),
                                                              self.transform.decimalToDegree(data['DecJNow'][i], True, False),
                                                              data['Pierside'][i],
                                                              self.transform.decimalToDegree(data['RaJNowSolved'][i], False, True),
                                                              self.transform.decimalToDegree(data['DecJNowSolved'][i], True, False),
                                                              self.transform.decimalToDegree(data['LocalSiderealTimeFloat'][i], False, True))
            reply = self.app.mount.mountHandler.sendCommand(command)
            if reply == 'E':
                self.logger.warning('point {0} could not be added'.format(reply))
        reply = self.workerMountCommandRunner.sendCommand(':endalig#')
        if reply == 'V':
            self.logger.info('Model successful finished!')
        else:
            self.logger.warning('Model could not be calculated with current data!')

    def runTargetRMSAlignment(self):
        self.runTargetRMS = True
        self.cancelRunTargetRMS = False
        if 'Number' not in self.data:
            return
        if self.data['Number'] < 4:
            return
        while self.data['RMS'] > float(self.app.ui.targetRMS.value()) and not self.cancelRunTargetRMS:
            if self.deleteWorstPoint():
                break
        if self.cancelRunTargetRMS:
            self.app.messageQueue.put('#BRTarget RMS Run canceled\n')
        else:
            self.app.messageQueue.put('#BWTarget RMS Run finished\n')
        self.runTargetRMS = False

    def cancelRunTargetRMSFunction(self):
        if self.runTargetRMS:
            self.app.ui.btn_cancelRunTargetRMSAlignment.setProperty('cancel', True)
            self.app.ui.btn_cancelRunTargetRMSAlignment.style().unpolish(self.app.ui.btn_cancelRunTargetRMSAlignment)
            self.app.ui.btn_cancelRunTargetRMSAlignment.style().polish(self.app.ui.btn_cancelRunTargetRMSAlignment)
            self.cancelRunTargetRMS = True

    def deleteWorstPoint(self):
        # if there are less than 4 point, optimization can't take place
        if self.data['Number'] < 4:
            return True
        # find worst point
        maxError = 0
        worstPointIndex = 0
        for i in range(0, self.data['Number']):
            if self.data['ModelError'][i] > maxError:
                worstPointIndex = i
                maxError = self.data['ModelError'][i]
        self.app.messageQueue.put('Deleting Point {0:02d}  -> Az: {1:05.1f}  Alt: {2:04.1f}  Err: {3:05.1f} ...'.format(worstPointIndex + 1,
                                                                                                                        self.data['ModelAzimuth'][worstPointIndex],
                                                                                                                        self.data['ModelAltitude'][worstPointIndex],
                                                                                                                        maxError))
        reply = self.workerMountCommandRunner.sendCommand(':delalst{0:d}#'.format(worstPointIndex + 1))
        time.sleep(0.2)
        if reply == '1':
            # point could be deleted, feedback from mount ok
            self.logger.info('Deleting Point {0} with Error: {1}'.format(worstPointIndex+1, maxError))
            # get new calculated alignment model from mount
            self.app.messageQueue.put('\n')
        else:
            self.app.messageQueue.put(' Point could not be deleted \n')
            self.logger.warning('Point {0} could not be deleted'.format(worstPointIndex))
        self.workerMountGetAlignmentModel.getAlignmentModel()
        # wait form alignment model to be downloaded
        while self.data['ModelLoading']:
            time.sleep(0.2)
        return False
