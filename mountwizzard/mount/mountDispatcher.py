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
import math
# import basic stuff
import time
# import PyQT5 for threading purpose
import PyQt5
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
    signalMountConnected = PyQt5.QtCore.pyqtSignal([bool])
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal([float, float])
    signalMountTrackPreview = PyQt5.QtCore.pyqtSignal()
    signalMountShowAlignmentModel = PyQt5.QtCore.pyqtSignal()

    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red;'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'

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
        'FW': 21501
    }

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        # getting all supporting classes assigned
        self.mountModelHandling = mountModelHandling.MountModelHandling(self.app, self.data)
        self.analyse = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)
        self.checkIP = checkParamIP.CheckIP()
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
                            'Method': self.clearAlign
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
                            'Method': self.mountModelHandling.saveBackupModel,
                        }
                    ]
                },
            'LoadBackupModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadBackupModel,
                            'Method': self.mountModelHandling.loadBackupModel,
                        }
                    ]
                },
            'LoadBaseModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadBaseModel,
                            'Method': self.mountModelHandling.loadBaseModel,
                        }
                    ]
                },
            'SaveBaseModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveBaseModel,
                            'Method': self.mountModelHandling.saveBaseModel,
                        }
                    ]
                },
            'LoadRefinementModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadRefinementModel,
                            'Method': self.mountModelHandling.loadRefinementModel,
                        }
                    ]
                },
            'SaveRefinementModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveRefinementModel,
                            'Method': self.mountModelHandling.saveRefinementModel,
                        }
                    ]
                },
            'LoadSimpleModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadSimpleModel,
                            'Method': self.mountModelHandling.loadSimpleModel,
                        }
                    ]
                },
            'SaveSimpleModel':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveSimpleModel,
                            'Method': self.mountModelHandling.saveSimpleModel,
                        }
                    ]
                },
            'LoadDSO1Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadDSO1Model,
                            'Method': self.mountModelHandling.loadDSO1Model,
                        }
                    ]
                },
            'SaveDSO1Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveDSO1Model,
                            'Method': self.mountModelHandling.saveDSO1Model,
                        }
                    ]
                },
            'LoadDSO2Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_loadDSO2Model,
                            'Method': self.mountModelHandling.loadDSO2Model,
                        }
                    ]
                },
            'SaveDSO2Model':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_saveDSO2Model,
                            'Method': self.mountModelHandling.saveDSO2Model,
                        }
                    ]
                },
            '''
            'SetRefractionParameter':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_setRefractionParameters,
                            'Method': self.setRefractionParam,
                        }
                    ]
                },
            '''
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
        # getting all threads setup
        # commands sending thread
        self.workerMountCommandRunner = mountCommandRunner.MountCommandRunner(self.app, self.data)
        self.threadMountCommandRunner = PyQt5.QtCore.QThread()
        self.threadMountCommandRunner.setObjectName("MountCommandRunner")
        self.workerMountCommandRunner.moveToThread(self.threadMountCommandRunner)
        self.threadMountCommandRunner.started.connect(self.workerMountCommandRunner.run)
        self.workerMountCommandRunner.finished.connect(self.workerMountCommandRunnerStop)
        # fast status thread
        self.workerMountStatusRunnerFast = mountStatusRunnerFast.MountStatusRunnerFast(self.app, self.data, self.signalMountAzAltPointer)
        self.threadMountStatusRunnerFast = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerFast.setObjectName("MountStatusRunnerFast")
        self.workerMountStatusRunnerFast.moveToThread(self.threadMountStatusRunnerFast)
        self.threadMountStatusRunnerFast.started.connect(self.workerMountStatusRunnerFast.run)
        self.workerMountStatusRunnerFast.finished.connect(self.workerMountStatusRunnerFastStop)
        # medium status thread
        self.workerMountStatusRunnerMedium = mountStatusRunnerMedium.MountStatusRunnerMedium(self.app, self.data, self.signalMountTrackPreview)
        self.threadMountStatusRunnerMedium = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerMedium.setObjectName("MountStatusRunnerMedium")
        self.workerMountStatusRunnerMedium.moveToThread(self.threadMountStatusRunnerMedium)
        self.threadMountStatusRunnerMedium.started.connect(self.workerMountStatusRunnerMedium.run)
        self.workerMountStatusRunnerMedium.finished.connect(self.workerMountStatusRunnerMediumStop)
        # slow status thread
        self.workerMountStatusRunnerSlow = mountStatusRunnerSlow.MountStatusRunnerSlow(self.app, self.data)
        self.threadMountStatusRunnerSlow = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerSlow.setObjectName("MountStatusRunnerSlow")
        self.workerMountStatusRunnerSlow.moveToThread(self.threadMountStatusRunnerSlow)
        self.threadMountStatusRunnerSlow.started.connect(self.workerMountStatusRunnerSlow.run)
        self.workerMountStatusRunnerSlow.finished.connect(self.workerMountStatusRunnerSlowStop)
        # once status thread
        self.workerMountStatusRunnerOnce = mountStatusRunnerOnce.MountStatusRunnerOnce(self.app, self.data)
        self.threadMountStatusRunnerOnce = PyQt5.QtCore.QThread()
        self.threadMountStatusRunnerOnce.setObjectName("MountStatusRunnerOnce")
        self.workerMountStatusRunnerOnce.moveToThread(self.threadMountStatusRunnerOnce)
        self.threadMountStatusRunnerOnce.started.connect(self.workerMountStatusRunnerOnce.run)
        self.workerMountStatusRunnerOnce.finished.connect(self.workerMountStatusRunnerOnceStop)
        # get alignment model
        self.workerMountGetAlignmentModel = mountGetAlignmentModel.MountGetAlignmentModel(self.app, self.data, self.signalMountShowAlignmentModel)
        self.threadMountGetAlignmentModel = PyQt5.QtCore.QThread()
        self.threadMountGetAlignmentModel.setObjectName("MountGetAlignmentModel")
        self.workerMountGetAlignmentModel.moveToThread(self.threadMountGetAlignmentModel)
        self.threadMountGetAlignmentModel.started.connect(self.workerMountGetAlignmentModel.run)
        self.workerMountGetAlignmentModel.finished.connect(self.workerMountGetAlignmentModelStop)

        self.counter = 0
        self.cancelTargetRMS = False

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
        return
        # stopping all interaction
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
        self.signalMountConnected.emit(False)
        self.threadMountGetAlignmentModel.start()
        self.threadMountCommandRunner.start()
        self.threadMountStatusRunnerOnce.start()
        self.threadMountStatusRunnerSlow.start()
        self.threadMountStatusRunnerMedium.start()
        self.threadMountStatusRunnerFast.start()

        # self.app.ui.btn_setRefractionCorrection.clicked.connect(self.commandDispatcher('SetRefractionParameter'))
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
        self.workerMountGetAlignmentModel.getAlignmentModel()
        while self.isRunning:
            self.signalMountConnected.emit(self.workerMountStatusRunnerFast.connected)
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
                    work['Button'].setStyleSheet(self.BLUE)
                if 'Parameter' in work:
                    parameter = []
                    for p in work['Parameter']:
                        parameter.append(eval(p))
                    work['Method'](*parameter)
                else:
                    work['Method']()
                time.sleep(0.2)
                if 'Button' in work:
                    work['Button'].setStyleSheet(self.DEFAULT)
                if 'Cancel' in work:
                    work['Cancel'].setStyleSheet(self.DEFAULT)
                PyQt5.QtWidgets.QApplication.processEvents()

    def mountShutdown(self):
        reply = self.workerMountCommandRunner.sendCommand(':shutdown#')
        if reply != '1':
            self.logger.error('error: {0}'.format(reply))
            self.app.messageQueue.put('#BRError in mount shutdown\n')
        else:
            self.workerMountCommandRunner.connected = False
            time.sleep(1)
            self.workerMountCommandRunner.disconnect()
            self.logger.info('Shutdown mount manually')
            self.app.messageQueue.put('Shutting mount down !')

    def clearAlign(self):
        self.workerMountCommandRunner.sendCommand(':delalig#')

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

    def retrofitMountData(self, data):
        num = self.data['Number']
        if num == len(data):
            alignModel = self.getAlignmentModel()
            self.showAlignmentModel(alignModel)
            for i in range(0, alignModel['Number']):
                data[i]['ModelError'] = alignModel['ModelError'][i]
                data[i]['RaError'] = data[i]['ModelError'] * math.sin(math.radians(alignModel['ModelErrorAngle'][i]))
                data[i]['DecError'] = data[i]['ModelError'] * math.cos(math.radians(alignModel['ModelErrorAngle'][i]))
            self.app.messageQueue.put('Mount Model and Model Data synced\n')
        else:
            self.logger.warning('Size of mount data {0} and modeling data {1} do not fit !'.format(num, len(data)))
            self.app.messageQueue.put('Mount Data and Model Data could not be synced\n')
            self.app.messageQueue.put('#BRMount Data and Model Data mismatch\n')
        return data

    def runTargetRMSAlignment(self):
        self.cancelTargetRMS = False
        if self.data['Number'] < 4:
            return
        while self.data['RMS'] > float(self.app.ui.targetRMS.value()) and not self.cancelTargetRMS:
            self.deleteWorstPointRaw()

    def cancelRunTargetRMS(self):
        self.app.ui.btn_cancelRunTargetRMSAlignment.setStyleSheet(self.app.RED)
        self.cancelTargetRMS = True

    def deleteWorstPoint(self):
        self.deleteWorstPointRaw()

    def deleteWorstPointRaw(self):
        # if there are less than 4 point, optimization can't take place
        if self.data['Number'] < 4:
            self.cancelTargetRMS = True
            return
        # find worst point
        maxError = 0
        worstPointIndex = 0
        for i in range(0, self.data['Number']):
            if self.data['ModelError'][i] > maxError:
                worstPointIndex = i
                maxError = self.data['ModelError'][i]
        self.app.messageQueue.put('Deleting Point {0:02d}  with Error: {1} ...'.format(worstPointIndex + 1, maxError))
        reply = self.workerMountCommandRunner.sendCommand(':delalst{0:d}#'.format(worstPointIndex + 1))
        if reply == '1':
            # point could be deleted, feedback from mount ok
            self.logger.info('Deleting Point {0} with Error: {1}'.format(worstPointIndex+1, maxError))
            # get new calculated alignment model from mount
            self.workerMountGetAlignmentModel.getAlignmentModel()
            # wait form alignment model to be downloaded
            while self.data['ModelLoading']:
                time.sleep(0.2)
            self.app.messageQueue.put(' Point deleted \n')
            # if data set is there, than delete this point as well
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.workerModelingDispatcher.modelingRunner.modelData.pop(worstPointIndex)
                # update the rest of point with the new error vectors
                for i in range(0, self.data['Number']):
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] = self.data['ModelError'][i]
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['RaError'] = self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] * math.sin(math.radians(self.data['ModelErrorAngle'][i]))
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['DecError'] = self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] * math.cos(math.radians(self.data['ModelErrorAngle'][i]))
        else:
            self.logger.warning('Point {0} could not be deleted').format(worstPointIndex)
        return

    def setupAlignmentModel(self):
        # first try to load the actual model, which was used the last time MW was run
        self.mountModelHandling.loadActualModel()
        alignModel = self.getAlignmentModel()
        # if there was no data set stored, i try to reconstruct the data from the model stored in mount
        if not self.app.workerModelingDispatcher.modelingRunner.modelData and alignModel['Number'] > 0:
            self.app.messageQueue.put('Model Data will be reconstructed from Mount Data\n')
            self.app.workerModeling.modelData = []
            for i in range(0, alignModel['Number']):
                self.app.workerModelingDispatcher.modelingRunner.modelData.append({
                                                                                      'ModelError': float(alignModel['Points'][i][5]),
                                                                                      'RaError': float(alignModel['Points'][i][5]) * math.sin(math.radians(alignModel['Points'][i][6])),
                                                                                      'DecError': float(alignModel['Points'][i][5]) * math.cos(math.radians(alignModel['Points'][i][6])),
                                                                                      'Azimuth': float(alignModel['Points'][i][3]),
                                                                                      'Altitude': float(alignModel['Points'][i][4])
                                                                                  })
        self.showAlignmentModel(alignModel)
