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
from mount import mountStatusRunner
# astrometry
from astrometry import transform
from mount import mountModelHandling
from analyse import analysedata


class Mount(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)
    signalMountConnected = PyQt5.QtCore.pyqtSignal([bool], name='mountConnected')
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal([float, float], name='mountAzAltPointer')
    signalMountTrackPreview = PyQt5.QtCore.pyqtSignal(name='mountTrackPreview')

    BLIND_COMMANDS = ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']
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

        self.mountIpDirect = ipdirect.MountIpDirect(self.app)
        self.mountModelHandling = mountModelHandling.MountModelHandling(self.app)
        self.analyse = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)

        self.workerMountStatusRunner = mountStatusRunner.MountStatusRunner(self, self.app)
        self.threadMountStatusRunner = PyQt5.QtCore.QThread()
        self.threadMountStatusRunner.setObjectName("MountStatusRunner")
        self.workerMountStatusRunner.moveToThread(self.threadMountStatusRunner)
        # noinspection PyUnresolvedReferences
        self.threadMountStatusRunner.started.connect(self.workerMountStatusRunner.run)
        self.workerMountStatusRunner.finished.connect(self.workerMountStatusRunnerStop)

        self.data = {}
        self.site_lat = '49'
        self.site_lon = '0'
        self.site_height = '0'
        self.sidereal_time = ''
        self.counter = 0
        self.cancelTargetRMS = False

    def initConfig(self):
        try:
            if 'CheckAutoRefractionCamera' in self.app.config:
                self.app.ui.checkAutoRefractionCamera.setChecked(self.app.config['CheckAutoRefractionCamera'])
            if 'CheckAutoRefractionNotTracking' in self.app.config:
                self.app.ui.checkAutoRefractionNotTracking.setChecked(self.app.config['CheckAutoRefractionNotTracking'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.mountIpDirect.initConfig()
        self.workerMountStatusRunner.initConfig()

    def storeConfig(self):
        self.app.config['CheckAutoRefractionCamera'] = self.app.ui.checkAutoRefractionCamera.isChecked()
        self.app.config['CheckAutoRefractionNotTracking'] = self.app.ui.checkAutoRefractionNotTracking.isChecked()
        self.mountIpDirect.storeConfig()
        self.workerMountStatusRunner.storeConfig()

    def workerMountStatusRunnerStop(self):
        self.threadMountStatusRunner.quit()
        self.threadMountStatusRunner.wait()

    def run(self):
        self.counter = 0
        self.threadMountStatusRunner.start()
        while True:
            self.signalMountConnected.emit(self.mountIpDirect.connected)
            if self.mountIpDirect.connected:
                if not self.app.mountCommandQueue.empty():
                    command = self.app.mountCommandQueue.get()
                    if command == 'ShowAlignmentModel':
                        num = self.numberModelStars()
                        if num == -1:
                            self.app.messageQueue.put('#BRShow Model not available in simulation mode\n')
                        else:
                            self.app.ui.btn_showActualModel.setStyleSheet(self.app.BLUE)
                            self.showAlignmentModel(self.getAlignmentModel())
                            self.app.ui.btn_showActualModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'ClearAlign':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('#BRClear Align not available in simulation mode\n')
                        else:
                            self.mountIpDirect.sendCommand('delalig')
                    elif command == 'RunTargetRMSAlignment':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('#BRRun Optimize not available in simulation mode\n')
                        else:
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.app.BLUE)
                            self.runTargetRMSAlignment()
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.app.DEFAULT)
                        self.app.ui.btn_cancelRunTargetRMSAlignment.setStyleSheet(self.app.DEFAULT)
                    elif command == 'DeleteWorstPoint':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('#BRDelete worst point not available in simulation mode\n')
                        else:
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
                        self.setupAlignmentModel()
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
                self.counter += 1
            else:
                self.mountIpDirect.connect()
                self.counter = 0
                time.sleep(1)
        self.mountIpDirect.disconnect()

    def mountShutdown(self):
        reply = self.mountIpDirect.sendCommand('shutdown')
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
        reply = self.mountIpDirect.sendCommand('FLIP').rstrip('#').strip()
        if reply == '0':
            self.app.messageQueue.put('#BRFlip Mount could not be executed\n')
            self.logger.error('error: {0}'.format(reply))

    def syncMountModel(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.mountIpDirect.sendCommand('Sr{0}'.format(ra))
        self.mountIpDirect.sendCommand('Sd{0}'.format(dec))
        self.mountIpDirect.sendCommand('CMCFG0')
        # send sync command
        reply = self.mountIpDirect.sendCommand('CM')
        if reply[:5] == 'Coord':
            self.logger.info('mount modeling synced')
            return True
        else:
            self.logger.warning('error in sync mount modeling')
            return False

    def addRefinementStar(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.mountIpDirect.sendCommand('Sr{0}'.format(ra))
        self.mountIpDirect.sendCommand('Sd{0}'.format(dec))
        starNumber = self.numberModelStars()
        reply = self.mountIpDirect.sendCommand('CMS')
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
        self.mountIpDirect.sendCommand('newalig')
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
        reply = self.mountIpDirect.sendCommand('endalig')
        if reply == 'V':
            self.logger.info('Model successful finished!')
        else:
            self.logger.warning('Model could not be calculated with current data!')

    def numberModelStars(self):
        return int(self.mountIpDirect.sendCommand('getalst'))

    def getAlignmentModelStatus(self, alignModel):
        if self.data['FW'] < 21500:
            return alignModel
        try:
            reply = self.mountIpDirect.sendCommand('getain')
            # there should be a reply, format string is "ZZZ.ZZZZ,+AA.AAAA,EE.EEEE,PPP.PP,+OO.OOOO,+aa.aa, +bb.bb,NN,RRRRR.R#"
            if reply:
                # if a single 'E' returns, there is a problem, not further parameter will follow
                if reply != 'E':
                    a1, a2, a3, a4, a5, a6, a7, a8, a9 = reply.split(',')
                    # 'E' could be sent if not calculable or no value available
                    if a1 != 'E':
                        alignModel['ModelErrorAzimuth'] = float(a1)
                    else:
                        alignModel['ModelErrorAzimuth'] = 0
                    if a2 != 'E':
                        alignModel['ModelErrorAltitude'] = float(a2)
                    else:
                        alignModel['ModelErrorAltitude'] = 0
                    if a3 != 'E':
                        alignModel['PolarError'] = float(a3)
                    else:
                        alignModel['PolarError'] = 0
                    if a4 != 'E':
                        alignModel['PosAngle'] = float(a4)
                    else:
                        alignModel['PosAngle'] = 0
                    if a5 != 'E':
                        alignModel['OrthoError'] = float(a5)
                    else:
                        alignModel['OrthoError'] = 0
                    if a6 != 'E':
                        alignModel['AzimuthKnobs'] = float(a6)
                    else:
                        alignModel['AzimuthKnobs'] = 0
                    if a7 != 'E':
                        alignModel['AltitudeKnobs'] = float(a7)
                    else:
                        alignModel['AltitudeKnobs'] = 0
                    if a8 != 'E':
                        alignModel['Terms'] = int(float(a8))
                    else:
                        alignModel['Terms'] = 0
                    if a9 != 'E':
                        alignModel['RMS'] = float(a9)
                    else:
                        alignModel['RMS'] = 0
        except Exception as e:
            self.logger.error('Receive error getain command: {0}'.format(e))
        finally:
            return alignModel

    def getAlignmentModel(self):
        alignModel = {'ModelErrorAzimuth': 0.0,
                      'ModelErrorAltitude': 0.0,
                      'PolarError': 0.0,
                      'PosAngle': 0.0,
                      'OrthoError': 0.0,
                      'AzimuthKnobs': 0.0,
                      'AltitudeKnobs': 0.0,
                      'Terms': 0,
                      'RMS': 0.0,
                      'Index': [],
                      'Azimuth': [],
                      'Altitude': [],
                      'ModelError': [],
                      'ModelErrorAngle': []}
        numberStars = self.numberModelStars()
        alignModel['Number'] = numberStars
        if numberStars < 1:
            return alignModel
        alignModel = self.getAlignmentModelStatus(alignModel)
        self.app.messageQueue.put('Downloading Alignment Model from Mount\n')
        for i in range(1, numberStars + 1):
            reply = self.mountIpDirect.sendCommand('getalp{0:d}'.format(i)).split(',')
            ha = reply[0].strip().split('.')[0]
            dec = reply[1].strip().split('.')[0]
            ErrorRMS = float(reply[2].strip())
            ErrorAngle = float(reply[3].strip().rstrip('#'))
            dec = dec.replace('*', ':')
            RaJNow = self.transform.degStringToDecimal(ha)
            DecJNow = self.transform.degStringToDecimal(dec)
            az, alt = self.transform.ra_dec_lst_to_az_alt(RaJNow, DecJNow)
            # index should start with 0, but numbering in mount starts with 1
            alignModel['Index'].append(i - 1)
            alignModel['Azimuth'].append(az)
            alignModel['Altitude'].append(alt)
            alignModel['ModelError'].append(ErrorRMS)
            alignModel['ModelErrorAngle'].append(ErrorAngle)
            self.app.messageQueue.put('#{0:02d}   AZ: {1:3f}   Alt: {2:3f}   Err: {3:4.1f}\x22   PA: {4:3.0f}\xb0\n'.format(i, az, alt, ErrorRMS, ErrorAngle))
        self.app.messageQueue.put('Alignment Model from Mount downloaded\n')
        return alignModel

    def retrofitMountData(self, data):
        num = self.numberModelStars()
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

    def showAlignmentModel(self, alignModel):
        self.data['NumberAlignmentStars'] = alignModel['Number']
        self.data['ModelRMSError'] = '{0:3.1f}'.format(alignModel['RMS'])
        self.data['ModelErrorPosAngle'] = '{0:3.1f}'.format(alignModel['PosAngle'])
        self.data['ModelPolarError'] = '{0}'.format(self.transform.decimalToDegree(alignModel['PolarError']))
        self.data['ModelOrthoError'] = '{0}'.format(self.transform.decimalToDegree(alignModel['OrthoError']))
        self.data['ModelErrorAz'] = '{0}'.format(self.transform.decimalToDegree(alignModel['ModelErrorAzimuth']))
        self.data['ModelErrorAlt'] = '{0}'.format(self.transform.decimalToDegree(alignModel['ModelErrorAltitude']))
        self.data['ModelTerms'] = '{0:2d}'.format(alignModel['Terms'])
        if alignModel['AzimuthKnobs'] > 0:
            value = '{0:2.2f} left'.format(abs(alignModel['AzimuthKnobs']))
        else:
            value = '{0:2.2f} right'.format(abs(alignModel['AzimuthKnobs']))
        self.data['ModelKnobTurnAz'] = '{0}'.format(value)
        if alignModel['AltitudeKnobs'] > 0:
            value = '{0:2.2f} down'.format(abs(alignModel['AltitudeKnobs']))
        else:
            value = '{0:2.2f} up'.format(abs(alignModel['AltitudeKnobs']))
        self.data['ModelKnobTurnAlt'] = '{0}'.format(value)
        self.app.showModelErrorPolar(alignModel)

    def runTargetRMSAlignment(self):
        self.cancelTargetRMS = False
        alignModel = self.getAlignmentModel()
        if alignModel['Number'] < 4:
            return
        while alignModel['RMS'] > float(self.app.ui.targetRMS.value()) and alignModel['Number'] > 3 and not self.cancelTargetRMS:
            alignModel = self.deleteWorstPointRaw(alignModel)

    def cancelRunTargetRMS(self):
        self.app.ui.btn_cancelRunTargetRMSAlignment.setStyleSheet(self.app.RED)
        self.cancelTargetRMS = True

    def deleteWorstPoint(self):
        alignModel = self.getAlignmentModel()
        self.deleteWorstPointRaw(alignModel)

    def deleteWorstPointRaw(self, alignModel):
        # if there are less than 4 point, optimization can't take place
        if alignModel['Number'] < 4:
            return
        # find worst point
        maxError = 0
        worstPointIndex = 0
        for i in range(0, alignModel['Number']):
            if alignModel['ModelError'][i] > maxError:
                worstPointIndex = i
                maxError = alignModel['ModelError'][i]
        reply = self.mountIpDirect.sendCommand('delalst{0:d}'.format(worstPointIndex + 1))
        if reply == '1':
            # point could be deleted, feedback from mount ok
            self.logger.info('Point {0} deleted'.format(worstPointIndex))
            # get new calculated alignment model from mount
            alignModel = self.getAlignmentModel()
            # if data set is there, than delete this point as well
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.workerModelingDispatcher.modelingRunner.modelData.pop(worstPointIndex)
                # update the rest of point with the new error vectors
                for i in range(0, alignModel['Number']):
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] = alignModel['ModelError'][i]
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['RaError'] = self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] * math.sin(math.radians(alignModel['ModelErrorAngle'][i]))
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['DecError'] = self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] * math.cos(math.radians(alignModel['ModelErrorAngle'][i]))
            self.showAlignmentModel(alignModel)
        else:
            self.logger.warning('Point {0} could not be deleted').format(worstPointIndex)
        return alignModel

    def setupAlignmentModel(self):
        # first try to load the actual model, which was used the last time MW was run
        self.mountModelHandling.loadActualModel()
        alignModel = self.getAlignmentModel()
        # if there was no data set stored, i try to reconstruct the data from the model stored in mount
        if not self.app.workerModelingDispatcher.modelingRunner.modelData and alignModel['Number'] > 0:
            self.app.messageQueue.put('Model Data will be reconstructed from Mount Data\n')
            self.app.workerModeling.modelData = []
            for i in range(0, alignModel['Number']):
                self.app.workerModelingDispatcher.modelingRunner.modelData.append({'ModelError': float(alignModel['Points'][i][5]),
                                                                                   'RaError': float(alignModel['Points'][i][5]) * math.sin(math.radians(alignModel['Points'][i][6])),
                                                                                   'DecError': float(alignModel['Points'][i][5]) * math.cos(math.radians(alignModel['Points'][i][6])),
                                                                                   'Azimuth': float(alignModel['Points'][i][3]),
                                                                                   'Altitude': float(alignModel['Points'][i][4])})
        self.showAlignmentModel(alignModel)

