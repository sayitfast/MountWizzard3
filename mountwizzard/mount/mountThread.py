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
import platform
import threading
import time
# for the sorting
from operator import itemgetter
# import PyQT5 for threading purpose
import PyQt5
if platform.system() == 'Windows':
    # win32com
    import pythoncom
#  mount driver classes
if platform.system() == 'Windows':
    from mount import ascommount
from mount import ipdirect
# astrometry
from astrometry import transform


class Mount(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)
    signalMountConnected = PyQt5.QtCore.pyqtSignal([bool], name='mountConnected')
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal([float, float], name='mountAzAltPointer')
    signalMountTrackPreview = PyQt5.QtCore.pyqtSignal(name='mountTrackPreview')

    BLIND_COMMANDS = ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.data = {}
        if platform.system() == 'Windows':
            self.MountAscom = ascommount.MountAscom(app)
        self.MountIpDirect = ipdirect.MountIpDirect(app)
        self.mountHandler = self.MountIpDirect
        self.transform = transform.Transform(app)
        self.statusReference = {'0': 'Tracking',
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
        self.site_lat = '49'
        self.site_lon = '0'
        self.site_height = '0'
        self.sidereal_time = ''
        self.counter = 0
        self.cancelTargetRMS = False
        self.chooserLock = threading.Lock()
        self.initConfig()

    def initConfig(self):
        self.app.ui.pd_chooseMount.clear()
        self.app.ui.pd_chooseMount.addItem('IP Direct Connection')
        if platform.system() == 'Windows':
            self.app.ui.pd_chooseMount.addItem('ASCOM Driver Connection')
        try:
            if platform.system() == 'Windows':
                if 'ASCOMTelescopeDriverName' in self.app.config:
                    self.MountAscom.driverName = self.app.config['ASCOMTelescopeDriverName']
            if 'MountConnection' in self.app.config:
                self.app.ui.pd_chooseMount.setCurrentIndex(int(self.app.config['MountConnection']))
            if 'CheckAutoRefractionCamera' in self.app.config:
                self.app.ui.checkAutoRefractionCamera.setChecked(self.app.config['CheckAutoRefractionCamera'])
            if 'CheckAutoRefractionNotTracking' in self.app.config:
                self.app.ui.checkAutoRefractionNotTracking.setChecked(self.app.config['CheckAutoRefractionNotTracking'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.app.ui.pd_chooseMount.currentIndexChanged.connect(self.chooseMountConn)

    def storeConfig(self):
        if platform.system() == 'Windows':
            self.app.config['ASCOMTelescopeDriverName'] = self.MountAscom.driverName
        self.app.config['MountConnection'] = self.app.ui.pd_chooseMount.currentIndex()
        self.app.config['CheckAutoRefractionCamera'] = self.app.ui.checkAutoRefractionCamera.isChecked()
        self.app.config['CheckAutoRefractionNotTracking'] = self.app.ui.checkAutoRefractionNotTracking.isChecked()
        self.MountIpDirect.storeConfig()

    def chooseMountConn(self):
        self.chooserLock.acquire()
        if self.mountHandler.connected:
            self.mountHandler.connected = False
            self.mountHandler.disconnect()
        if self.app.ui.pd_chooseMount.currentText().startswith('IP Direct Connection'):
            self.mountHandler = self.MountIpDirect
            self.logger.info('actual driver is IpDirect, IP is: {0}'.format(self.MountIpDirect.mountIP))
        if self.app.ui.pd_chooseMount.currentText().startswith('ASCOM Driver Connection'):
            self.mountHandler = self.MountAscom
            self.logger.info('actual driver is ASCOM')
        self.chooserLock.release()

    def run(self):
        if platform.system() == 'Windows':
            pythoncom.CoInitialize()
        self.chooseMountConn()
        self.counter = 0

        self.loadActualModel()
        alignModel = self.getAlignmentModel()
        if not self.app.workerModelingDispatcher.modelingRunner.modelData and alignModel['RMS'] > 0:
            self.app.messageQueue.put('Model Data will be reconstructed from Mount Data\n')
            self.app.workerModeling.modelData = []
            for i in range(0, alignModel['Number']):
                self.app.workerModelingDispatcher.modelingRunner.modelData.append({'ModelError': float(alignModel['Points'][i][5]),
                                                                                   'RaError': float(alignModel['Points'][i][5]) * math.sin(math.radians(alignModel['Points'][i][6])),
                                                                                   'DecError': float(alignModel['Points'][i][5]) * math.cos(math.radians(alignModel['Points'][i][6])),
                                                                                   'Azimuth': float(alignModel['Points'][i][3]),
                                                                                   'Altitude': float(alignModel['Points'][i][4])})
        self.showAlignmentModel(alignModel)

        while True:
            self.signalMountConnected.emit(self.mountHandler.connected)
            if self.mountHandler.connected:
                if not self.app.mountCommandQueue.empty():
                    command = self.app.mountCommandQueue.get()
                    if command == 'ShowAlignmentModel':
                        num = self.numberModelStars()
                        if num == -1:
                            self.app.messageQueue.put('#BRShow Model not available without real mount\n')
                        else:
                            self.app.ui.btn_showActualModel.setStyleSheet(self.app.BLUE)
                            self.showAlignmentModel(self.getAlignmentModel())
                            self.app.ui.btn_showActualModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'ClearAlign':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('#BRClear Align not available without real mount\n')
                        else:
                            self.mountHandler.sendCommand('delalig')
                    elif command == 'RunTargetRMSAlignment':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('#BRRun Optimize not available without real mount\n')
                        else:
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.app.BLUE)
                            self.runTargetRMSAlignment()
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.app.DEFAULT)
                        self.app.ui.btn_cancelRunTargetRMSAlignment.setStyleSheet(self.app.DEFAULT)
                    elif command == 'DeleteWorstPoint':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('#BRDelete worst point not available without real mount\n')
                        else:
                            self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.app.BLUE)
                            self.deleteWorstPoint()
                            self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveBackupModel':
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.app.BLUE)
                        self.saveBackupModel()
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadBackupModel':
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.app.BLUE)
                        self.loadBackupModel()
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadBaseModel':
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.app.BLUE)
                        self.loadBaseModel()
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveBaseModel':
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.app.BLUE)
                        self.saveBaseModel()
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadRefinementModel':
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.app.BLUE)
                        self.loadRefinementModel()
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveRefinementModel':
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.app.BLUE)
                        self.saveRefinementModel()
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadSimpleModel':
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.app.BLUE)
                        self.loadSimpleModel()
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveSimpleModel':
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.app.BLUE)
                        self.saveSimpleModel()
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadDSO1Model':
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.app.BLUE)
                        self.loadDSO1Model()
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveDSO1Model':
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.app.BLUE)
                        self.saveDSO1Model()
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.app.DEFAULT)
                    elif command == 'LoadDSO2Model':
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.app.BLUE)
                        self.loadDSO2Model()
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.app.DEFAULT)
                    elif command == 'SaveDSO2Model':
                        self.app.ui.btn_saveDSO2Model.setStyleSheet(self.app.BLUE)
                        self.saveDSO2Model()
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
                        self.mountHandler.sendCommand(command)
                    self.app.mountCommandQueue.task_done()
                else:
                    if self.counter == 0:
                        self.getStatusOnce()
                    if self.counter % 2 == 0:
                        self.getStatusFast()
                    if self.counter % 15 == 0:
                        self.getStatusMedium()
                    if self.counter % 150 == 0:
                        self.getStatusSlow()
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
                self.counter += 1
            else:
                self.mountHandler.connect()
                self.counter = 0
                time.sleep(1)
        self.mountHandler.disconnect()
        if platform.system() == 'Windows':
            pythoncom.CoUninitialize()

    def mountShutdown(self):
        reply = self.mountHandler.sendCommand('shutdown')
        if reply != '1':
            self.logger.error('error: {0}'.format(reply))
            self.app.messageQueue.put('#BRError in mount shutdown\n')
        else:
            self.mountHandler.connected = False
            time.sleep(1)
            self.mountHandler.disconnect()
            self.logger.info('Shutdown mount manually')
            self.app.messageQueue.put('Shutting mount down !')

    def flipMount(self):
        reply = self.mountHandler.sendCommand('FLIP').rstrip('#').strip()
        if reply == '0':
            self.app.messageQueue.put('#BRFlip Mount could not be executed\n')
            self.logger.error('error: {0}'.format(reply))

    def syncMountModel(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.mountHandler.sendCommand('Sr{0}'.format(ra))
        self.mountHandler.sendCommand('Sd{0}'.format(dec))
        self.mountHandler.sendCommand('CMCFG0')
        # send sync command
        reply = self.mountHandler.sendCommand('CM')
        if reply[:5] == 'Coord':
            self.logger.info('mount modeling synced')
            return True
        else:
            self.logger.warning('error in sync mount modeling')
            return False

    def addRefinementStar(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.mountHandler.sendCommand('Sr{0}'.format(ra))
        self.mountHandler.sendCommand('Sd{0}'.format(dec))
        starNumber = self.numberModelStars()
        reply = self.mountHandler.sendCommand('CMS')
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
        self.mountHandler.sendCommand('newalig')
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
        reply = self.mountHandler.sendCommand('endalig')
        if reply == 'V':
            self.logger.info('Model successful finished!')
        else:
            self.logger.warning('Model could not be calculated with current data!')

    def numberModelStars(self):
        return int(self.mountHandler.sendCommand('getalst'))

    def getAlignmentModelStatus(self, alignModel):
        if self.data['FW'] < 21500:
            return alignModel
        try:
            reply = self.mountHandler.sendCommand('getain')
            # there should be a reply, format string is "ZZZ.ZZZZ,+AA.AAAA,EE.EEEE,PPP.PP,+OO.OOOO,+aa.aa, +bb.bb,NN,RRRRR.R#"
            if reply:
                # if a single 'E' returns, there is a problem, not further parameter will follow
                if reply != 'E':
                    a1, a2, a3, a4, a5, a6, a7, a8, a9 = reply.split(',')
                    # 'E' could be sent if not calculable or no value available
                    if a1 != 'E':
                        alignModel['Azimuth'] = float(a1)
                    else:
                        alignModel['Azimuth'] = 0
                    if a2 != 'E':
                        alignModel['Altitude'] = float(a2)
                    else:
                        alignModel['Altitude'] = 0
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
        points = []
        alignModel = {'Azimuth': 0.0,
                      'Altitude': 0.0,
                      'PolarError': 0.0,
                      'PosAngle': 0.0,
                      'OrthoError': 0.0,
                      'AzimuthKnobs': 0.0,
                      'AltitudeKnobs': 0.0,
                      'Terms': 0,
                      'RMS': 0.0,
                      'Points': points}
        numberStars = self.numberModelStars()
        alignModel['Number'] = numberStars
        if numberStars < 1:
            return alignModel
        alignModel = self.getAlignmentModelStatus(alignModel)
        for i in range(1, numberStars + 1):
            reply = self.mountHandler.sendCommand('getalp{0:d}'.format(i)).split(',')
            ha = reply[0].strip().split('.')[0]
            dec = reply[1].strip().split('.')[0]
            ErrorRMS = float(reply[2].strip())
            ErrorAngle = reply[3].strip().rstrip('#')
            dec = dec.replace('*', ':')
            RaJNow = self.transform.degStringToDecimal(ha)
            DecJNow = self.transform.degStringToDecimal(dec)
            az, alt = self.transform.ra_dec_lst_to_az_alt(RaJNow, DecJNow)
            # index should start with 0, but numbering in mount starts with 1
            alignModel['Points'].append((i-1, RaJNow, DecJNow, az, alt, ErrorRMS, float(ErrorAngle)))
        return alignModel

    def retrofitMountData(self, data):
        num = self.numberModelStars()
        if num == len(data):
            alignModel = self.getAlignmentModel()
            self.showAlignmentModel(alignModel)
            for i in range(0, alignModel['Number']):
                data[i]['ModelError'] = float(alignModel['Points'][i][5])
                data[i]['RaError'] = data[i]['ModelError'] * math.sin(math.radians(alignModel['Points'][i][6]))
                data[i]['DecError'] = data[i]['ModelError'] * math.cos(math.radians(alignModel['Points'][i][6]))
            self.app.modelLogQueue.put('Mount Model and Model Data synced\n')
        else:
            self.logger.warning('Size of mount data {0} and modeling data {1} do not fit !'.format(num, len(data)))
            self.app.messageQueue.put('Mount Data and Model Data could not be synced\n')
            self.app.messageQueue.put('#BRMount Data and Model Data mismatch\n')
        return data

    def showAlignmentModel(self, alignModel):
        self.data['ModelStarError'] = 'Downloading data\n'
        for i in range(0, alignModel['Number']):
            self.data['ModelStarError'] += '#{0:02d}   AZ: {1:3d}   Alt: {2:3d}   Err: {3:4.1f}\x22   PA: {4:3.0f}\xb0\n'.format(i, int(alignModel['Points'][i][3]), int(alignModel['Points'][i][4]), alignModel['Points'][i][5], alignModel['Points'][i][6])
        self.data['ModelStarError'] += 'Downloading finished\n'
        self.data['NumberAlignmentStars'] = alignModel['Number']
        self.data['ModelRMSError'] = '{0:3.1f}'.format(alignModel['RMS'])
        self.data['ModelErrorPosAngle'] = '{0:3.1f}'.format(alignModel['PosAngle'])
        self.data['ModelPolarError'] = '{0}'.format(self.transform.decimalToDegree(alignModel['PolarError']))
        self.data['ModelOrthoError'] = '{0}'.format(self.transform.decimalToDegree(alignModel['OrthoError']))
        self.data['ModelErrorAz'] = '{0}'.format(self.transform.decimalToDegree(alignModel['AzimuthKnobs']))
        self.data['ModelErrorAlt'] = '{0}'.format(self.transform.decimalToDegree(alignModel['AltitudeKnobs']))
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
        self.app.showModelErrorPolar()
        return

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
        if alignModel['Number'] < 4:
            return
        if alignModel['Number'] > 3:
            # index 0 is the worst star, index starts with 0
            a = sorted(alignModel['Points'], key=itemgetter(5), reverse=True)
            index = a[0][0]
            # numbering in mount starts with 1
            reply = self.mountHandler.sendCommand('delalst{0:d}'.format(index + 1))
            if reply == '1':
                alignModel = self.getAlignmentModel()
                self.app.workerModelingDispatcher.modelingRunner.modelData.pop(index)
                for i in range(0, alignModel['Number']):
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] = float(alignModel['Points'][i][5])
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['RaError'] = self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] * math.sin(math.radians(float(alignModel['Points'][i][6])))
                    self.app.workerModelingDispatcher.modelingRunner.modelData[i]['DecError'] = self.app.workerModelingDispatcher.modelingRunner.modelData[i]['ModelError'] * math.cos(math.radians(float(alignModel['Points'][i][6])))
                self.showAlignmentModel(alignModel)
            else:
                self.logger.warning('Point {0} could not be deleted').format(index)
        return alignModel

    def saveModel(self, target):
        num = self.numberModelStars()
        if num == -1:
            self.app.messageQueue.put('#BWSave Model not available in simulation\n')
            return False
        self.mountHandler.sendCommand('modeldel0' + target)
        reply = self.mountHandler.sendCommand('modelsv0' + target)
        if reply == '1':
            self.app.messageQueue.put('Actual Mount Model saved to file {0}\n'.format(target))
            return True
        else:
            self.logger.warning('Model {0} could not be saved'.format(target))
            return False

    def loadModel(self, target):
        num = self.numberModelStars()
        if num == -1:
            self.app.messageQueue.put('#BWLoad Model not available in simulation\n')
            return False
        reply = self.mountHandler.sendCommand('modelld0' + target)
        if reply == '1':
            self.app.messageQueue.put('Mount Model loaded from file {0}'.format(target))
            return True
        else:
            self.app.messageQueue.put('#BRThere is no modeling named {0} or error while loading\n'.format(target))
            self.logger.warning('Model {0} could not be loaded'.format(target))
            return False

    def saveBackupModel(self):
        if self.saveModel('BACKUP'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'backup.dat')

    def loadBackupModel(self):
        if self.loadModel('BACKUP'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.analyseWindow.analyse.loadDataRaw('backup.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for BACKUP\n')

    def saveBaseModel(self):
        if self.saveModel('BASE'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'base.dat')
            else:
                self.app.messageQueue.put('#BRNo data for BASE\n')

    def loadBaseModel(self):
        if self.loadModel('BASE'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.analyseWindow.analyse.loadDataRaw('base.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for BASE\n')

    def saveRefinementModel(self):
        if self.saveModel('REFINE'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'refine.dat')
            else:
                self.app.messageQueue.put('#BRNo data for REFINE\n')

    def loadRefinementModel(self):
        if self.loadModel('REFINE'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.analyseWindow.analyse.loadDataRaw('refine.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for REFINE\n')

    def saveActualModel(self):
        if self.saveModel('ACTUAL'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                if 'Index' in self.app.workerModelingDispatcher.modelingRunner.modelData[0].keys():
                    self.app.analyseWindow.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'actual.dat')
            else:
                self.app.messageQueue.put('#BRNo data for ACTUAL\n')

    def loadActualModel(self):
        if self.loadModel('ACTUAL'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.analyseWindow.analyse.loadDataRaw('actual.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for ACTUAL\n')

    def saveSimpleModel(self):
        if self.saveModel('SIMPLE'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'simple.dat')
            else:
                self.app.messageQueue.put('#BRNo data file for SIMPLE\n')

    def loadSimpleModel(self):
        if self.loadModel('SIMPLE'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.analyseWindow.analyse.loadDataRaw('simple.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for SIMPLE\n')

    def saveDSO1Model(self):
        if self.saveModel('DSO1'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'DSO1.dat')
            else:
                self.app.messageQueue.put('#BRNo data file for DSO1\n')

    def loadDSO1Model(self):
        if self.loadModel('DSO1'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.analyseWindow.analyse.loadDataRaw('DSO1.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for DSO1\n')

    def saveDSO2Model(self):
        if self.saveModel('DSO2'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'DSO2.dat')
            else:
                self.app.messageQueue.put('#BRNo data file for DSO2\n')

    def loadDSO2Model(self):
        if self.loadModel('DSO2'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.analyseWindow.analyse.loadDataRaw('dso2.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for DSO2\n')

    def setRefractionParam(self):
        if 'Temperature' in self.app.workerAscomEnvironment.data and 'Pressure' in self.app.workerAscomEnvironment.data and self.app.workerAscomEnvironment.isRunning:
            pressure = self.app.workerAscomEnvironment.data['Pressure']
            temperature = self.app.workerAscomEnvironment.data['Temperature']
            if (900.0 < pressure < 1100.0) and (-40.0 < temperature < 50.0):
                self.mountHandler.sendCommand('SRPRS{0:04.1f}'.format(pressure))
                if temperature > 0:
                    self.mountHandler.sendCommand('SRTMP+{0:03.1f}'.format(temperature))
                else:
                    self.mountHandler.sendCommand('SRTMP-{0:3.1f}'.format(-temperature))
                self.data['RefractionTemperature'] = self.mountHandler.sendCommand('GRTMP')
                self.data['RefractionPressure'] = self.mountHandler.sendCommand('GRPRS')
            else:
                self.logger.warning('parameters out of range ! temperature:{0} pressure:{1}'.format(temperature, pressure))

    def getStatusFast(self):
        reply = self.mountHandler.sendCommand('GS')
        if reply:
            self.data['LocalSiderealTime'] = reply.strip('#')
        reply = self.mountHandler.sendCommand('GR')
        if reply:
            self.data['RaJNow'] = self.transform.degStringToDecimal(reply)
        reply = self.mountHandler.sendCommand('GD')
        if reply:
            self.data['DecJNow'] = self.transform.degStringToDecimal(reply)
        reply = self.mountHandler.sendCommand('Ginfo')
        if reply:
            try:
                reply = reply.rstrip('#').strip().split(',')
            except Exception as e:
                self.logger.error('receive error Ginfo command: {0} reply:{1}'.format(e, reply))
            finally:
                pass
            if len(reply) == 8:
                self.data['RaJNow'] = float(reply[0])
                self.data['DecJNow'] = float(reply[1])
                self.data['Pierside'] = reply[2]
                self.data['Az'] = float(reply[3])
                self.data['Alt'] = float(reply[4])
                # needed for 2.14. firmware
                self.data['JulianDate'] = reply[5].rstrip('#')
                self.data['Status'] = int(reply[6])
                self.data['Slewing'] = (reply[7] == '1')
            else:
                self.logger.warning('Ginfo command delivered wrong number of arguments: {0}'.format(reply))
            self.data['RaJ2000'], self.data['DecJ2000'] = self.transform.transformERFA(self.data['RaJNow'], self.data['DecJNow'], 2)
            self.data['TelescopeRA'] = '{0}'.format(self.transform.decimalToDegree(self.data['RaJ2000'], False, False))
            self.data['TelescopeDEC'] = '{0}'.format(self.transform.decimalToDegree(self.data['DecJ2000'], True, False))
            self.data['TelescopeAltitude'] = '{0:03.2f}'.format(self.data['Alt'])
            self.data['TelescopeAzimuth'] = '{0:03.2f}'.format(self.data['Az'])
            self.data['MountStatus'] = '{0}'.format(self.data['Status'])
            self.data['JulianDate'] = '{0}'.format(self.data['JulianDate'][:13])
            if self.data['Pierside'] == str('W'):
                self.data['TelescopePierSide'] = 'WEST'
            else:
                self.data['TelescopePierSide'] = 'EAST'
            self.signalMountAzAltPointer.emit(self.data['Az'], self.data['Alt'])
            self.data['TimeToFlip'] = int(float(self.mountHandler.sendCommand('Gmte')))
            self.data['MeridianLimitTrack'] = int(float(self.mountHandler.sendCommand('Glmt')))
            self.data['MeridianLimitSlew'] = int(float(self.mountHandler.sendCommand('Glms')))
            self.data['TimeToMeridian'] = int(self.data['TimeToFlip'] - self.data['MeridianLimitTrack'] / 360 * 24 * 60)

    def getStatusMedium(self):
        if self.app.ui.checkAutoRefractionNotTracking.isChecked():
            # if there is no tracking, than updating is good
            if self.data['Status'] != 0:
                self.setRefractionParam()
        if self.app.ui.checkAutoRefractionCamera.isChecked():
            # the same is good if the camera is not in integrating
            if self.app.workerModelingDispatcher.modelingRunner.imagingHandler.cameraStatus in ['READY - IDLE', 'DOWNLOADING']:
                self.setRefractionParam()
        self.data['SlewRate'] = self.mountHandler.sendCommand('GMs')
        self.signalMountTrackPreview.emit()

    def getStatusSlow(self):
        self.data['TimeToTrackingLimit'] = self.mountHandler.sendCommand('Gmte')
        self.data['RefractionTemperature'] = self.mountHandler.sendCommand('GRTMP')
        self.data['RefractionPressure'] = self.mountHandler.sendCommand('GRPRS')
        self.data['TelescopeTempDEC'] = self.mountHandler.sendCommand('GTMP1')
        self.data['RefractionStatus'] = self.mountHandler.sendCommand('GREF')
        self.data['UnattendedFlip'] = self.mountHandler.sendCommand('Guaf')
        self.data['MeridianLimitTrack'] = self.mountHandler.sendCommand('Glmt')
        self.data['MeridianLimitSlew'] = self.mountHandler.sendCommand('Glms')
        self.data['DualAxisTracking'] = self.mountHandler.sendCommand('Gdat')
        self.data['CurrentHorizonLimitHigh'] = self.mountHandler.sendCommand('Gh')
        self.data['CurrentHorizonLimitLow'] = self.mountHandler.sendCommand('Go')
        try:
            if self.data['FW'] < 21500:
                return
            reply = self.mountHandler.sendCommand('GDUTV')
            if reply:
                valid, expirationDate = reply.split(',')
                self.data['UTCDataValid'] = valid
                self.data['UTCDataExpirationDate'] = expirationDate
        except Exception as e:
            self.logger.error('receive error GDUTV command: {0}'.format(e))
        finally:
            pass

    def getStatusOnce(self):
        # Set high precision mode
        self.mountHandler.sendCommand('U2')
        self.site_height = self.mountHandler.sendCommand('Gev')
        lon1 = self.mountHandler.sendCommand('Gg')
        # due to compatibility to LX200 protocol east is negative
        if lon1[0] == '-':
            self.site_lon = lon1.replace('-', '+')
        else:
            self.site_lon = lon1.replace('+', '-')
        self.site_lat = self.mountHandler.sendCommand('Gt')
        self.data['CurrentSiteElevation'] = self.site_height
        self.data['CurrentSiteLongitude'] = lon1
        self.data['CurrentSiteLatitude'] = self.site_lat
        self.data['FirmwareDate'] = self.mountHandler.sendCommand('GVD')
        self.data['FirmwareNumber'] = self.mountHandler.sendCommand('GVN')
        fw = self.data['FirmwareNumber'].split('.')
        if len(fw) == 3:
            self.data['FW'] = int(float(fw[0]) * 10000 + float(fw[1]) * 100 + float(fw[2]))
        else:
            self.data['FW'] = 0
        self.data['FirmwareProductName'] = self.mountHandler.sendCommand('GVP')
        self.data['FirmwareTime'] = self.mountHandler.sendCommand('GVT')
        self.data['HardwareVersion'] = self.mountHandler.sendCommand('GVZ')
        self.logger.info('FW: {0} Number: {1}'.format(self.mountHandler.sendCommand('GVN'), self.data['FW']))
        self.logger.info('Site Lon:{0}'.format(self.site_lon))
        self.logger.info('Site Lat:{0}'.format(self.site_lat))
        self.logger.info('Site Height:{0}'.format(self.site_height))
