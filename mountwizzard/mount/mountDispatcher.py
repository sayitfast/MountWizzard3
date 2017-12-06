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
from mount import ipdirect
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


class Mount(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)
    signalMountConnected = PyQt5.QtCore.pyqtSignal([bool])
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal([float, float])
    signalMountTrackPreview = PyQt5.QtCore.pyqtSignal()
    signalMountShowAlignmentModel = PyQt5.QtCore.pyqtSignal()

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

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.data = {
            'SiteLatitude': '49:00:00',
            'SiteLongitude': '01:00:00',
            'SiteHeight': '1',
            'MountIP': '',
            'MountMAC': '',
            'MountPort': 3490,
            'LocalSiderealTime': '',
            'FW': 21501
        }

        # getting all supporting classes assigned
        self.mountIpDirect = ipdirect.MountIpDirect(self.app, self.data)
        self.mountModelHandling = mountModelHandling.MountModelHandling(self.app, self.data)
        self.analyse = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)
        self.checkIP = checkParamIP.CheckIP()

        # getting all threads setup
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
        # stopping all interaction
        self.mountIpDirect.disconnect()
        self.workerGetAlignmentModel.stop()
        self.workerMountStatusRunnerOnce.stop()
        self.workerMountStatusRunnerSlow.stop()
        self.workerMountStatusRunnerMedium.stop()
        self.workerMountStatusRunnerFast.stop()
        # setting new values
        self.setIP()
        self.setMAC()
        # starting new communication
        self.mountIpDirect.connect()
        self.threadGetAlignmentModel.start()
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

    def workerMountGetAlignmentModelStop(self):
        self.threadMountGetAlignmentModel.quit()
        self.threadMountGetAlignmentModel.wait()

    def run(self):
        self.counter = 0
        self.threadMountGetAlignmentModel.start()
        self.threadMountStatusRunnerOnce.start()
        self.threadMountStatusRunnerSlow.start()
        self.threadMountStatusRunnerMedium.start()
        self.threadMountStatusRunnerFast.start()
        while True:
            self.signalMountConnected.emit(self.mountIpDirect.connected)
            if self.mountIpDirect.connected:
                if not self.app.mountCommandQueue.empty():
                    command = self.app.mountCommandQueue.get()
                    if command == 'ClearAlign':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('#BRClear Align not available in simulation mode\n')
                        else:
                            self.mountIpDirect.sendCommand(':delalig#')
                    elif command == 'RunTargetRMSAlignment':
                        self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.app.BLUE)
                        self.runTargetRMSAlignment()
                        self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.app.DEFAULT)
                        self.app.ui.btn_cancelRunTargetRMSAlignment.setStyleSheet(self.app.DEFAULT)
                    elif command == 'DeleteWorstPoint':
                        self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.app.BLUE)
                        self.deleteWorstPoint()
                        self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveBackupModel':
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.saveBackupModel()
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadBackupModel':
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.loadBackupModel()
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadBaseModel':
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.loadBaseModel()
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveBaseModel':
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.saveBaseModel()
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadRefinementModel':
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.loadRefinementModel()
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveRefinementModel':
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.saveRefinementModel()
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadSimpleModel':
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.loadSimpleModel()
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveSimpleModel':
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.saveSimpleModel()
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadDSO1Model':
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.loadDSO1Model()
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveDSO1Model':
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.saveDSO1Model()
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadDSO2Model':
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.loadDSO2Model()
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveDSO2Model':
                        self.app.ui.btn_saveDSO2Model.setStyleSheet(self.app.BLUE)
                        self.mountModelHandling.saveDSO2Model()
                        self.app.ui.btn_saveDSO2Model.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SetRefractionParameter':
                        self.setRefractionParam()
                    elif command == 'FLIP':
                        self.flipMount()
                    elif command == 'SetupAscomDriver':
                        self.MountAscom.setupDriver()
                    elif command == 'Shutdown':
                        self.mountShutdown()
                    else:
                        self.mountIpDirect.sendCommand(command)
                    self.app.mountCommandQueue.task_done()
                else:
                    if self.counter == 0:
                        pass
                        # self.setupAlignmentModel()
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
                self.counter += 1
            else:
                self.mountIpDirect.connect()
                self.counter = 0
                time.sleep(1)
        self.mountIpDirect.disconnect()

    def mountShutdown(self):
        reply = self.mountIpDirect.sendCommand(':shutdown#')
        if reply != '1':
            self.logger.error('error: {0}'.format(reply))
            self.app.messageQueue.put('#BRError in mount shutdown\n')
        else:
            self.mountIpDirect.connected = False
            time.sleep(1)
            self.mountIpDirect.disconnect()
            self.logger.info('Shutdown mount manually')
            self.app.messageQueue.put('Shutting mount down !')

    def flipMount(self):
        reply = self.mountIpDirect.sendCommand(':FLIP#').rstrip('#').strip()
        if reply == '0':
            self.app.messageQueue.put('#BRFlip Mount could not be executed\n')
            self.logger.error('error: {0}'.format(reply))

    def syncMountModel(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.mountIpDirect.sendCommand(':Sr{0}#'.format(ra))
        self.mountIpDirect.sendCommand(':Sd{0}#'.format(dec))
        self.mountIpDirect.sendCommand(':CMCFG0#')
        # send sync command
        reply = self.mountIpDirect.sendCommand(':CM#')
        if reply[:5] == 'Coord':
            self.logger.info('mount modeling synced')
            return True
        else:
            self.logger.warning('error in sync mount modeling')
            return False

    def addRefinementStar(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.mountIpDirect.sendCommand(':Sr{0}#'.format(ra))
        self.mountIpDirect.sendCommand(':Sd{0}#'.format(dec))
        starNumber = self.numberModelStars()
        reply = self.mountIpDirect.sendCommand(':CMS#')
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
        self.mountIpDirect.sendCommand(':newalig#')
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
        reply = self.mountIpDirect.sendCommand(':endalig#')
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
        reply = self.mountIpDirect.sendCommand(':delalst{0:d}#'.format(worstPointIndex + 1))
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
