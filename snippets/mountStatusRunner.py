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
# import PyQT5 for threading purpose
import PyQt5
from snippets import ipdirect
from mount import mount_command
from astrometry import transform


class MountStatusRunner(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    signalStatusCamera = PyQt5.QtCore.pyqtSignal(int)
    signalStatusSolver = PyQt5.QtCore.pyqtSignal(int)
    signalModelPointsRedraw = PyQt5.QtCore.pyqtSignal(bool)

    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red;'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'

    CYCLESTATUSSLOW = 10000
    CYCLESTATUSMEDIUM = 3000
    CYCLESTATUSFAST = 200

    def __init__(self, parent, app):
        super().__init__()
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        # make main sources available
        self.app = app
        self.parent = parent
        self.data = parent
        self.transform = transform.Transform(self.app)
        self.mountIpDirect = ipdirect.MountIpDirect(self.app)

        self.worker1Mount = mount_command.MountIpDirect(self.app, self.data)
        self.thread1Mount = PyQt5.QtCore.QThread()
        self.thread1Mount.setObjectName("Mount1")
        self.worker1Mount.moveToThread(self.thread1Mount)
        # noinspection PyUnresolvedReferences
        self.thread1Mount.started.connect(self.worker1Mount.run)
        self.worker1Mount.finished.connect(self.thread1MountStop)

    def thread1MountStop(self):
        self.thread1Mount.quit()
        self.thread1Mount.wait()

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.mountIpDirect.connect()
        self.thread1Mount.start()
        self.getStatusFast()
        self.getStatusMedium()
        self.getStatusSlow()
        self.getStatusOnce()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.mountIpDirect.disconnect()
        self.worker1Mount.stop()
        self.finished.emit()

    def setRefractionParam(self):
        if 'Temperature' in self.app.workerAscomEnvironment.data and 'Pressure' in self.app.workerAscomEnvironment.data and self.app.workerAscomEnvironment.isRunning:
            pressure = self.app.workerAscomEnvironment.data['Pressure']
            temperature = self.app.workerAscomEnvironment.data['Temperature']
            if (900.0 < pressure < 1100.0) and (-40.0 < temperature < 50.0):
                self.mountIpDirect.sendCommand(':SRPRS{0:04.1f}#'.format(pressure))
                if temperature > 0:
                    self.mountIpDirect.sendCommand(':SRTMP+{0:03.1f}#'.format(temperature))
                else:
                    self.mountIpDirect.sendCommand(':SRTMP-{0:3.1f}#'.format(-temperature))
                self.parent.data['RefractionTemperature'] = self.mountIpDirect.sendCommand(':GRTMP#')
                self.parent.data['RefractionPressure'] = self.mountIpDirect.sendCommand(':GRPRS#')
            else:
                self.logger.warning('parameters out of range ! temperature:{0} pressure:{1}'.format(temperature, pressure))

    def getStatusMedium(self):
        if self.app.ui.checkAutoRefractionNotTracking.isChecked():
            # if there is no tracking, than updating is good
            if 'Status' in self.parent.data:
                if self.parent.data['Status'] != 0:
                    self.setRefractionParam()
        if self.app.ui.checkAutoRefractionCamera.isChecked():
            # the same is good if the camera is not in integrating
            if self.app.workerModelingDispatcher.modelingRunner.imagingApps.imagingWorkerAppHandler.data['CameraStatus'] in ['READY - IDLE', 'DOWNLOADING']:
                self.setRefractionParam()
        self.parent.data['SlewRate'] = self.mountIpDirect.sendCommand(':GMs#')
        self.parent.data['TimeToFlip'] = int(self.mountIpDirect.sendCommand(':Gmte#'))
        self.parent.data['MeridianLimitTrack'] = int(self.mountIpDirect.sendCommand(':Glmt#'))
        self.parent.data['MeridianLimitSlew'] = int(self.mountIpDirect.sendCommand(':Glms#'))
        self.parent.data['TimeToMeridian'] = int(self.parent.data['TimeToFlip'] - self.parent.data['MeridianLimitTrack'] / 360 * 24 * 60)
        self.parent.signalMountTrackPreview.emit()
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUSMEDIUM, self.getStatusMedium)

    def getStatusSlow(self):
        self.parent.data['TimeToTrackingLimit'] = self.mountIpDirect.sendCommand(':Gmte#')
        self.parent.data['RefractionTemperature'] = self.mountIpDirect.sendCommand(':GRTMP#')
        self.parent.data['RefractionPressure'] = self.mountIpDirect.sendCommand(':GRPRS#')
        self.parent.data['TelescopeTempDEC'] = self.mountIpDirect.sendCommand(':GTMP1#')
        self.parent.data['RefractionStatus'] = self.mountIpDirect.sendCommand(':GREF#')
        self.parent.data['UnattendedFlip'] = self.mountIpDirect.sendCommand(':Guaf#')
        self.parent.data['MeridianLimitTrack'] = self.mountIpDirect.sendCommand(':Glmt#')
        self.parent.data['MeridianLimitSlew'] = self.mountIpDirect.sendCommand(':Glms#')
        self.parent.data['DualAxisTracking'] = self.mountIpDirect.sendCommand(':Gdat#')
        self.parent.data['CurrentHorizonLimitHigh'] = self.mountIpDirect.sendCommand(':Gh#')
        self.parent.data['CurrentHorizonLimitLow'] = self.mountIpDirect.sendCommand(':Go#')
        try:
            if self.parent.data['FW'] < 21500:
                return
            reply = self.mountIpDirect.sendCommand(':GDUTV#')
            if len(reply) > 0:
                valid, expirationDate = reply.split(',')
                self.parent.data['UTCDataValid'] = valid
                self.parent.data['UTCDataExpirationDate'] = expirationDate
        except Exception as e:
            self.logger.error('receive error GDUTV command: {0}'.format(e))
        finally:
            pass
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUSSLOW, self.getStatusSlow)

    def getStatusOnce(self):
        command = ''
        target = list()
        for i in range(1, 80):
            command += (':getalp{0:d}#'.format(i))
            target.append('{0:02d}'.format(i))
        self.worker1Mount.sendCommandQueue.put((command, target))
        # Set high precision mode
        self.mountIpDirect.sendCommand(':U2#')
        self.parent.site_height = self.mountIpDirect.sendCommand(':Gev#')
        lon1 = self.mountIpDirect.sendCommand(':Gg#')
        # due to compatibility to LX200 protocol east is negative
        if lon1[0] == '-':
            self.parent.site_lon = lon1.replace('-', '+')
        else:
            self.parent.site_lon = lon1.replace('+', '-')
        self.parent.site_lat = self.mountIpDirect.sendCommand(':Gt#')
        self.parent.data['CurrentSiteElevation'] = self.parent.site_height
        self.parent.data['CurrentSiteLongitude'] = lon1
        self.parent.data['CurrentSiteLatitude'] = self.parent.site_lat
        self.parent.data['FirmwareDate'] = self.mountIpDirect.sendCommand(':GVD#')
        self.parent.data['FirmwareNumber'] = self.mountIpDirect.sendCommand(':GVN#')
        fw = self.parent.data['FirmwareNumber'].split('.')
        if len(fw) == 3:
            self.parent.data['FW'] = int(float(fw[0]) * 10000 + float(fw[1]) * 100 + float(fw[2]))
        else:
            self.parent.data['FW'] = 0
        self.parent.data['FirmwareProductName'] = self.mountIpDirect.sendCommand(':GVP#')
        self.parent.data['FirmwareTime'] = self.mountIpDirect.sendCommand(':GVT#')
        self.parent.data['HardwareVersion'] = self.mountIpDirect.sendCommand(':GVZ#')
        self.logger.info('FW: {0} Number: {1}'.format(self.mountIpDirect.sendCommand(':GVN#'), self.parent.data['FW']))
        self.logger.info('Site Lon:{0}'.format(self.parent.site_lon))
        self.logger.info('Site Lat:{0}'.format(self.parent.site_lat))
        self.logger.info('Site Height:{0}'.format(self.parent.site_height))

