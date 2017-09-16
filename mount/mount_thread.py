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

# import basic stuff
import logging
import math
import threading
import time
# for the sorting
from operator import itemgetter
# import PyQT5 for threading purpose
import PyQt5
# win32com
import pythoncom
#  mount driver classes
from mount import ascommount
from mount import ipdirect
# astrometry
from astrometry import transform


class Mount(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # enable logging
    signalMountConnected = PyQt5.QtCore.pyqtSignal([bool], name='mountConnected')                                                 # signal for connection status
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal([float, float], name='mountAzAltPointer')
    signalMountTrackPreview = PyQt5.QtCore.pyqtSignal(name='mountTrackPreview')

    BLUE = 'background-color: rgb(42, 130, 218)'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'
    BLIND_COMMANDS = ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']

    def __init__(self, app):
        super().__init__()                                                                                                  # init of the class parent with super
        self.app = app                                                                                                      # accessing ui object from mount class
        self.MountAscom = ascommount.MountAscom(app)                                                                             # set ascom driver class
        self.MountIpDirect = ipdirect.MountIpDirect(app)
        self.mountHandler = self.MountAscom
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
                                }                                                                                           # conversion list Gstat to text
        self.ra = 0                                                                                                         # mount reported ra to J2000 converted
        self.dec = 0                                                                                                        # mount reported dec to J2000 converted
        self.raJnow = 0
        self.decJnow = 0
        self.az = 0                                                                                                         # mount reported azimuth
        self.alt = 0                                                                                                        # mount reported altitude
        self.stat = 0                                                                                                       # mount status (from Gstat command)
        self.slewing = False                                                                                                # from *D' command
        self.site_lat = '49'                                                                                                # site lat
        self.site_lon = 0                                                                                                   # site lon
        self.site_height = 0                                                                                                # site height
        self.jd = 2451544.5                                                                                                 # julian date
        self.sidereal_time = ''                                                                                             # local sidereal time
        self.pierside = 0                                                                                                   # side of pier (E/W)
        self.timeToFlip = 200                                                                                               # minutes to flip
        self.timeToMeridian = 0
        self.meridianLimitTrack = 5.0                                                                                       # degrees after meridian to flip
        self.refractionTemp = '20.0'                                                                                        # coordinate transformation need temp
        self.refractionPressure = '900.0'                                                                                   # and pressure
        self.counter = 0                                                                                                    # counter im main loop
        self.chooserLock = threading.Lock()
        self.initConfig()

    def initConfig(self):
        try:
            if 'ASCOMTelescopeDriverName' in self.app.config:
                self.MountAscom.driverName = self.app.config['ASCOMTelescopeDriverName']
        except Exception as e:
            self.logger.error('initConfig -> item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['ASCOMTelescopeDriverName'] = self.MountAscom.driverName

    def mountDriverChooser(self):
        self.chooserLock.acquire()                                                                                          # avoid multiple switches running at the same time
        if self.mountHandler.connected:
            self.mountHandler.connected = False                                                                             # connection to False -> no commands emitted
            time.sleep(1)                                                                                                   # wait some time to get commands finished
            self.mountHandler.disconnect()                                                                                  # do formal disconnection
        if self.app.ui.rb_directMount.isChecked():
            self.mountHandler = self.MountIpDirect
            self.logger.debug('mountDriverChoo-> actual driver is IpDirect, IP is: {0}'.format(self.MountIpDirect.mountIP()))
        elif self.app.ui.rb_ascomMount.isChecked():
            self.mountHandler = self.MountAscom
            self.logger.debug('mountDriverChoo-> actual driver is ASCOM')
        self.chooserLock.release()                                                                                          # free the lock to move again

    def run(self):                                                                                                          # runnable of the thread
        pythoncom.CoInitialize()                                                                                            # needed for doing COM objects in threads
        self.counter = 0                                                                                                    # init count for managing different cycle times
        while True:                                                                                                         # main loop in thread
            self.signalMountConnected.emit(self.mountHandler.connected)                                                     # sending the connection status
            if self.mountHandler.connected:                                                                                              # when connected, starting the work
                if not self.app.commandQueue.empty():                                                                       # checking if in queue is something to do
                    command = self.app.commandQueue.get()                                                                   # if yes, getting the work command
                    if command == 'ShowAlignmentModel':                                                                     # checking which command was sent
                        num = self.numberModelStars()
                        if num == -1:
                            self.app.messageQueue.put('Show Model not available without real mount')
                        else:
                            self.app.mountDataQueue.put({'Name': 'ModelStarError', 'Value': 'delete'})
                            self.app.ui.btn_showActualModel.setStyleSheet(self.BLUE)
                            self.showAlignmentModel(self.getAlignmentModel())
                            self.app.ui.btn_showActualModel.setStyleSheet(self.DEFAULT)
                    elif command == 'ClearAlign':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('Clear Align not available without real mount')
                        else:
                            self.mountHandler.sendCommand('delalig')
                    elif command == 'RunTargetRMSAlignment':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('Run Optimize not available without real mount')
                        else:
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.BLUE)
                            self.runTargetRMSAlignment()
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.DEFAULT)
                    elif command == 'DeleteWorstPoint':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('Delete worst point not available without real mount')
                        else:
                            self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                            self.deleteWorstPoint()
                            self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveBackupModel':
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.BLUE)                                                # button blue
                        self.saveBackupModel()
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.DEFAULT)                                             # button to default back
                    elif command == 'LoadBackupModel':
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.BLUE)
                        self.loadBackupModel()
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadBaseModel':
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.BLUE)
                        self.loadBaseModel()
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveBaseModel':
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.BLUE)
                        self.saveBaseModel()
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadRefinementModel':
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.BLUE)
                        self.loadRefinementModel()
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveRefinementModel':
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.BLUE)
                        self.saveRefinementModel()
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadSimpleModel':
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.BLUE)
                        self.loadSimpleModel()
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveSimpleModel':
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.BLUE)
                        self.saveSimpleModel()
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadDSO1Model':
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.BLUE)
                        self.loadDSO1Model()
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveDSO1Model':
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.BLUE)
                        self.saveDSO1Model()
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadDSO2Model':
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.BLUE)
                        self.loadDSO2Model()
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveDSO2Model':
                        self.app.ui.btn_saveDSO2Model.setStyleSheet(self.BLUE)
                        self.saveDSO2Model()
                        self.app.ui.btn_saveDSO2Model.setStyleSheet(self.DEFAULT)
                    elif command == 'SetRefractionParameter':
                        self.setRefractionParameter()
                    elif command == 'FLIP':
                        self.flipMount()
                    elif command == 'SetupAscomDriver':
                        self.MountAscom.setupDriver()
                    else:
                        self.mountHandler.sendCommand(command)                                                              # doing the command directly to mount (no method necessary)
                    self.app.commandQueue.task_done()
                else:                                                                                                       # if not connected, the we should do this
                    if self.counter == 0:                                                                                   # jobs once done at the beginning
                        self.getStatusOnce()                                                                                # task once
                    if self.counter % 2 == 0:                                                                               # all tasks with 400 ms
                        self.getStatusFast()                                                                                # polling the mount status Ginfo
                    if self.counter % 15 == 0:                                                                              # all tasks with 3 s
                        self.getStatusMedium()                                                                              # polling the mount
                    if self.counter % 150 == 0:                                                                             # all task with 30 seconds
                        self.getStatusSlow()                                                                                # slow ones
                time.sleep(0.2)                                                                                             # time base is 200 ms
                self.counter += 1                                                                                           # increasing counter for selection
            else:                                                                                                           # when not connected try to connect
                self.mountHandler.connect()
                self.counter = 0
                time.sleep(1)                                                                                               # try it every second, not more
        self.mountHandler.disconnect()
        pythoncom.CoUninitialize()                                                                                          # needed for doing COM objects in threads
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         # wait for stop of thread

    def flipMount(self):                                                                                                    # doing the flip of the mount
        reply = self.mountHandler.sendCommand('FLIP').rstrip('#').strip()
        if reply == '0':                                                                                                    # error handling if not successful
            self.app.messageQueue.put('Flip Mount could not be executed !')                                                 # write to gui
            self.logger.debug('flipMount      -> error: {0}'.format(reply))                                                 # write to logger

    def numberModelStars(self):
        return int(self.mountHandler.sendCommand('getalst'))                                                                # if there are some points, a modeling must be there

    def getAlignmentModelStatus(self, alignModel):
        try:
            reply = self.mountHandler.sendCommand('getain')                                                                 # load the data from new command
            if reply:                                                                                                       # there should be a reply, format string is "ZZZ.ZZZZ,+AA.AAAA,EE.EEEE,PPP.PP,+OO.OOOO,+aa.aa, +bb.bb,NN,RRRRR.R#"
                if reply != 'E':                                                                                            # if a single 'E' returns, there is a problem, not further parameter will follow
                    a1, a2, a3, a4, a5, a6, a7, a8, a9 = reply.split(',')
                    if a1 != 'E':                                                                                           # 'E' could be sent if not calculable or no value available
                        alignModel['azimuth'] = float(a1)
                    else:
                        alignModel['azimuth'] = 0
                    if a2 != 'E':
                        alignModel['altitude'] = float(a2)
                    else:
                        alignModel['altitude'] = 0
                    if a3 != 'E':
                        alignModel['polarError'] = float(a3)
                    else:
                        alignModel['polarError'] = 0
                    if a4 != 'E':
                        alignModel['posAngle'] = float(a4)
                    else:
                        alignModel['posAngle'] = 0
                    if a5 != 'E':
                        alignModel['orthoError'] = float(a5)
                    else:
                        alignModel['orthoError'] = 0
                    if a6 != 'E':
                        alignModel['azimuthKnobs'] = float(a6)
                    else:
                        alignModel['azimuthKnobs'] = 0
                    if a7 != 'E':
                        alignModel['altitudeKnobs'] = float(a7)
                    else:
                        alignModel['altitudeKnobs'] = 0
                    if a8 != 'E':
                        alignModel['terms'] = int(float(a8))
                    else:
                        alignModel['terms'] = 0
                    if a9 != 'E':
                        alignModel['RMS'] = float(a9)
                    else:
                        alignModel['RMS'] = 0
        except Exception as e:
            self.logger.error('getAlignmentMod-> receive error getain command: {0}'.format(e))
        finally:
            return alignModel

    def getAlignmentModel(self):                                                                                            # download alignment modeling from mount
        alignModel = {}                                                                                                     # clear alignment data
        points = []                                                                                                         # clear points list
        alignModel['azimuth'] = 0.0
        alignModel['altitude'] = 0.0
        alignModel['polarError'] = 0.0
        alignModel['posAngle'] = 0.0
        alignModel['orthoError'] = 0.0
        alignModel['azimuthKnobs'] = 0.0
        alignModel['altitudeKnobs'] = 0.0
        alignModel['terms'] = 0
        alignModel['RMS'] = 0.0                                                                                             # clear the alignment points downloaded
        alignModel['points'] = points
        numberStars = self.numberModelStars()                                                                               # get number of stars
        alignModel['number'] = numberStars
        if numberStars < 1:                                                                                                 # if no stars or no real mount, finish
            return alignModel
        alignModel = self.getAlignmentModelStatus(alignModel)                                                               # add status information
        for i in range(1, numberStars + 1):                                                                                 # otherwise download them step for step
            reply = self.mountHandler.sendCommand('getalp{0:d}'.format(i)).split(',')
            ha = reply[0].strip().split('.')[0]
            dec = reply[1].strip().split('.')[0]
            errorRMS = float(reply[2].strip())
            errorAngle = reply[3].strip().rstrip('#')
            dec = dec.replace('*', ':')
            ra_J2000 = self.transform.degStringToDecimal(ha)
            dec_J2000 = self.transform.degStringToDecimal(dec)
            az, alt = self.transform.ra_dec_lst_to_az_alt(ra_J2000, dec_J2000, self.transform.degStringToDecimal(self.site_lat))
            alignModel['points'].append((i-1, ra_J2000, dec_J2000, az, alt, errorRMS, float(errorAngle)))                   # index should start with 0, but numbering in mount starts with 1
        return alignModel

    def retrofitMountData(self, data):
        num = self.numberModelStars()                                                                                       # size mount modeling
        if num == len(data):
            alignModel = self.getAlignmentModel()                                                                           # get mount points
            self.showAlignmentModel(alignModel)
            for i in range(0, alignModel['number']):                                                                        # run through all the points
                data[i]['modelError'] = float(alignModel['points'][i][5])                                                   # and for the total error
                data[i]['raError'] = data[i]['modelError'] * math.sin(math.radians(alignModel['points'][i][6]))             # set raError new from total error mount with polar error angle from mount
                data[i]['decError'] = data[i]['modelError'] * math.cos(math.radians(alignModel['points'][i][6]))            # same to dec
            self.app.modelLogQueue.put('Mount Model and Model Data synced\n')
        else:
            self.logger.error('retrofitMountDa-> size mount modeling {0} and modeling data {1} do not fit !'.format(num, len(data)))
            self.app.modelLogQueue.put('Mount Model and Model Data could not be synced\n')
            self.app.messageQueue.put('Error- Mount Model and Model Data mismatch!\n')
        return data

    def showAlignmentModel(self, alignModel):
        self.app.mountDataQueue.put({'Name': 'ModelStarError', 'Value': 'Downloading data\n'})
        for i in range(0, alignModel['number']):
            self.app.mountDataQueue.put({'Name': 'ModelStarError', 'Value': '#{0:02d}   AZ: {1:3d}   Alt: {2:3d}   Err: {3:4.1f}\x22   PA: {4:3.0f}\xb0\n'
                                        .format(i, int(alignModel['points'][i][3]), int(alignModel['points'][i][4]), alignModel['points'][i][5], alignModel['points'][i][6])})
        self.app.mountDataQueue.put({'Name': 'ModelStarError', 'Value': 'Downloading finished\n'})
        self.app.mountDataQueue.put({'Name': 'NumberAlignmentStars', 'Value': alignModel['number']})
        self.app.mountDataQueue.put({'Name': 'ModelRMSError', 'Value': '{0:3.1f}'.format(alignModel['RMS'])})
        self.app.mountDataQueue.put({'Name': 'ModelRMSError', 'Value': '{0:3.1f}'.format(alignModel['RMS'])})
        self.app.mountDataQueue.put({'Name': 'ModelErrorPosAngle', 'Value': '{0:3.1f}'.format(alignModel['posAngle'])})
        self.app.mountDataQueue.put({'Name': 'ModelPolarError', 'Value': '{0}'.format(self.transform.decimalToDegree(alignModel['polarError']))})
        self.app.mountDataQueue.put({'Name': 'ModelOrthoError', 'Value': '{0}'.format(self.transform.decimalToDegree(alignModel['orthoError']))})
        self.app.mountDataQueue.put({'Name': 'ModelErrorAz', 'Value': '{0}'.format(self.transform.decimalToDegree(alignModel['azimuthKnobs']))})
        self.app.mountDataQueue.put({'Name': 'ModelErrorAlt', 'Value': '{0}'.format(self.transform.decimalToDegree(alignModel['altitudeKnobs']))})
        self.app.mountDataQueue.put({'Name': 'ModelTerms', 'Value': '{0:2d}'.format(alignModel['terms'])})
        if alignModel['azimuthKnobs'] > 0:
            value = '{0:2.2f} left'.format(abs(alignModel['azimuthKnobs']))
        else:
            value = '{0:2.2f} left'.format(abs(alignModel['azimuthKnobs']))
        self.app.mountDataQueue.put({'Name': 'ModelKnobTurnAz', 'Value': '{0}'.format(value)})
        if alignModel['altitudeKnobs'] > 0:
            value = '{0:2.2f} down'.format(abs(alignModel['altitudeKnobs']))
        else:
            value = '{0:2.2f} up'.format(abs(alignModel['altitudeKnobs']))
        self.app.mountDataQueue.put({'Name': 'ModelKnobTurnAlt', 'Value': '{0}'.format(value)})
        self.app.showModelErrorPolar()
        return

    def runTargetRMSAlignment(self):
        self.app.mountDataQueue.put({'Name': 'ModelStarError', 'Value': 'delete'})
        alignModel = self.getAlignmentModel()
        if alignModel['number'] < 4:
            return                                                                                                          # set maximum
        while alignModel['RMS'] > float(self.app.ui.targetRMS.value()) and alignModel['number'] > 3:
            alignModel = self.deleteWorstPointRaw(alignModel)

    def deleteWorstPoint(self):
        alignModel = self.getAlignmentModel()
        self.deleteWorstPointRaw(alignModel)

    def deleteWorstPointRaw(self, alignModel):
        if alignModel['number'] < 4:
            return
        if alignModel['number'] > 3:
            a = sorted(alignModel['points'], key=itemgetter(5), reverse=True)                                               # index 0 is the worst star, index starts with 0
            index = a[0][0]
            reply = self.mountHandler.sendCommand('delalst{0:d}'.format(index + 1))                                         # numbering in mount starts with 1
            if reply == '1':                                                                                                # worst point could be deleted
                alignModel = self.getAlignmentModel()
                self.app.modeling.modelData.pop(index)
                for i in range(0, alignModel['number']):
                    self.app.modeling.modelData[i]['modelError'] = float(alignModel['points'][i][5])
                    self.app.modeling.modelData[i]['raError'] = self.app.modeling.modelData[i]['modelError'] * math.sin(math.radians(float(alignModel['points'][i][6])))
                    self.app.modeling.modelData[i]['decError'] = self.app.modeling.modelData[i]['modelError'] * math.cos(math.radians(float(alignModel['points'][i][6])))
                self.showAlignmentModel(alignModel)
            else:
                self.logger.error('deleteWorstPoin-> Point {0} could not be deleted').format(index)
        return alignModel

    def saveModel(self, target):
        num = self.numberModelStars()
        if num == -1:
            self.app.messageQueue.put('Save Model not available without real mount')
            return False
        self.mountHandler.sendCommand('modeldel0' + target)
        reply = self.mountHandler.sendCommand('modelsv0' + target)
        if reply == '1':
            self.app.messageQueue.put('Actual Mount Model saved to {0}'.format(target))
            return True
        else:
            self.logger.debug('saveBackupModel-> Model {0} could not be saved'.format(target))                              # log it
            return False

    def loadModel(self, target):
        num = self.numberModelStars()
        if num == -1:
            self.app.messageQueue.put('Load Model not available without real mount')
            return False
        reply = self.mountHandler.sendCommand('modelld0' + target)
        if reply == '1':
            self.app.messageQueue.put('Actual Mount Model loaded from {0}'.format(target))
            return True
        else:
            self.app.messageQueue.put('There is no modeling named {0} or error while loading'.format(target))
            self.logger.debug('loadBackupModel-> Model {0} could not be loaded'.format(target))                             # log it
            return False

    def saveBackupModel(self):
        if self.saveModel('BACKUP'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'backup.dat')

    def loadBackupModel(self):
        if self.loadModel('BACKUP'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('backup.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for BACKUP')

    def saveBaseModel(self):
        if self.saveModel('BASE'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'base.dat')
            else:
                self.app.messageQueue.put('No data for BASE')

    def loadBaseModel(self):
        if self.loadModel('BASE'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('base.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for BASE')

    def saveRefinementModel(self):
        if self.saveModel('REFINE'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'refine.dat')
            else:
                self.app.messageQueue.put('No data for REFINE')

    def loadRefinementModel(self):
        if self.loadModel('REFINE'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('refine.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for REFINE')

    def saveActualModel(self):
        if self.saveModel('ACTUAL'):
            if self.app.modeling.modelData:
                if 'index' in self.app.modeling.modelData[0].keys():
                    self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'actual.dat')
            else:
                self.app.messageQueue.put('No data for ACTUAL')

    def loadActualModel(self):
        if self.loadModel('ACTUAL'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('actual.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for ACTUAL')

    def saveSimpleModel(self):
        if self.saveModel('SIMPLE'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'simple.dat')
            else:
                self.app.messageQueue.put('No data file for SIMPLE')

    def loadSimpleModel(self):
        if self.loadModel('SIMPLE'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('simple.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for SIMPLE')

    def saveDSO1Model(self):
        if self.saveModel('DSO1'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'DSO1.dat')
            else:
                self.app.messageQueue.put('No data file for DSO1')

    def loadDSO1Model(self):
        if self.loadModel('DSO1'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('DSO1.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for DSO1')

    def saveDSO2Model(self):
        if self.saveModel('DSO2'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'DSO2.dat')
            else:
                self.app.messageQueue.put('No data file for DSO2')

    def loadDSO2Model(self):
        if self.loadModel('DSO2'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('dso2.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for DSO2')

    def setRefractionParameter(self):
        pressure = float(self.app.ui.le_pressureStick.text() + '0')
        temperature = float(self.app.ui.le_temperatureStick.text() + '0')
        if self.app.stick.connected == 1:
            if (900.0 < pressure < 1100.0) and (-40.0 < temperature < 50.0):
                self.mountHandler.sendCommand('SRPRS{0:04.1f}'.format(float(self.app.ui.le_pressureStick.text())))
                if temperature > 0:
                    self.mountHandler.sendCommand('SRTMP+{0:03.1f}'.format(float(self.app.ui.le_temperatureStick.text())))
                else:
                    self.mountHandler.sendCommand('SRTMP-{0:3.1f}'.format(-float(self.app.ui.le_temperatureStick.text())))
                self.app.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.mountHandler.sendCommand('GRTMP')})
                self.app.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.mountHandler.sendCommand('GRPRS')})
            else:
                self.logger.error('setRefractionPa-> parameters out of range ! temperature:{0} pressure:{1}'.format(temperature, pressure))
                self.logger.error('setRefractionPa-> parameters out of range ! driver:{0} object:{1}'.format(self.app.stick.driverName, self.app.stick.ascom))

    def getStatusFast(self):                                                                                                # fast status item like pointing
        reply = self.mountHandler.sendCommand('GS')
        if reply:
            self.sidereal_time = reply.strip('#')
            self.app.mountDataQueue.put({'Name': 'GetLocalTime', 'Value': '{0}'.format(self.sidereal_time)})                # Sidereal local time
        reply = self.mountHandler.sendCommand('GR')
        if reply:
            self.raJnow = self.transform.degStringToDecimal(reply)
        reply = self.mountHandler.sendCommand('GD')
        if reply:
            self.decJnow = self.transform.degStringToDecimal(reply)
        reply = self.mountHandler.sendCommand('Ginfo')                                                                      # use command "Ginfo" for fast topics
        if reply:                                                                                                           # if reply is there
            try:
                ra, dec, self.pierside, az, alt, jd, stat, slew = reply.rstrip('#').strip().split(',')                      # split the response to its parts
                self.raJnow = float(ra)
                self.decJnow = float(dec)
                self.jd = jd.rstrip('#')                                                                                    # needed for 2.14.8 beta firmware
                self.az = float(az)                                                                                         # same to azimuth
                self.alt = float(alt)                                                                                       # and altitude
                self.stat = int(stat)                                                                                       # status should be int for referencing list
                self.slewing = (slew == '1')                                                                                # set status slewing
                self.ra, self.dec = self.transform.transformNovas(self.raJnow, self.decJnow, 2)                             # convert J2000
                ra_show = self.transform.decimalToDegree(self.ra, False, False)
                dec_show = self.transform.decimalToDegree(self.dec, True, False)
                self.app.mountDataQueue.put({'Name': 'GetTelescopeDEC', 'Value': '{0}'.format(dec_show)})                   # put dec to gui
                self.app.mountDataQueue.put({'Name': 'GetTelescopeRA', 'Value': '{0}'.format(ra_show)})                     # put ra to gui
                self.app.mountDataQueue.put({'Name': 'GetTelescopeAltitude', 'Value': '{0:03.2f}'.format(self.alt)})        # Altitude
                self.app.mountDataQueue.put({'Name': 'GetTelescopeAzimuth', 'Value': '{0:03.2f}'.format(self.az)})          # Azimuth
                self.app.mountDataQueue.put({'Name': 'GetMountStatus', 'Value': '{0}'.format(self.stat)})                   # Mount status -> slew to stop
                if str(self.pierside) == str('W'):                                                                          # pier side
                    self.app.mountDataQueue.put({'Name': 'GetTelescopePierSide', 'Value': 'WEST'})                          # Transfer to test in GUI
                else:                                                                                                       #
                    self.app.mountDataQueue.put({'Name': 'GetTelescopePierSide', 'Value': 'EAST'})                          # Transfer to Text for GUI
                self.signalMountAzAltPointer.emit(self.az, self.alt)                                                        # set azalt Pointer in diagrams to actual pos
            except Exception as e:
                self.logger.error('getStatusFast  -> receive error Ginfo command: {0} reply:{1}'.format(e, reply))
            finally:
                pass
            self.timeToFlip = int(float(self.mountHandler.sendCommand('Gmte')))
            self.meridianLimitTrack = int(float(self.mountHandler.sendCommand('Glmt')))
            self.timeToMeridian = int(self.timeToFlip - self.meridianLimitTrack / 360 * 24 * 60)
            self.app.mountDataQueue.put({'Name': 'GetMeridianLimitTrack', 'Value': self.meridianLimitTrack})
            self.app.mountDataQueue.put({'Name': 'GetMeridianLimitSlew', 'Value': int(float(self.mountHandler.sendCommand('Glms')))})
            self.app.mountDataQueue.put({'Name': 'GetTimeToFlip', 'Value': self.timeToFlip})                                # Flip time
            self.app.mountDataQueue.put({'Name': 'GetTimeToMeridian', 'Value': self.timeToMeridian})                        # Time to meridian

    def getStatusMedium(self):                                                                                              # medium status items like refraction
        if self.app.ui.checkAutoRefraction.isChecked():                                                                     # check if autorefraction is set
            if self.stat != 0:                                                                                              # if no tracking, than autorefraction is good
                self.setRefractionParameter()                                                                               # transfer refraction from to mount
            else:                                                                                                           #
                if self.app.modeling.cpObject.cameraStatus in ['IDLE', 'DOWNLOADING', 'READY']:                                # if tracking, when camera is idle or downloading
                    self.setRefractionParameter()                                                                           # transfer refraction to mount
                else:                                                                                                       # otherwise
                    self.logger.debug('getStatusMedium-> no autorefraction')                                                # no autorefraction is possible
        self.app.mountDataQueue.put({'Name': 'GetSlewRate', 'Value': self.mountHandler.sendCommand('GMs')})                 # get actual slew rate
        self.signalMountTrackPreview.emit()

    def getStatusSlow(self):                                                                                                # slow update item like temps
        self.timeToFlip = self.mountHandler.sendCommand('Gmte')
        self.app.mountDataQueue.put({'Name': 'GetTimeToTrackingLimit', 'Value': self.timeToFlip})                           # Flip time
        self.refractionTemp = self.mountHandler.sendCommand('GRTMP')
        self.app.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.refractionTemp})                     # refraction temp out of mount
        self.refractionPressure = self.mountHandler.sendCommand('GRPRS')
        self.app.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.refractionPressure})                    # refraction pressure out of mount
        self.app.mountDataQueue.put({'Name': 'GetTelescopeTempDEC', 'Value': self.mountHandler.sendCommand('GTMP1')})       # temp motor circuit of both axes
        self.app.mountDataQueue.put({'Name': 'GetRefractionStatus', 'Value': self.mountHandler.sendCommand('GREF')})
        self.app.mountDataQueue.put({'Name': 'GetUnattendedFlip', 'Value': self.mountHandler.sendCommand('Guaf')})
        self.app.mountDataQueue.put({'Name': 'GetMeridianLimitTrack', 'Value': self.mountHandler.sendCommand('Glmt')})
        self.app.mountDataQueue.put({'Name': 'GetMeridianLimitSlew', 'Value': self.mountHandler.sendCommand('Glms')})
        self.app.mountDataQueue.put({'Name': 'GetDualAxisTracking', 'Value': self.mountHandler.sendCommand('Gdat')})
        self.app.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitHigh', 'Value': self.mountHandler.sendCommand('Gh')})
        self.app.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitLow', 'Value': self.mountHandler.sendCommand('Go')})
        try:
            reply = self.mountHandler.sendCommand('GDUTV')
            if reply:
                valid, expirationDate = reply.split(',')
                self.app.mountDataQueue.put({'Name': 'GetUTCDataValid', 'Value': valid})
                self.app.mountDataQueue.put({'Name': 'GetUTCDataExpirationDate', 'Value': expirationDate})
        except Exception as e:
            self.logger.error('getStatusSlow  -> receive error GDUTV command: {0}'.format(e))
        finally:
            pass

    def getStatusOnce(self):                                                                                                # one time updates for settings
        self.mountHandler.sendCommand('U2')                                                                                 # Set high precision mode
        self.site_height = self.mountHandler.sendCommand('Gev')                                                             # site height
        lon1 = self.mountHandler.sendCommand('Gg')                                                                          # get site lon
        if lon1[0] == '-':                                                                                                  # due to compatibility to LX200 protocol east is negative
            self.site_lon = lon1.replace('-', '+')                                                                          # change that
        else:
            self.site_lon = lon1.replace('+', '-')                                                                          # and vice versa
        self.site_lat = self.mountHandler.sendCommand('Gt')                                                                 # get site latitude
        self.app.mountDataQueue.put({'Name': 'GetCurrentSiteElevation', 'Value': self.site_height})                         # write data to GUI
        self.app.mountDataQueue.put({'Name': 'GetCurrentSiteLongitude', 'Value': lon1})
        self.app.mountDataQueue.put({'Name': 'GetCurrentSiteLatitude', 'Value': self.site_lat})
        self.app.mountDataQueue.put({'Name': 'GetFirmwareDate', 'Value': self.mountHandler.sendCommand('GVD')})
        self.app.mountDataQueue.put({'Name': 'GetFirmwareNumber', 'Value': self.mountHandler.sendCommand('GVN')})
        self.app.mountDataQueue.put({'Name': 'GetFirmwareProductName', 'Value': self.mountHandler.sendCommand('GVP')})
        self.app.mountDataQueue.put({'Name': 'GetFirmwareTime', 'Value': self.mountHandler.sendCommand('GVT')})
        self.app.mountDataQueue.put({'Name': 'GetHardwareVersion', 'Value': self.mountHandler.sendCommand('GVZ')})
        self.logger.debug('getStatusOnce  -> FW:{0}'.format(self.mountHandler.sendCommand('GVN')))                          # firmware version for checking
        self.logger.debug('getStatusOnce  -> Site Lon:{0}'.format(self.site_lon))                                           # site lon
        self.logger.debug('getStatusOnce  -> Site Lat:{0}'.format(self.site_lat))                                           # site lat
        self.logger.debug('getStatusOnce  -> Site Height:{0}'.format(self.site_height))                                     # site height
        self.loadActualModel()                                                                                              # prepare data synchronisation, load modeling data
        alignModel = self.getAlignmentModel()                                                                               # get modeling data from mount
        if not self.app.modeling.modelData and alignModel['RMS'] > 0:
            self.app.messageQueue.put('Model Data will be reconstructed from Mount Data')
            self.app.modeling.modelData = []
            for i in range(0, alignModel['number']):
                self.app.modeling.modelData.append({'modelError': float(alignModel['points'][i][5]),
                                                    'raError': float(alignModel['points'][i][5]) * math.sin(math.radians(alignModel['points'][i][6])),
                                                    'decError': float(alignModel['points'][i][5]) * math.cos(math.radians(alignModel['points'][i][6])),
                                                    'azimuth': float(alignModel['points'][i][3]),
                                                    'altitude': float(alignModel['points'][i][4])})
        self.showAlignmentModel(alignModel)
